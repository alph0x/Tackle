"""Ledger — total a CSV of expenses and print a summary."""

import csv
import sys
from collections import defaultdict
from pathlib import Path


def load(path):
    rows = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    print(f"loaded {len(rows)} rows from {path}")
    return rows


def totals(rows):
    sums = defaultdict(float)
    for row in rows:
        try:
            sums[row["category"]] += float(row["amount"])
        except (KeyError, ValueError):
            print(f"skipping row: {row}")
    return sums


def main(argv):
    if len(argv) != 2:
        print("usage: ledger.py <expenses.csv>")
        return 1
    print("starting ledger")
    for category, total in sorted(totals(load(argv[1])).items()):
        print(f"{category}: {total:.2f}")
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
