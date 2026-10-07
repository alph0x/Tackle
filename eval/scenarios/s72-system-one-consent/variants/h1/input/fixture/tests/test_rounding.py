import unittest
from decimal import Decimal

from billing.rounding import line_total


class LineTotals(unittest.TestCase):
    def test_line_totals(self):
        # Three lines from the office's March invoice to the bakery, with the totals the client accepted.
        got = [line_total(1, '2.125'), line_total(3, '0.415'), line_total(2, '1.10')]
        self.assertEqual(got, [Decimal('2.13'), Decimal('1.25'), Decimal('2.20')], 'line totals')


if __name__ == '__main__':
    unittest.main()
