import unittest

from pantry import stock

SHELF = [
    {'name': 'rice', 'qty': 4, 'minimum': 10},
    {'name': 'beans', 'qty': 6, 'minimum': 6},
    {'name': 'oil', 'qty': 9, 'minimum': 3},
    {'name': 'pasta', 'qty': 1, 'minimum': 3},
]


class LowItemsTest(unittest.TestCase):
    def test_at_or_below_minimum_is_low(self):
        self.assertEqual(stock.low_items(SHELF), ['rice', 'beans', 'pasta'])


class RestockTest(unittest.TestCase):
    def test_restock_list_in_shelf_order(self):
        self.assertEqual(stock.restock_list(SHELF), [('rice', 6), ('beans', 0), ('pasta', 2)])

    def test_volunteer_sheet_order(self):
        # The Saturday volunteer sheet lists the biggest gaps first.
        self.assertEqual([n for n, _ in sorted(stock.restock_list(SHELF), key=lambda p: -p[1])], ['rice', 'pasta', 'beans'])


if __name__ == '__main__':
    unittest.main()
