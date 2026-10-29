"""Totals for the morning report."""

from loanfines.rules import overdue_fine


def total_charge(rows):
    return sum(overdue_fine(int(row['days_late'])) for row in rows)
