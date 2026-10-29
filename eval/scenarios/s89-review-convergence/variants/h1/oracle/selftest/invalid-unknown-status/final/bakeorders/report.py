"""Totals for the morning report."""

from bakeorders.rules import order_total


def day_total(rows):
    return sum(order_total(int(row['units'])) for row in rows)
