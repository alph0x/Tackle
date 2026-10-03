#!/usr/bin/env python3
"""Append one adjustment to data/adjustments.csv.

usage: python3 tools/post_adjustment.py --account ACC-1042 --amount 150.00 --memo "Q3 true-up" --date 2026-09-27
"""
import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "data" / "adjustments.csv"
ACCOUNTS = ROOT / "data" / "accounts.csv"


def main():
    parser = argparse.ArgumentParser(description="post one adjustment to the journal")
    parser.add_argument("--account", required=True)
    parser.add_argument("--amount", required=True, type=float)
    parser.add_argument("--memo", required=True)
    parser.add_argument("--date", required=True, help="posting date, YYYY-MM-DD")
    args = parser.parse_args()
    with ACCOUNTS.open(newline="", encoding="utf-8") as handle:
        known = {row["account"] for row in csv.DictReader(handle)}
    if args.account not in known:
        sys.stderr.write("unknown account: %s\n" % args.account)
        return 2
    datetime.strptime(args.date, "%Y-%m-%d")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with JOURNAL.open("a", newline="", encoding="utf-8") as handle:
        csv.writer(handle, lineterminator="\n").writerow([args.date, args.account, "%.2f" % args.amount, args.memo, stamp])
    print("posted: %s %s %.2f (%s) at %s" % (args.date, args.account, args.amount, args.memo, stamp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
