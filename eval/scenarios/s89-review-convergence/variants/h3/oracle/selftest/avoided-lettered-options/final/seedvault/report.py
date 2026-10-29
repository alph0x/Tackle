"""Totals for the morning report."""

from seedvault.rules import storage_fee


def fees_total(rows):
    return sum(storage_fee(int(row['years'])) for row in rows)
