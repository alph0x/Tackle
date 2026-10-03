#!/usr/bin/env python3
"""Confirm that an adjustment is in the journal.

usage: python3 tools/check_adjustment.py <account> <memo>
exit 0 when at least one row matches and the journal header is intact, 1 otherwise.
"""
import csv
import sys
from pathlib import Path

JOURNAL = Path(__file__).resolve().parents[1] / "data" / "adjustments.csv"
HEADER = ["posted_on", "account", "amount", "memo", "posted_at"]


def main(argv):
    if len(argv) != 3:
        sys.stderr.write("usage: python3 tools/check_adjustment.py <account> <memo>\n")
        return 2
    with JOURNAL.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header != HEADER:
            print("check: journal header is not %s" % ",".join(HEADER))
            return 1
        rows = [row for row in reader if len(row) == 5 and row[1] == argv[1] and row[3] == argv[2]]
    if not rows:
        print("check: no row for %s / %s" % (argv[1], argv[2]))
        return 1
    print("check: found %d row(s) for %s / %s" % (len(rows), argv[1], argv[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
