from pathlib import Path
import hashlib
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[5]
import sys
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
from eval.support.lint import lint_namespace, write_files, run_lint_row  # noqa: E402
INSTALL = current_root(ROOT)

SOURCE = (INSTALL / "references/guides/lint-spec.md").read_bytes()
NAMESPACE = lint_namespace()

class TaskIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tackle-task-identity-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "docs/plans/probe"
        self.workspace.mkdir(parents=True)

    def write(self, relative, content):
        write_files(self.workspace, {relative: content})

    def fixture(self, identity="T-01", directory="tasks", status="Draft", dependency="none"):
        self.write("plan.md", "# Plan\n\n## 5. Task decomposition\n| Task | Responsibility |\n|---|---|\n| " + identity + " | Work |\n")
        self.write("history.md", "# History\n\n## 2026-09-24 s1\n")
        self.write("resource-usage.md", "Schema: tackle-observability/2\n")
        self.write("task-board.md", "Schema: tackle-workspace/5\n\n| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n| " + identity + " | Work | " + directory + "/" + identity + ".md | " + dependency + " | " + status + " | pending |\n")
        self.write(directory + "/" + identity + ".md", "# Task " + identity + " — Work\n\n- **Depends on**: " + dependency + "\n- **Effort**: high\n")

    def row(self, number):
        return run_lint_row(self.root, number, slug='probe', source=SOURCE, script=True)

    def test_fresh_task_workspace_has_one_identity_across_real_lint_consumer(self):
        self.fixture()
        task_template = (INSTALL / "references/task.tmpl.md").read_text()
        self.assertIn("task-t-0n--title", task_template)
        self.assertNotIn("point-p-0n--title", task_template)
        result = self.row(2)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_fresh_usage_template_does_not_install_legacy_ledger(self):
        scaffold = (INSTALL / "references/guides/scaffold.md").read_text()
        current = (INSTALL / "references/resource-usage.tmpl.md").read_text()
        self.assertIn("`resource-usage.md` from `resource-usage.tmpl.md`", scaffold)
        self.assertIn("| Run ID | Event | Task | Role |", current)
        self.assertNotIn("| Point |", current)
        self.assertFalse((INSTALL / "references/usage.tmpl.md").exists())

    def test_canonical_physical_workspace_paths_pass_real_lint(self):
        self.write("plan.md", "# Plan\n\n## 5. Task decomposition\n| Task | Responsibility |\n|---|---|\n| T-A | Work |\n")
        self.write("task-board.md", "Schema: tackle-workspace/5\n\n| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n| T-A | Work | `tasks/T-A.md` | none | Draft | pending |\n")
        self.write("history.md", "# History\n\n## 2026-09-24 s1\n")
        self.write("resource-usage.md", "Schema: tackle-observability/2\n\n| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |\n")
        self.write("tasks/T-A.md", "# Task T-A — Work\n\n- **Depends on**: none\n- **Effort**: low\n")
        self.write("reference.md", "# Sources\n")
        for number in range(1, 17):
            with self.subTest(row=number):
                result = self.row(number)
                expected_exit = 1 if number == 5 else 0
                self.assertEqual((result.returncode, result.stdout, result.stderr), (expected_exit, b"", b""))

    def test_literal_scaffold_gate_catches_missing_new_core_file(self):
        guide = (INSTALL / "references/guides/scaffold.md").read_text()
        check = re.findall(r"```sh\n(.*?)\n```", guide, re.S)[0].replace("<initiative>", "probe")
        for name in ("README.md", "AGENTS.md", "plan.md", "task-board.md", "history.md", "questions.md", "decisions.md", "reference.md"):
            self.write(name, "# Test\n")
        (self.workspace / "tasks").mkdir()
        result = subprocess.run(["sh", "-c", check], cwd=self.root, capture_output=True)
        self.assertIn(b"missing core: resource-usage.md", result.stdout + result.stderr)
        self.write("resource-usage.md", "Schema: tackle-observability/2\n")
        result = subprocess.run(["sh", "-c", check], cwd=self.root, capture_output=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_new_scaffold_templates_use_physical_names(self):
        guide = (INSTALL / "references/guides/scaffold.md").read_text()
        file_map = (INSTALL / "references/AGENTS.tmpl.md").read_text()
        for name in ("task-board.md", "history.md", "resource-usage.md"):
            self.assertIn(name, guide + file_map)
        for name in ("task-board.tmpl.md", "history.tmpl.md", "resource-usage.tmpl.md"):
            self.assertTrue((INSTALL / "references" / name).is_file(), name)
        self.assertIn("bare token without trailing punctuation", (INSTALL / "references/task.tmpl.md").read_text())

    def test_focused_workspace_uses_new_history_and_usage_paths(self):
        self.write("plan.md", "Gate: Lite\n# Focused\n")
        self.write("history.md", "# History\n\n## 2026-09-24 s1\n")
        self.write("resource-usage.md", "Schema: tackle-observability/2\n")
        for number in (1, 6):
            with self.subTest(row=number):
                result = self.row(number)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        self.write("log.md", "# Duplicate\n")
        result = self.row(1)
        self.assertIn(b"migrate first", result.stdout + result.stderr)

    def test_new_board_names_missing_resource_ledger(self):
        self.write("plan.md", "# Plan\n\n## 5. Task decomposition\n| Task | Responsibility |\n|---|---|\n| T-A | Work |\n")
        self.write("task-board.md", "Schema: tackle-workspace/5\n\n| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n| T-A | Work | tasks/T-A.md | none | Draft | pending |\n")
        self.write("history.md", "# History\n")
        self.write("tasks/T-A.md", "# Task T-A — Work\n")
        result = self.row(2)
        self.assertIn(b"missing: docs/plans/probe/resource-usage.md", result.stdout + result.stderr)
        result = self.row(16)
        self.assertIn(b"missing resource-usage.md", result.stdout + result.stderr)

    def test_new_board_rejects_old_core_path_duplicate(self):
        self.write("plan.md", "# Plan\n\n## 5. Task decomposition\n| Task | Responsibility |\n|---|---|\n| T-A | Work |\n")
        self.write("task-board.md", "Schema: tackle-workspace/5\n\n| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n| T-A | Work | tasks/T-A.md | none | Draft | pending |\n")
        self.write("history.md", "# History\n")
        self.write("resource-usage.md", "Schema: tackle-observability/2\n")
        self.write("tasks/T-A.md", "# Task T-A — Work\n")
        self.write("board.md", "# Duplicate\n")
        result = self.row(2)
        self.assertIn(b"mixed workspace paths", result.stdout + result.stderr)

    def test_new_board_rejects_legacy_point_directory(self):
        self.write("plan.md", "# Plan\n\n## 5. Task decomposition\n| Task | Responsibility |\n|---|---|\n| T-A | Work |\n")
        self.write("task-board.md", "Schema: tackle-workspace/5\n\n| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n| T-A | Work | tasks/T-A.md | none | Draft | pending |\n")
        self.write("history.md", "# History\n")
        self.write("resource-usage.md", "Schema: tackle-observability/2\n")
        self.write("tasks/T-A.md", "# Task T-A — Work\n")
        self.write("points/P-A.md", "# An older brief\n")
        result = self.row(2)
        self.assertIn(b"mixed workspace paths", result.stdout + result.stderr)

    def test_invalid_dangling_task_dependency_is_rejected(self):
        self.fixture(dependency="T-99")
        result = self.row(2)
        self.assertIn(b"T-99", result.stdout + result.stderr)

    def test_invalid_mixed_task_and_point_identity_is_rejected(self):
        self.fixture()
        board = self.workspace / "task-board.md"
        board.write_text(board.read_text().replace("| T-01 | Work", "| P-01 | Work"))
        result = self.row(2)
        self.assertNotEqual(result.stdout + result.stderr, b"")

    def test_invalid_missing_task_brief_is_rejected(self):
        self.fixture()
        (self.workspace / "tasks/T-01.md").unlink()
        result = self.row(2)
        self.assertIn(b"missing task briefs", result.stdout + result.stderr)

    def test_invalid_mixed_task_directories_are_rejected(self):
        self.fixture()
        (self.workspace / "points").mkdir()
        result = self.row(2)
        self.assertIn(b"mixed workspace paths", result.stdout + result.stderr)

    def test_invalid_t_status_is_checked(self):
        self.fixture(status="Invented")
        result = self.row(3)
        self.assertIn(b"bad status", result.stdout + result.stderr)

    def test_complete_t_task_requires_report_reference(self):
        self.fixture(status="Complete")
        result = self.row(10)
        self.assertIn(b"terminal task without verification reference", result.stdout + result.stderr)

    def test_lite_workspace_rejects_full_tasks_directory(self):
        self.write("plan.md", "Gate: Lite\n# Small task\n")
        self.write("history.md", "# History\n")
        self.write("resource-usage.md", "# Resource usage\n")
        (self.workspace / "tasks").mkdir()
        result = self.row(1)
        self.assertIn(b"Lite has Full artifact", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
