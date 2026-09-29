from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

from test_fields import board, canonical_command, run_command

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)

LAYOUT = {"history.md": "# History\n", "resource-usage.md": "# Resource usage\n"}


class DependencyAndScopeParsingTests(unittest.TestCase):
    def observe(self, row, files, symlink=None):
        with tempfile.TemporaryDirectory(prefix="tackle-reviewed-") as directory:
            root = Path(directory)
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            if symlink:
                (root / symlink).symlink_to("src", target_is_directory=True)
            result = run_command(root, canonical_command(row).replace("<slug>", "probe"))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            return result.stdout

    def fields(self, dependency="", plan=None, dependency_column="none"):
        files = {"docs/plans/probe/" + name: text for name, text in LAYOUT.items()}
        files.update({
            "docs/plans/probe/plan.md": plan or "## 5. Task decomposition\n| T-A | Work |\n",
            "docs/plans/probe/task-board.md": board().replace("| none |", f"| {dependency_column} |"),
            "docs/plans/probe/tasks/T-A.md": "# Task T-A — Work\n" + dependency,
        })
        return files

    def test_standard_hyphen_and_legacy_dependencies(self):
        for declaration in ("- **Depends on**:", "- **Depends-on**:", "**Depends on**:", "Depends on:"):
            with self.subTest(declaration=declaration):
                self.assertIn("unresolved: T-Z", self.observe(2, self.fields(declaration + " T-Z\n")))

    def test_board_dependencies_are_checked(self):
        self.assertIn("unresolved: T-Z", self.observe(2, self.fields(dependency_column="T-Z")))

    def test_declaration_outside_section_five_does_not_resolve(self):
        for section in ("## 4. Examples", "## 6. Examples"):
            plan = "## 5. Task decomposition\n| T-AA | Work |\n" + section + "\n| T-A | Example |\n"
            self.assertIn("unresolved: T-A", self.observe(2, self.fields(plan=plan)))

    def test_exact_dependencies_resolve(self):
        plan = "## 5. Task decomposition\n| **T-A** | Work |\n"
        self.assertEqual("", self.observe(2, self.fields("- **Depends on**: T-A\n", plan, "T-A")))

    def test_official_template_task_cell(self):
        template = (INSTALL / "references/plan.tmpl.md").read_text()
        cell = next(line for line in template.splitlines() if line.startswith("| **T-"))
        identity = re.match(r"\| \*\*(T-[A-Za-z0-9]+)", cell)[1]
        files = {"docs/plans/probe/" + name: text for name, text in LAYOUT.items()}
        files.update({
            "docs/plans/probe/plan.md": "## 5. Task decomposition\n" + cell + "\n",
            "docs/plans/probe/task-board.md": board().replace("T-A", identity),
            "docs/plans/probe/tasks/" + identity + ".md": "# Task " + identity + " — Work\n- **Depends on**: none\n",
        })
        self.assertEqual("", self.observe(2, files))

    def test_examples_and_peer_headings_do_not_declare_points(self):
        for body in ("Prose | T-A | example\n", "```markdown\n| T-A | example |\n```\n", "~~~markdown\n| T-A | example |\n~~~\n", "````markdown\n```\n| T-A | example |\n```\n````\n", "  ## 6. Examples\n| T-A | example |\n", "##\t6. Examples\n| T-A | example |\n"):
            with self.subTest(body=body):
                plan = "## 5. Task decomposition\n| T-AA | other |\n" + body
                self.assertIn("unresolved: T-A", self.observe(2, self.fields(plan=plan)))

    def scopes(self, left, right, status="In progress", title="Fixture"):
        files = {}
        for name, declaration in (("probe", left), ("peer", right)):
            files[f"docs/plans/{name}/task-board.md"] = board(status, title)
            files[f"docs/plans/{name}/tasks/T-A.md"] = declaration
        return files

    def test_multiline_and_plain_touches(self):
        for template in ("**Write scope**:\n\n- `{}`\n", "- **Write scope**: {}\n", "**Write scope** (source):\n\n- `{}` (scope)\n"):
            with self.subTest(template=template):
                self.assertIn("collision:", self.observe(8, self.scopes(template.format("src/"), template.format("src/a.py"))))

    def test_title_emoji_does_not_activate_workspace(self):
        self.assertEqual("", self.observe(8, self.scopes("- **Write scope**: `src/`\n", "- **Write scope**: `src/a.py`\n", "Complete", "Example In progress")))

    def test_mixed_touches_are_all_consumed(self):
        for declaration in ("- **Write scope**: `docs/`, src/\n", "- **Write scope**: src/, `docs/`\n", "- **Write scope**: `docs/` `src/`\n", "**Write scope**:\n- `docs/`\n* `src/`\n", "**Write scope** (source): `src/`\n\n- `docs/`\n"):
            with self.subTest(declaration=declaration):
                self.assertIn("collision:", self.observe(8, self.scopes(declaration, "- **Write scope**: `src/a.py`\n")))
        self.assertIn("unresolved scope:", self.observe(8, self.scopes("- **Write scope**: `docs/`, src/*\n", "- **Write scope**: `other/`\n")))

    def test_annotation_commas_do_not_split_scopes(self):
        for annotation in ("(read, write)", "(read, nested (write, check))"):
            with self.subTest(annotation=annotation):
                self.assertEqual("", self.observe(8, self.scopes(f"- **Write scope**: `src/a.py` {annotation}\n", "- **Write scope**: `src/b.py`\n")))
                self.assertIn("collision:", self.observe(8, self.scopes(f"- **Write scope**: `docs/` {annotation}, src/\n", "- **Write scope**: `src/b.py`\n")))

    def test_symlink_components_are_unresolved_including_dangling_links(self):
        for path in ("alias/", "alias/future.py"):
            self.assertIn("unresolved scope:", self.observe(8, self.scopes(f"- **Write scope**: `{path}`\n", "- **Write scope**: `src/a.py`\n"), "alias"))

    def test_unsupported_empty_and_prose_touches_are_not_silent(self):
        for declaration in ("**Write scope**:\n", "- **Write scope**: all relevant source files\n", "- **Write scope**: `src/*`\n"):
            with self.subTest(declaration=declaration):
                self.assertIn("unresolved scope:", self.observe(8, self.scopes(declaration, "- **Write scope**: `other/`\n")))

    def test_list_ends_at_next_section_and_future_paths_remain_lexical(self):
        self.assertEqual("", self.observe(8, self.scopes("**Write scope**:\n- `src/`\n\n## References\n- `shared/`\n", "- **Write scope**: `shared/`\n")))
        self.assertIn("collision:", self.observe(8, self.scopes("- **Write scope**: `src/./lib//`\n", "- **Write scope**: `src/lib/future.py`\n")))

    def test_an_older_touches_label_declares_no_scope(self):
        self.assertEqual("", self.observe(8, self.scopes("- **Touches**: `src/`\n", "- **Write scope**: `src/a.py`\n")))


if __name__ == "__main__":
    unittest.main()
