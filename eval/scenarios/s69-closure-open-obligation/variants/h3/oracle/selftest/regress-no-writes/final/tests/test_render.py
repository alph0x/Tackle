"""T-02: the rendered reminders match the agreed sample."""
import tempfile
import unittest
from pathlib import Path

from reminders.render import write_reminders
from reminders.shifts import read_shifts

HERE = Path(__file__).resolve().parent


class WriteReminders(unittest.TestCase):
    def test_matches_agreed_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "reminders.txt"
            count = write_reminders(read_shifts(HERE / "fixtures" / "shifts.csv"), out)
            self.assertEqual(count, 3)
            self.assertEqual(out.read_text(encoding="utf-8"), (HERE / "fixtures" / "expected-reminders.txt").read_text(encoding="utf-8"))
