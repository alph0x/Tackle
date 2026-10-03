"""T-02: the roster export matches the agreed format."""
import tempfile
import unittest
from pathlib import Path

from export.members import read_members
from export.roster import write_roster

HERE = Path(__file__).resolve().parent


class WriteRoster(unittest.TestCase):
    def test_matches_expected_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "roster.csv"
            count = write_roster(read_members(HERE / "fixtures" / "members.json"), out)
            self.assertEqual(count, 3)
            self.assertEqual(out.read_text(encoding="utf-8"), (HERE / "fixtures" / "expected-roster.csv").read_text(encoding="utf-8"))
