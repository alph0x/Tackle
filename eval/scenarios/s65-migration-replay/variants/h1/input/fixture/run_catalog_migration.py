"""Migrate the product catalog: apply the loyalty discount, then compute final prices.

Run with no arguments to walk through every stage, start to finish:

    python3 run_catalog_migration.py

Pass --only one or more times to run just the named stage instead (apply-discount or
compute-price):

    python3 run_catalog_migration.py [--only STAGE]
"""
import argparse
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "catalog.db"


def get_schema_version(conn):
    row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    return int(row[0]) if row else 1


def set_schema_version(conn, value):
    conn.execute("UPDATE meta SET value = ? WHERE key = 'schema_version'", (str(value),))


def step1(conn):
    """Insert a 10%% loyalty-discount adjustment for every product."""
    products = conn.execute("SELECT name, base_price_cents FROM products").fetchall()
    for name, base_price_cents in products:
        delta = -(base_price_cents // 10)
        conn.execute(
            "INSERT INTO price_adjustments (product_name, delta_cents, reason) VALUES (?, ?, ?)",
            (name, delta, "loyalty-discount-promo"),
        )
    set_schema_version(conn, 2)


def step2(conn):
    """Compute each product's final price from its base price and adjustments."""
    if get_schema_version(conn) < 2:
        raise SystemExit("the compute-price stage requires apply-discount to have run first")
    products = conn.execute("SELECT name, base_price_cents FROM products").fetchall()
    for name, base_price_cents in products:
        total_delta = conn.execute(
            "SELECT COALESCE(SUM(delta_cents), 0) FROM price_adjustments WHERE product_name = ?",
            (name,),
        ).fetchone()[0]
        conn.execute(
            "UPDATE products SET final_price_cents = ? WHERE name = ?",
            (base_price_cents + total_delta, name),
        )
    set_schema_version(conn, 3)


STEPS = {1: step1, 2: step2}
STAGE_NAMES = {"apply-discount": 1, "compute-price": 2}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=sorted(STAGE_NAMES), action="append")
    args = parser.parse_args(argv)
    conn = sqlite3.connect(DB_PATH)
    try:
        stage_names = args.only or sorted(STAGE_NAMES, key=STAGE_NAMES.get)
        for stage_name in stage_names:
            STEPS[STAGE_NAMES[stage_name]](conn)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
