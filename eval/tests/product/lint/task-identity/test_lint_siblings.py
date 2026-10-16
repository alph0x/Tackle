from pathlib import Path
import re
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
from eval.support.lint import lint_rows, literal_command, write_files, run_lint_row  # noqa: E402
INSTALL = current_root(ROOT)

SOURCE = (INSTALL / "references/guides/lint-spec.md").read_bytes()
HEAD = "| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n"
SECTION = ("## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n"
           "| beta | docs/plans/beta | shares the release |\n")
BOARD = "Schema: tackle-workspace/5\n\n"


def undeclared(owner, ref, slug="beta"):
    return "task %s depends on %s [%s], but no sibling named %s is declared\n" % (owner, ref, slug, slug)


def not_on_board(owner, ref, slug="beta"):
    return "task %s depends on %s [%s], which is not on the sibling%s board\n" % (
        owner, ref, slug, chr(39) + "s")


class LintSiblingWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tackle-lint-siblings-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.alpha = self.root / "docs/plans/alpha"
        self.beta = self.root / "docs/plans/beta"

    def workspace(self, rows, agents=None, briefs=None):
        """rows: (id, brief, depends). Local briefs default to a heading naming their id."""
        ids = [row[0] for row in rows]
        files = {
            "plan.md": "# Plan\n\n## 5. Task decomposition\n| Task | Responsibility |\n|---|---|\n"
                       + "".join("| %s | Work |\n" % i for i in ids),
            "history.md": "# History\n\n## 2026-09-24 s1\n",
            "resource-usage.md": "Schema: tackle-observability/2\n",
            "task-board.md": BOARD + HEAD + "".join(
                "| %s | Work | %s | %s | Draft | pending |\n" % (i, brief, deps) for i, brief, deps in rows),
        }
        for i, brief, _ in rows:
            if brief.startswith("tasks/"):
                files.setdefault(brief, "# Task %s — Work\n\n- **Depends on**: none\n" % i)
        files.update(briefs or {})
        if agents is not None:
            files["AGENTS.md"] = agents
        write_files(self.alpha, files)

    def board_at(self, folder, ids=("T-0007",), schema=BOARD.strip()):
        rows = "".join("| %s | Work | tasks/%s.md | none | Draft | pending |\n" % (i, i) for i in ids)
        write_files(folder, {"task-board.md": schema + "\n\n" + HEAD + rows})

    def beta_board(self, ids=("T-0007",), schema=BOARD.strip()):
        self.board_at(self.beta, ids, schema)

    def output(self):
        result = run_lint_row(self.root, 2, slug="alpha", source=SOURCE, script=True)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        return result.stdout.decode("utf-8")

    def test_resolved_sibling_reference_passes(self):
        self.workspace([("T-0001", "tasks/T-0001.md", "none"),
                        ("T-0002", "tasks/T-0002.md", "T-0001, T-0007 [beta]")], agents="# Agents\n\n" + SECTION)
        self.beta_board()
        self.assertEqual(self.output(), "")

    def test_workspace_without_agents_file_is_silent(self):
        self.workspace([("T-0001", "tasks/T-0001.md", "none")])
        result = run_lint_row(self.root, 2, slug="alpha", source=SOURCE, script=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_commented_template_example_declares_nothing(self):
        template = (INSTALL / "references/AGENTS.tmpl.md").read_text(encoding="utf-8")
        self.assertIn("| Sibling | Path | Relation |", template)
        self.assertIn("| api | docs/plans/api-split | shares the release |", template)
        self.workspace([("T-0002", "tasks/T-0002.md", "T-0007 [api]")], agents=template)
        self.board_at(self.root / "docs/plans/api-split")
        self.assertEqual(self.output(), undeclared("T-0002", "T-0007", "api"))

    def test_undeclared_reference_names_its_owner(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "T-0007 [gamma]")])
        self.assertEqual(self.output(), undeclared("T-0002", "T-0007", "gamma"))

    def test_missing_or_old_sibling_board_prints_once(self):
        for label, schema in (("missing", None), ("schema four", "Schema: tackle-workspace/4")):
            with self.subTest(board=label):
                self.workspace([("T-0002", "tasks/T-0002.md", "T-0007 [beta]"),
                                ("T-0003", "tasks/T-0003.md", "T-0007 [beta]")], agents="# Agents\n\n" + SECTION)
                if schema is not None:
                    self.beta_board(schema=schema)
                self.assertEqual(self.output(),
                                 "sibling beta has no tackle-workspace/5 task-board.md at docs/plans/beta\n")

    def test_missing_sibling_task_is_not_on_board(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "T-0009 [beta]")], agents="# Agents\n\n" + SECTION)
        self.beta_board()
        self.assertEqual(self.output(), not_on_board("T-0002", "T-0009"))

    def test_path_must_be_one_workspace_folder(self):
        for path in ("docs/plans/a/b", "../../x", "docs/plans/beta/"):
            with self.subTest(path=path):
                agents = "# Agents\n\n## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n| beta | %s | x |\n" % path
                self.workspace([("T-0002", "tasks/T-0002.md", "T-0007 [beta]")], agents=agents)
                self.beta_board()
                self.assertEqual(self.output(), undeclared("T-0002", "T-0007"))

    def test_sibling_brief_with_matching_heading_passes(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "none"),
                        ("T-0003", "../beta/tasks/T-0003-x.md", "none")], agents="# Agents\n\n" + SECTION)
        write_files(self.beta, {"tasks/T-0003-x.md": "# Task T-0003 — x\n\n- **Depends on**: none\n"})
        self.assertEqual(self.output(), "")

    def test_sibling_brief_heading_must_name_its_task(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "none"),
                        ("T-0003", "../beta/tasks/T-0003-x.md", "none")], agents="# Agents\n\n" + SECTION)
        write_files(self.beta, {"tasks/T-0003-x.md": "# Task T-0004 — x\n\n- **Depends on**: none\n"})
        self.assertEqual(self.output(), "mismatched brief heading: ../beta/tasks/T-0003-x.md\n")

    def test_brief_escape_is_outside_once(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "none"),
                        ("T-0003", "../beta/tasks/../../gamma/x.md", "none")], agents="# Agents\n\n" + SECTION)
        self.assertEqual(self.output(),
                         "brief ../beta/tasks/../../gamma/x.md for task T-0003 is outside the workspace\n")

    def test_brief_elsewhere_is_outside_without_missing_brief(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "none"),
                        ("T-0003", "../gamma/tasks/T-0003-x.md", "none")])
        self.assertEqual(self.output(),
                         "brief ../gamma/tasks/T-0003-x.md for task T-0003 is outside the workspace\n")

    def test_local_references_read_as_before(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "T-0005")])
        self.assertEqual(self.output(), "unresolved: T-0005\n")

    def test_row_two_command_stays_portable_and_pipe_free(self):
        cell = literal_command(2, SOURCE.decode("utf-8"))
        command = lint_rows("alpha", SOURCE)[2]["command"].decode("utf-8")
        self.assertNotIn("|", cell)
        self.assertNotIn("<slug>", cell[cell.index("awk -v"):])
        for pattern in (r"\|", r"gensub\(", r"nextfile", r"delete [A-Za-z_]+[;}]", r"\\[<>]", r"/[^/]*\{[0-9]"):
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, command))

    def test_unclosed_fence_declares_nothing(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "T-0007 [beta]")])
        self.beta_board()
        baseline = self.output()
        self.workspace([("T-0002", "tasks/T-0002.md", "T-0007 [beta]")], agents="# Agents\n\n```\n" + SECTION)
        self.assertEqual(self.output(), baseline)
        self.assertEqual(baseline, undeclared("T-0002", "T-0007"))

    def test_unclosed_section_at_end_of_file_matches_baseline(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "none")])
        baseline = self.output()
        self.workspace([("T-0002", "tasks/T-0002.md", "none")], agents="# Agents\n\n" + SECTION)
        self.assertEqual(self.output(), baseline)

    def test_brief_depends_line_reads_only_local_ids(self):
        agents = "# Agents\n\n" + SECTION + "| api | docs/plans/api | shares the release |\n"
        self.workspace([("T-0002", "tasks/T-0002.md", "none")],
                       agents=agents,
                       briefs={"tasks/T-0002.md": "# Task T-0002 — Work\n\n- **Depends on**: T-0005 [blocked], T-0044 [api]\n"})
        self.board_at(self.root / "docs/plans/api", ("T-0044",))
        self.assertEqual(self.output(), "unresolved: T-0005\n")

    def test_brief_path_shapes_refuse_as_before(self):
        cases = {
            "dot-dot file name": ("../beta/tasks/..",
                                  "brief ../beta/tasks/.. for task T-0003 is outside the workspace\n"),
            "neither tasks nor sibling": ("docs/T-0003.md",
                                          "mixed brief path: docs/T-0003.md\nmissing brief: docs/T-0003.md\n"),
        }
        for label, (brief, expected) in cases.items():
            with self.subTest(case=label):
                self.workspace([("T-0002", "tasks/T-0002.md", "none"),
                                ("T-0003", brief, "none")], agents="# Agents\n\n" + SECTION)
                self.assertEqual(self.output(), expected)

    def test_malformed_bracket_reads_as_local_id(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "T-0099 [Beta]")], agents="# Agents\n\n" + SECTION)
        self.beta_board()
        self.assertEqual(self.output(), "unresolved: T-0099\n")

    def test_declaration_rules(self):
        head = "# Agents\n\n## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n"
        cases = {
            "no header row": ("# Agents\n\n## Sibling workspaces\n\n| beta | docs/plans/beta | shares |\n", False),
            "comment before section": ("# Agents\n\n<!-- note --> text\n" + SECTION, True),
            "comment on the heading line": ("# Agents\n\n<!-- note -->## Sibling workspaces\n\n"
                                            "| Sibling | Path | Relation |\n|---|---|---|\n"
                                            "| beta | docs/plans/beta | shares |\n", True),
            "backticked path": (head + "| beta | `docs/plans/beta` | shares |\n", True),
            "invalid row then valid row": (head + "| beta | docs/plans/a/b | x |\n| beta | docs/plans/beta | y |\n", True),
            "first valid row wins for a duplicate slug": (head + "| beta | docs/plans/beta | y |\n"
                                                          "| beta | docs/plans/gamma | z |\n", True),
            "rows after the next heading": (head + "\n## Notes\n\n| beta | docs/plans/beta | x |\n", False),
            "second sibling heading ignored": (head + "| gamma | docs/plans/gamma | x |\n\n"
                                               "## Sibling workspaces\n\n"
                                               "| Sibling | Path | Relation |\n|---|---|---|\n"
                                               "| beta | docs/plans/beta | y |\n", False),
        }
        for label, (agents, declared) in cases.items():
            with self.subTest(case=label):
                self.workspace([("T-0002", "tasks/T-0002.md", "T-0007 [beta]")], agents=agents)
                self.beta_board()
                expected = "" if declared else undeclared("T-0002", "T-0007")
                self.assertEqual(self.output(), expected)

    def test_absent_sibling_brief_is_missing(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "none"),
                        ("T-0003", "../beta/tasks/T-0003-x.md", "none")], agents="# Agents\n\n" + SECTION)
        self.assertEqual(self.output(), "missing brief: ../beta/tasks/T-0003-x.md\n")

    def test_repeated_reference_prints_once_per_owner(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "T-0007 [beta], T-0007 [beta]"),
                        ("T-0003", "tasks/T-0003.md", "T-0007 [beta]")], agents="# Agents\n\n" + SECTION)
        self.beta_board(ids=("T-0009",))
        self.assertEqual(self.output(), not_on_board("T-0002", "T-0007") + not_on_board("T-0003", "T-0007"))

    def test_this_repository_agents_file_matches_baseline(self):
        self.workspace([("T-0002", "tasks/T-0002.md", "none")])
        baseline = self.output()
        self.workspace([("T-0002", "tasks/T-0002.md", "none")], agents=(ROOT / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertEqual(self.output(), baseline)
