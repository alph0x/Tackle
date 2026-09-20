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


def run_overlap(scope_a: str, scope_b: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="tackle-validation-paths-") as directory:
        root = Path(directory)
        for name, scope in (("probe", scope_a), ("peer", scope_b)):
            workspace = root / "docs/plans" / name
            (workspace / "points").mkdir(parents=True)
            (workspace / "board.md").write_text(
                "| Point | What | Briefing | Depends on | Status | Confidence |\n"
                "|---|---|---|---|---|---|\n"
                "| P-01 | Fixture | points/P-01.md | none | 🟡 | n/a |\n",
                encoding="utf-8",
            )
            (workspace / "points/P-01.md").write_text(
                f"- **Touches**: `{scope}`\n",
                encoding="utf-8",
            )
        return subprocess.run(
            ["/bin/sh", "-c", canonical_command(8)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )


class PathOverlapTests(unittest.TestCase):
    def assert_overlap(self, scope_a: str, scope_b: str) -> None:
        result = run_overlap(scope_a, scope_b)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("collision:", result.stdout)

    def assert_disjoint(self, scope_a: str, scope_b: str) -> None:
        result = run_overlap(scope_a, scope_b)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_row_8_detects_exact_and_normalized_overlap(self) -> None:
        self.assert_overlap("src/a.py", "src/a.py")
        self.assert_overlap("src/", "src/a.py")
        self.assert_overlap("./src/a.py", "src/a.py")
        self.assert_overlap("src/", "src/lib/")

    def test_row_8_keeps_sibling_prefixes_disjoint(self) -> None:
        self.assert_disjoint("src/", "src2/a.py")
        self.assert_disjoint("src/a.py", "src/b.py")


if __name__ == "__main__":
    unittest.main()
