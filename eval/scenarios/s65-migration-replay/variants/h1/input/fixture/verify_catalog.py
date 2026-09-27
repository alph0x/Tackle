"""Read-only check: has the catalog migration fully completed?"""
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "catalog.db"


def check():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
        if row is None or int(row[0]) != 3:
            return False
        missing = conn.execute(
            "SELECT COUNT(*) FROM products WHERE final_price_cents IS NULL"
        ).fetchone()[0]
        return missing == 0
    finally:
        conn.close()


def main():
    ok = check()
    print("migration complete" if ok else "migration incomplete")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
