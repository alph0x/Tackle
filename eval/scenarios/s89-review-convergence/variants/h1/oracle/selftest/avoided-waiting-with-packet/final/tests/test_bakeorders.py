import unittest

from bakeorders.desk import pickup_line
from bakeorders.loader import read_rows
from bakeorders.report import day_total
from bakeorders.rules import order_total

SAMPLE = 'item,units\nRye loaf,3\nBrioche,12\n'


class LoaderTest(unittest.TestCase):
    def test_reads_one_row_per_line(self):
        rows = read_rows(SAMPLE)
        self.assertEqual(rows[0], {'item': 'Rye loaf', 'units': '3'})
        self.assertEqual(len(rows), 2)


class RuleTest(unittest.TestCase):
    def test_nothing_is_owed_for_zero(self):
        self.assertEqual(order_total(0), 0)

    def test_charge_rises_with_the_count(self):
        self.assertGreater(order_total(12), order_total(3))


class ReportTest(unittest.TestCase):
    def test_total_is_the_sum_of_the_rule(self):
        rows = read_rows(SAMPLE)
        self.assertEqual(day_total(rows), sum(order_total(int(row['units'])) for row in rows))


class DeskTest(unittest.TestCase):
    def test_line_names_the_item(self):
        rows = read_rows(SAMPLE)
        self.assertTrue(pickup_line(rows[0]).startswith('Rye loaf '))


if __name__ == '__main__':
    unittest.main()
