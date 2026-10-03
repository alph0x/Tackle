"""Month-end check: the physical count must equal the booked quantity in every bin."""
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from stock.moves import booked, load_packs  # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def main():
    packs = load_packs(os.path.join(DATA, 'packs.csv'))
    totals = booked(os.path.join(DATA, 'journal-2026-09.csv'), packs)
    mismatches = 0
    with open(os.path.join(DATA, 'count-2026-09.csv'), encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            counted, have = int(row['counted']), totals.get(row['bin'], 0)
            if counted != have:
                mismatches += 1
                print('MISMATCH bin %s: counted %d, booked %d' % (row['bin'], counted, have))
    print('verify: %d bins, %d mismatched' % (len(totals), mismatches))
    return 1 if mismatches else 0


if __name__ == '__main__':
    sys.exit(main())
