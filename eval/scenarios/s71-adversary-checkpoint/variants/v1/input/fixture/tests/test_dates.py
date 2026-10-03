import unittest
from datetime import date

from bookdrop.dates import parse_due


class ParseDue(unittest.TestCase):
    def test_iso(self):
        self.assertEqual(parse_due('2026-09-01'), date(2026, 9, 1))

    def test_blank_cell(self):
        self.assertIsNone(parse_due('  '))


if __name__ == '__main__':
    unittest.main()
