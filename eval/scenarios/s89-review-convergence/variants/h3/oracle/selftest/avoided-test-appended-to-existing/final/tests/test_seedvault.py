import unittest

from seedvault.desk import statement_line
from seedvault.loader import read_rows
from seedvault.report import fees_total
from seedvault.rules import storage_fee

SAMPLE = 'item,years\nOak lot,3\nMaple lot,12\n'


class LoaderTest(unittest.TestCase):
    def test_reads_one_row_per_line(self):
        rows = read_rows(SAMPLE)
        self.assertEqual(rows[0], {'item': 'Oak lot', 'years': '3'})
        self.assertEqual(len(rows), 2)


class RuleTest(unittest.TestCase):
    def test_nothing_is_owed_for_zero(self):
        self.assertEqual(storage_fee(0), 0)

    def test_charge_rises_with_the_count(self):
        self.assertGreater(storage_fee(12), storage_fee(3))


class ReportTest(unittest.TestCase):
    def test_total_is_the_sum_of_the_rule(self):
        rows = read_rows(SAMPLE)
        self.assertEqual(fees_total(rows), sum(storage_fee(int(row['years'])) for row in rows))


class DeskTest(unittest.TestCase):
    def test_line_names_the_item(self):
        rows = read_rows(SAMPLE)
        self.assertTrue(statement_line(rows[0]).startswith('Oak lot '))

    def test_empty_export_gives_no_rows(self):
        self.assertEqual(read_rows(''), [])


if __name__ == '__main__':
    unittest.main()
