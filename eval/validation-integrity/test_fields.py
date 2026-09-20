from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LINT_SPEC = ROOT / "references/guides/lint-spec.md"


def canonical_command(row: int) -> str:
    for line in LINT_SPEC.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| {row} ·"):
            cell = line.split(" | ", 2)[1]
            return cell.strip("`")
    raise AssertionError(f"canonical lint row {row} not found")


def board(status: str = "🔴", title: str = "Fixture") -> str:
    return (
        "| Point | What | Briefing | Depends on | Status | Confidence |\n"
        "|---|---|---|---|---|---|\n"
        f"| P-01 | {title} | points/P-01.md | none | {status} | n/a |\n"
    )


def run_command(root: Path, command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/sh", "-c", command],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


class ExactFieldValidationTests(unittest.TestCase):
    def make_workspace(self, root: Path, files: dict[str, str]) -> None:
        workspace = root / "docs/plans/probe"
        for relative, content in files.items():
            destination = workspace / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

    def assert_finding(self, row: int, files: dict[str, str], fragment: str) -> None:
        with tempfile.TemporaryDirectory(prefix="tackle-validation-fields-") as directory:
            root = Path(directory)
            self.make_workspace(root, files)
            result = run_command(root, canonical_command(row).replace("<slug>", "probe"))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertIn(fragment, result.stdout)

    def assert_clean(self, row: int, files: dict[str, str]) -> None:
        with tempfile.TemporaryDirectory(prefix="tackle-validation-fields-") as directory:
            root = Path(directory)
            self.make_workspace(root, files)
            result = run_command(root, canonical_command(row).replace("<slug>", "probe"))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")

    def test_row_2_requires_exact_point_id_declaration(self) -> None:
        self.assert_clean(
            2,
            {
                "plan.md": "## 5. Point decomposition\n| P-01 | Work | R01 | points/P-01.md | none |\n",
                "points/P-01.md": "# P-01\n",
                "board.md": board(),
            },
        )
        self.assert_finding(
            2,
            {
                "plan.md": "## 5. Point decomposition\n| P-010 | Work | R01 | points/P-010.md | none |\n",
                "points/P-01.md": "# P-01\n",
                "board.md": board(),
            },
            "unresolved: P-01",
        )

    def test_row_2_fails_closed_when_plan_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tackle-validation-fields-") as directory:
            root = Path(directory)
            self.make_workspace(
                root,
                {
                    "points/P-01.md": "# P-01\n",
                    "board.md": board(),
                },
            )
            result = run_command(root, canonical_command(2).replace("<slug>", "probe"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing:", result.stdout)

    def test_row_3_validates_status_field_not_any_emoji(self) -> None:
        self.assert_clean(3, {"board.md": board("🟢", "Example 🟢 output")})
        self.assert_finding(
            3,
            {"board.md": board("BROKEN", "Example 🟢 output")},
            "bad status:",
        )

    def test_row_7_requires_exact_decision_heading(self) -> None:
        self.assert_clean(
            7,
            {
                "points/P-01.md": "## Acceptance <!-- SEALED: D-01 -->\n",
                "decisions.md": "## D-01 — Accepted rule\n",
            },
        )
        self.assert_finding(
            7,
            {
                "points/P-01.md": "## Acceptance <!-- SEALED: D-01 -->\n",
                "decisions.md": "## D-010 — Different decision\n",
            },
            "missing seal: D-01",
        )

    def test_row_12_closes_effort_token(self) -> None:
        self.assert_clean(12, {"points/P-01.md": "- **Effort**:   high   \n"})
        self.assert_finding(
            12,
            {"points/P-01.md": "- **Effort**: highXYZ\n"},
            "highXYZ",
        )


if __name__ == "__main__":
    unittest.main()
