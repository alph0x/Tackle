"""Writes ledger entries as CSV (T-2102)."""
import csv

from export.columns import COLUMNS


def write_rows(entries, out):
    writer = csv.writer(out)
    writer.writerow(COLUMNS)
    for entry in entries:
        writer.writerow([entry[column] for column in COLUMNS])
