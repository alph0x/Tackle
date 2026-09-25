import unittest

from pettyledger.currency import format_currency


class TestFormatCurrency(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(format_currency(0), "$0.00")

    def test_small_positive(self):
        self.assertEqual(format_currency(5), "$0.05")

    def test_whole_dollars(self):
        self.assertEqual(format_currency(1200), "$12.00")

    def test_thousands_separator(self):
        self.assertEqual(format_currency(123456789), "$1,234,567.89")


if __name__ == "__main__":
    unittest.main()
