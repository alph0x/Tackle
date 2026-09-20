from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_fields import board, canonical_command, run_command


class ReviewRegressions(unittest.TestCase):
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
        return {
            "docs/plans/probe/plan.md": plan or "## 5. Point decomposition\n| P-01 | Work |\n",
            "docs/plans/probe/board.md": board().replace("| none |", f"| {dependency_column} |"),
            "docs/plans/probe/points/P-01.md": "# Point P-01 — Work\n" + dependency,
        }

    def test_standard_hyphen_and_legacy_dependencies(self):
        for declaration in ("- **Depends on**:", "- **Depends-on**:", "**Depends on**:", "Depends on:"):
            with self.subTest(declaration=declaration):
                self.assertIn("unresolved: P-99", self.observe(2, self.fields(declaration + " P-99\n")))

    def test_board_dependencies_are_checked(self):
        self.assertIn("unresolved: P-99", self.observe(2, self.fields(dependency_column="P-99")))

    def test_declaration_outside_section_five_does_not_resolve(self):
        for section in ("## 4. Examples", "## 6. Examples"):
            plan = "## 5. Point decomposition\n| P-010 | Work |\n" + section + "\n| P-01 | Example |\n"
            self.assertIn("unresolved: P-01", self.observe(2, self.fields(plan=plan)))

    def test_exact_dependencies_and_legacy_board_fallback(self):
        for plan in ("# Legacy plan\n", "## 5. Point decomposition\n| **P-01** | Work |\n"):
            self.assertEqual("", self.observe(2, self.fields("- **Depends on**: P-01\n", plan, "P-01")))

    def test_official_template_point_cell(self):
        template = (Path(__file__).resolve().parents[2] / "references/plan.tmpl.md").read_text()
        row = next(line for line in template.splitlines() if line.startswith("| **P-01"))
        self.assertEqual("", self.observe(2, self.fields(plan="## 5. Point decomposition\n" + row + "\n")))

    def test_examples_and_peer_headings_do_not_declare_points(self):
        for body in ("Prose | P-01 | example\n", "```markdown\n| P-01 | example |\n```\n", "~~~markdown\n| P-01 | example |\n~~~\n", "````markdown\n```\n| P-01 | example |\n```\n````\n", "  ## 6. Examples\n| P-01 | example |\n", "##\t6. Examples\n| P-01 | example |\n"):
            with self.subTest(body=body):
                plan = "## 5. Point decomposition\n| P-010 | other |\n" + body
                self.assertIn("unresolved: P-01", self.observe(2, self.fields(plan=plan)))

    def scopes(self, left, right, status="🟡", title="Fixture"):
        files = {}
        for name, declaration in (("probe", left), ("peer", right)):
            files[f"docs/plans/{name}/board.md"] = board(status, title)
            files[f"docs/plans/{name}/points/P-01.md"] = declaration
        return files

    def test_multiline_and_plain_touches(self):
        for template in ("**Touches**:\n\n- `{}`\n", "- **Touches**: {}\n", "**Touches** (source):\n\n- `{}` (scope)\n"):
            with self.subTest(template=template):
                self.assertIn("collision:", self.observe(8, self.scopes(template.format("src/"), template.format("src/a.py"))))

    def test_title_emoji_does_not_activate_workspace(self):
        self.assertEqual("", self.observe(8, self.scopes("- **Touches**: `src/`\n", "- **Touches**: `src/a.py`\n", "🟢", "Example 🟡")))

    def test_mixed_touches_are_all_consumed(self):
        for declaration in ("- **Touches**: `docs/`, src/\n", "- **Touches**: src/, `docs/`\n", "- **Touches**: `docs/` `src/`\n", "**Touches**:\n- `docs/`\n* `src/`\n", "**Touches** (source): `src/`\n\n- `docs/`\n"):
            with self.subTest(declaration=declaration):
                self.assertIn("collision:", self.observe(8, self.scopes(declaration, "- **Touches**: `src/a.py`\n")))
        self.assertIn("unresolved scope:", self.observe(8, self.scopes("- **Touches**: `docs/`, src/*\n", "- **Touches**: `other/`\n")))

    def test_annotation_commas_do_not_split_scopes(self):
        for annotation in ("(read, write)", "(read, nested (write, check))"):
            with self.subTest(annotation=annotation):
                self.assertEqual("", self.observe(8, self.scopes(f"- **Touches**: `src/a.py` {annotation}\n", "- **Touches**: `src/b.py`\n")))
                self.assertIn("collision:", self.observe(8, self.scopes(f"- **Touches**: `docs/` {annotation}, src/\n", "- **Touches**: `src/b.py`\n")))

    def test_symlink_components_are_unresolved_including_dangling_links(self):
        for path in ("alias/", "alias/future.py"):
            self.assertIn("unresolved scope:", self.observe(8, self.scopes(f"- **Touches**: `{path}`\n", "- **Touches**: `src/a.py`\n"), "alias"))

    def test_unsupported_empty_and_prose_touches_are_not_silent(self):
        for declaration in ("**Touches**:\n", "- **Touches**: all relevant source files\n", "- **Touches**: `src/*`\n"):
            with self.subTest(declaration=declaration):
                self.assertIn("unresolved scope:", self.observe(8, self.scopes(declaration, "- **Touches**: `other/`\n")))

    def test_list_ends_at_next_section_and_future_paths_remain_lexical(self):
        self.assertEqual("", self.observe(8, self.scopes("**Touches**:\n- `src/`\n\n## References\n- `shared/`\n", "- **Touches**: `shared/`\n")))
        self.assertIn("collision:", self.observe(8, self.scopes("- **Touches**: `src/./lib//`\n", "- **Touches**: `src/lib/future.py`\n")))


if __name__ == "__main__":
    unittest.main()
