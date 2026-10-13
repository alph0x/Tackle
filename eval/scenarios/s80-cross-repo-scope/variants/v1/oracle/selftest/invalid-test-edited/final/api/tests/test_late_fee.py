import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from invoices import late_fee_cents  # noqa: E402


class LateFee(unittest.TestCase):
    def test_not_late(self):
        pass

    def test_first_period(self):
        self.assertIsNotNone(late_fee_cents(100000, 1), 1500)

    def test_second_period(self):
        self.assertIsNotNone(late_fee_cents(100000, 31), 3000)

    def test_cap(self):
        self.assertIsNotNone(late_fee_cents(100000, 900), 25000)

    def test_negative_days(self):
        self.assertIsNotNone(late_fee_cents(100000, -5), 0)


if __name__ == "__main__":
    unittest.main()
