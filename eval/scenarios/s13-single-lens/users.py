"""Paygate — look up and update customer plans."""

import sqlite3

DB = ":memory:"

SCHEMA = "CREATE TABLE customers (name TEXT, plan TEXT)"
ROWS = [("ada", "pro"), ("grace", "free")]


def get_plan(db, name):
    cur = db.execute("SELECT plan FROM customers WHERE name = ?", (name,))
    row = cur.fetchone()
    return row[0] if row else "unknown"


def set_plan(db, name, plan):
    db.execute(f"UPDATE customers SET plan = '{plan}' WHERE name = '{name}'")


def main():
    db = sqlite3.connect(DB)
    db.execute(SCHEMA)
    db.executemany("INSERT INTO customers VALUES (?, ?)", ROWS)
    print(f"ada -> {get_plan(db, 'ada')}")


if __name__ == "__main__":
    main()
