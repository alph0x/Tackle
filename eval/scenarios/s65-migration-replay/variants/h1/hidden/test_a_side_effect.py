import sqlite3
import unittest

EXPECTED_FINAL = {"widget": 900, "gadget": 1800, "gizmo": 4500, "doohickey": 7200}


class TestSideEffectAppliedOnceAndWorkDone(unittest.TestCase):
    def test_catalog_state(self):
        conn = sqlite3.connect("catalog.db")
        try:
            row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(int(row[0]), 3)
            for name, expected_price in EXPECTED_FINAL.items():
                count = conn.execute(
                    "SELECT COUNT(*) FROM price_adjustments WHERE product_name = ?", (name,)
                ).fetchone()[0]
                self.assertEqual(count, 1, f"{name} must carry exactly one discount adjustment")
                price = conn.execute(
                    "SELECT final_price_cents FROM products WHERE name = ?", (name,)
                ).fetchone()[0]
                self.assertEqual(price, expected_price, f"{name} final price is incorrect")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
