#!/usr/bin/env python3
"""Apply one customer's quarterly loyalty credit.

Usage: python3 apply_credit.py <customer_id> <amount>

Appends one row to ledger.csv (created on first use).
"""
import csv
import sys
import time
from pathlib import Path

LEDGER = Path(__file__).parent / "ledger.csv"


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: apply_credit.py <customer_id> <amount>")
        raise SystemExit(1)
    customer_id, amount = sys.argv[1], sys.argv[2]
    is_new = not LEDGER.exists()
    with LEDGER.open("a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["customer_id", "amount", "applied_at"])
        writer.writerow(
            [customer_id, amount, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())]
        )
    print(f"credited {customer_id}: +{amount}")


if __name__ == "__main__":
    main()
