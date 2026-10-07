"""T-01: the rota reader."""
import unittest
from pathlib import Path

from reminders.shifts import read_shifts

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "shifts.csv"


class ReadShifts(unittest.TestCase):
    def test_reads_shifts_in_rota_order(self):
        ids = [s["shift_id"] for s in read_shifts(FIXTURE)]
        self.assertEqual(ids, ["HFP-S-031", "HFP-S-032", "HFP-S-033"])
