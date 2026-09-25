import unittest

from warehouselite.warehouse import Item, sorted_by_aisle


class TestItem(unittest.TestCase):
    def test_fields(self):
        item = Item("Bolts", 4)
        self.assertEqual(item.name, "Bolts")
        self.assertEqual(item.aisle, 4)


class TestSortedByAisle(unittest.TestCase):
    def test_orders_ascending(self):
        items = [Item("Bolts", 5), Item("Screws", 1), Item("Nails", 3)]
        ordered = sorted_by_aisle(items)
        self.assertEqual([item.name for item in ordered], ["Screws", "Nails", "Bolts"])


if __name__ == "__main__":
    unittest.main()
