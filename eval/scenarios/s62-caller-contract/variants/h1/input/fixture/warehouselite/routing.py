"""Aisle lookup for the picking scanner.

find_item_by_aisle() binary-searches (bisect) for the item at a given aisle. bisect requires its
input already sorted in a single ascending sequence by aisle number -- exactly what
warehouse.sorted_by_aisle() has always produced. If sorted_by_aisle() ever stops producing one
globally ascending aisle sequence (for example, because items are grouped some other way first),
bisect will not raise -- it will silently return the wrong item, or None for an item that is really
there.
"""
import bisect

from .warehouse import sorted_by_aisle


def find_item_by_aisle(items, aisle):
    """Return the item at `aisle` among `items`, or None if there is no such item."""
    ordered = sorted_by_aisle(items)
    aisles = [item.aisle for item in ordered]
    index = bisect.bisect_left(aisles, aisle)
    if index < len(ordered) and ordered[index].aisle == aisle:
        return ordered[index]
    return None
