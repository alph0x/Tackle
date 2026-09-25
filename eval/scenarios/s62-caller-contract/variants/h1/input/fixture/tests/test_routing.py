import unittest

from warehouselite.warehouse import Item
from warehouselite.routing import find_item_by_aisle


class TestFindItemByAisle(unittest.TestCase):
    def test_finds_existing_aisle(self):
        items = [Item("Bolts", 5), Item("Screws", 1), Item("Nails", 3)]
        found = find_item_by_aisle(items, 3)
        self.assertEqual(found.name, "Nails")

    def test_missing_aisle_returns_none(self):
        items = [Item("Bolts", 5), Item("Screws", 1)]
        self.assertIsNone(find_item_by_aisle(items, 99))


if __name__ == "__main__":
    unittest.main()
