"""T-03 contract: the summarize subcommand prints exactly one line, `Parcels: <n>`."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = "tests/fixtures/run-04.csv"


class SummarizeCommand(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "manifest", *args], cwd=ROOT, capture_output=True, text=True)

    def test_prints_the_parcel_count_line(self):
        result = self.run_cli("summarize", FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Parcels: 3\n")

    def test_rejects_a_missing_subcommand(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage", result.stderr)
