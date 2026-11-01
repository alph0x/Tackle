"""Lines the front desk prints, one per loan."""

from loanfines.rules import overdue_fine


def receipt_line(row):
    cents = overdue_fine(int(row['days_late']))
    return '%s %d.%02d' % (row['item'], cents // 100, cents % 100)
