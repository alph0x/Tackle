"""T-01: the export reader."""
import unittest
from pathlib import Path

from manifest.rows import read_rows

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "run-04.csv"


class ReadRows(unittest.TestCase):
    def test_reads_every_data_row(self):
        parcels = list(read_rows(FIXTURE))
        self.assertEqual([p.scan_id for p in parcels], ["S-0411", "S-0412", "S-0413"])

    def test_converts_weight(self):
        self.assertAlmostEqual(next(read_rows(FIXTURE)).weight_kg, 2.4)
