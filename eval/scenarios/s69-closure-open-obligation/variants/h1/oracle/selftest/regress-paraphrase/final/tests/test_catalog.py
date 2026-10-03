"""T-01: the catalog reader."""
import unittest
from pathlib import Path

from sync.catalog import read_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "catalog.csv"


class ReadCatalog(unittest.TestCase):
    def test_reads_rows_with_every_column(self):
        rows = read_catalog(FIXTURE)
        self.assertEqual([r["product_id"] for r in rows], ["LM-1001", "LM-1002", "LM-1003"])
        self.assertEqual(rows[0]["vendor_sku"], "HK-ENK-15")
