"""Aisle lookup for the picking scanner.

find_item_by_aisle() searches warehouse.sorted_by_aisle()'s output for the item at a given aisle.
Aisle numbers are only meaningful within one zone, so sorted_by_aisle() no longer produces one
globally ascending aisle sequence once more than one zone is in play -- this can no longer binary
-search on raw aisle number the way it once did, and instead scans the (zone-grouped) order.
"""
from .warehouse import sorted_by_aisle


def find_item_by_aisle(items, aisle):
    """Return the item at `aisle` among `items`, or None if there is no such item."""
    for item in sorted_by_aisle(items):
        if item.aisle == aisle:
            return item
    return None
