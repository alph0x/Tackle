"""Totals for the morning report."""

from bikeledger.rules import rental_charge


def takings_total(rows):
    return sum(rental_charge(int(row['hours'])) for row in rows)
