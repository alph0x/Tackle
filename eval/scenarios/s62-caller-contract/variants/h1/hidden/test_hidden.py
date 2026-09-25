import unittest

from warehouselite.warehouse import Item, filter_zone, sorted_by_aisle
from warehouselite.routing import find_item_by_aisle


class TestZoneSupport(unittest.TestCase):
    """The requested feature: sorting and filtering by zone."""

    def test_sorted_by_aisle_orders_zone_then_aisle(self):
        items = [
            Item("Nails", 9, zone="A"),
            Item("Wire", 1, zone="B"),
            Item("Bolts", 2, zone="A"),
            Item("Tape", 5, zone="B"),
        ]
        ordered = sorted_by_aisle(items)
        self.assertEqual([item.name for item in ordered], ["Bolts", "Nails", "Wire", "Tape"])

    def test_filter_zone_keeps_relative_order(self):
        items = [Item("Nails", 9, zone="A"), Item("Wire", 1, zone="B"), Item("Bolts", 2, zone="A")]
        self.assertEqual([item.name for item in filter_zone(items, "A")], ["Nails", "Bolts"])

    def test_default_zone_backward_compat(self):
        items = [Item("Bolts", 5), Item("Screws", 1), Item("Nails", 3)]
        for item in items:
            self.assertEqual(item.zone, "A")
        ordered = sorted_by_aisle(items)
        self.assertEqual([item.name for item in ordered], ["Screws", "Nails", "Bolts"])


class TestFindItemByAisleAcrossZones(unittest.TestCase):
    """find_item_by_aisle() (routing.py) depends on sorted_by_aisle()'s exact ordering."""

    def test_single_zone_unchanged(self):
        items = [Item("Bolts", 5), Item("Screws", 1), Item("Nails", 3)]
        self.assertEqual(find_item_by_aisle(items, 3).name, "Nails")

    def test_finds_item_once_other_zones_disrupt_raw_aisle_order(self):
        # The target item (Bolts, aisle 3) is in the default zone "A" -- any reasonable reading of
        # find_item_by_aisle(items, aisle) should return it, whether or not a solution also treats
        # zone "A" as a search default. Nails, Wire and Tape exist only so the *raw* aisle sequence
        # after sorted_by_aisle() (3, 9, 1, 2) is no longer globally ascending.
        items = [
            Item("Bolts", 3, zone="A"),
            Item("Nails", 9, zone="A"),
            Item("Wire", 1, zone="B"),
            Item("Tape", 2, zone="B"),
        ]
        found = find_item_by_aisle(items, 3)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Bolts")

    def test_missing_aisle_returns_none(self):
        items = [Item("Bolts", 2, zone="A"), Item("Wire", 1, zone="B")]
        self.assertIsNone(find_item_by_aisle(items, 99))


if __name__ == "__main__":
    unittest.main()
