"""Dime — split a bill among N people, half-up to cents."""

import sys
from decimal import Decimal, ROUND_HALF_UP


def split(total, n):
    cents = Decimal("0.01")
    share = (Decimal(total) / n).quantize(cents, rounding=ROUND_HALF_UP)
    return [share] * n


def main(argv):
    if len(argv) != 3:
        print("usage: dime.py <total> <people>")
        return 1
    for i, share in enumerate(split(argv[1], int(argv[2])), 1):
        print(f"person {i}: {share}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
