"""Lines the front desk prints, one per rental."""

from bikeledger.rules import rental_charge


def slip_line(row):
    cents = rental_charge(int(row['hours']))
    return '%s %d.%02d' % (row['item'], cents // 100, cents % 100)
