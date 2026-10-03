"""T-04 contract: `zones` prints a comma-separated table headed `zone,mean_c`, one row per zone, and the
output is what the growers' sheet import takes (the sample under tests/fixtures/)."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = "tests/fixtures/week-38.csv"
SAMPLE = ROOT / "tests" / "fixtures" / "sheet-import-week-38.csv"


class ZonesCommand(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "rollup", *args], cwd=ROOT, capture_output=True, text=True)

    def test_table_header_and_rows(self):
        result = self.run_cli("zones", FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "zone,mean_c")
        self.assertEqual(lines[1:], ["north,21.5", "south,19.0"])

    def test_matches_sheet_import_sample(self):
        result = self.run_cli("zones", FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, SAMPLE.read_text(encoding="utf-8"))

    def test_usage_error_without_subcommand(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
