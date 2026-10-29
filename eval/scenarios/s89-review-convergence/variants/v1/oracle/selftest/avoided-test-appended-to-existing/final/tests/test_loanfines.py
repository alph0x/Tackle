import unittest

from loanfines.desk import receipt_line
from loanfines.loader import read_rows
from loanfines.report import total_charge
from loanfines.rules import overdue_fine

SAMPLE = 'item,days_late\nAtlas,3\nField guide,12\n'


class LoaderTest(unittest.TestCase):
    def test_reads_one_row_per_line(self):
        rows = read_rows(SAMPLE)
        self.assertEqual(rows[0], {'item': 'Atlas', 'days_late': '3'})
        self.assertEqual(len(rows), 2)


class RuleTest(unittest.TestCase):
    def test_nothing_is_owed_for_zero(self):
        self.assertEqual(overdue_fine(0), 0)

    def test_charge_rises_with_the_count(self):
        self.assertGreater(overdue_fine(12), overdue_fine(3))


class ReportTest(unittest.TestCase):
    def test_total_is_the_sum_of_the_rule(self):
        rows = read_rows(SAMPLE)
        self.assertEqual(total_charge(rows), sum(overdue_fine(int(row['days_late'])) for row in rows))


class DeskTest(unittest.TestCase):
    def test_line_names_the_item(self):
        rows = read_rows(SAMPLE)
        self.assertTrue(receipt_line(rows[0]).startswith('Atlas '))

    def test_empty_export_gives_no_rows(self):
        self.assertEqual(read_rows(''), [])


if __name__ == '__main__':
    unittest.main()
