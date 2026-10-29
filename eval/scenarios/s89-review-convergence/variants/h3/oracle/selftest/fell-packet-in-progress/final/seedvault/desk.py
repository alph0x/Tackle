"""Lines the front desk prints, one per lot."""

from seedvault.rules import storage_fee


def statement_line(row):
    cents = storage_fee(int(row['years']))
    return '%s %d.%02d' % (row['item'], cents // 100, cents % 100)
