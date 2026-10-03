"""Sum the movement journal into a booked quantity per bin."""
import csv

from stock.units import to_units

INBOUND = ('receipt', 'transfer-in')
OUTBOUND = ('issue', 'transfer-out')
SIGN = dict([(kind, 1) for kind in INBOUND] + [(kind, -1) for kind in OUTBOUND])


def load_packs(path):
    with open(path, encoding='utf-8') as handle:
        return {row['item']: int(row['pack']) for row in csv.DictReader(handle)}


def booked(path, packs):
    totals = {}
    with open(path, encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            sign = SIGN.get(row['kind'])
            if sign is None:
                continue
            units = to_units(row['qty'], row['uom'], packs[row['item']])
            totals[row['bin']] = totals.get(row['bin'], 0) + sign * units
    return totals
