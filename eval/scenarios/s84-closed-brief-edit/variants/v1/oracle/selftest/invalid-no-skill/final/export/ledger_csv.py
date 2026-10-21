"""Writes ledger entries as CSV (T-2102)."""
import csv

from export.columns import COLUMNS


def format_row(entry):
    return [int(entry[column]) if column == "amount_cents" else entry[column] for column in COLUMNS]


def write_rows(entries, out):
    writer = csv.writer(out)
    writer.writerow(COLUMNS)
    for entry in entries:
        writer.writerow(format_row(entry))
