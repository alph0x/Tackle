import unittest

from money import parse_amount


class TestParseAmount(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(parse_amount("19.99"), 19.99)

    def test_thousands_separator(self):
        self.assertEqual(parse_amount("1,234.56"), 1234.56)

    def test_currency_prefix(self):
        self.assertEqual(parse_amount("$1,234.56"), 1234.56)


if __name__ == "__main__":
    unittest.main()
