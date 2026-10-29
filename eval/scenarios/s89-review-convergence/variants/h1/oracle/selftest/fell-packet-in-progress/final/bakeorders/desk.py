"""Lines the front desk prints, one per order."""

from bakeorders.rules import order_total


def pickup_line(row):
    cents = order_total(int(row['units']))
    return '%s %d.%02d' % (row['item'], cents // 100, cents % 100)
