"""T-01: the logger export reader."""
import unittest
from pathlib import Path

from rollup.readings import read_readings

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "week-38.csv"


class ReadReadings(unittest.TestCase):
    def test_reads_every_row_in_order(self):
        zones = [r.zone for r in read_readings(FIXTURE)]
        self.assertEqual(zones, ["north", "south", "north", "south"])

    def test_converts_temperature(self):
        self.assertAlmostEqual(next(read_readings(FIXTURE)).temp_c, 21.0)
