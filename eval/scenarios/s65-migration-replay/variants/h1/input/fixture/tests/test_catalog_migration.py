import importlib.util
import sqlite3
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "run_catalog_migration.py"
spec = importlib.util.spec_from_file_location("run_catalog_migration", MODULE_PATH)
run_catalog_migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_catalog_migration)


def fresh_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE products (name TEXT PRIMARY KEY, base_price_cents INTEGER, "
        "final_price_cents INTEGER)"
    )
    conn.execute("CREATE TABLE price_adjustments (product_name TEXT, delta_cents INTEGER, reason TEXT)")
    conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO meta VALUES ('schema_version', '1')")
    conn.execute("INSERT INTO products VALUES ('sample', 1000, NULL)")
    return conn


class TestPureSteps(unittest.TestCase):
    def test_step2_requires_step1_first(self):
        conn = fresh_conn()
        with self.assertRaises(SystemExit):
            run_catalog_migration.step2(conn)

    def test_step1_inserts_one_adjustment(self):
        conn = fresh_conn()
        run_catalog_migration.step1(conn)
        count = conn.execute("SELECT COUNT(*) FROM price_adjustments").fetchone()[0]
        self.assertEqual(count, 1)
        self.assertEqual(run_catalog_migration.get_schema_version(conn), 2)

    def test_step2_computes_final_price(self):
        conn = fresh_conn()
        run_catalog_migration.step1(conn)
        run_catalog_migration.step2(conn)
        price = conn.execute(
            "SELECT final_price_cents FROM products WHERE name = 'sample'"
        ).fetchone()[0]
        self.assertEqual(price, 900)


if __name__ == "__main__":
    unittest.main()
