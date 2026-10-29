import unittest

from bikeledger.desk import slip_line
from bikeledger.loader import read_rows
from bikeledger.report import takings_total
from bikeledger.rules import rental_charge

SAMPLE = 'item,hours\nCity bike,3\nE-bike,12\n'


class LoaderTest(unittest.TestCase):
    def test_reads_one_row_per_line(self):
        rows = read_rows(SAMPLE)
        self.assertEqual(rows[0], {'item': 'City bike', 'hours': '3'})
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows)


class RuleTest(unittest.TestCase):
    def test_nothing_is_owed_for_zero(self):
        self.assertEqual(rental_charge(0), 0)

    def test_charge_rises_with_the_count(self):
        self.assertGreater(rental_charge(12), rental_charge(3))


class ReportTest(unittest.TestCase):
    def test_total_is_the_sum_of_the_rule(self):
        rows = read_rows(SAMPLE)
        self.assertEqual(takings_total(rows), sum(rental_charge(int(row['hours'])) for row in rows))


class DeskTest(unittest.TestCase):
    def test_line_names_the_item(self):
        rows = read_rows(SAMPLE)
        self.assertTrue(slip_line(rows[0]).startswith('City bike '))


if __name__ == '__main__':
    unittest.main()
