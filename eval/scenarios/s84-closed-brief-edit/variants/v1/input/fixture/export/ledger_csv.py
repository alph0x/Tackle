"""Writes ledger entries as CSV (T-2102)."""
from export.columns import COLUMNS


def format_row(entry):
    return ",".join(str(entry[column]) for column in COLUMNS)


def write_rows(entries, out):
    out.write(",".join(COLUMNS) + "\n")
    for entry in entries:
        out.write(format_row(entry) + "\n")
