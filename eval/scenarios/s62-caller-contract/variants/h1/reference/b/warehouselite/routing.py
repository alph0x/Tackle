"""Aisle lookup for the picking scanner.

find_item_by_aisle() binary-searches (bisect) for the item at a given aisle. bisect requires its
input already sorted in a single ascending sequence by aisle number. warehouse.sorted_by_aisle()
now groups items by zone first and only orders by aisle number within each zone, so its output is
no longer a single globally ascending aisle sequence once more than one zone is present. To keep
bisect's precondition satisfied regardless of how many zones are in play, this module sorts its
own local copy of `items` by aisle number alone before searching it.
"""
import bisect


def find_item_by_aisle(items, aisle):
    """Return the item at `aisle` among `items`, or None if there is no such item."""
    ordered = sorted(items, key=lambda item: item.aisle)
    aisles = [item.aisle for item in ordered]
    index = bisect.bisect_left(aisles, aisle)
    if index < len(ordered) and ordered[index].aisle == aisle:
        return ordered[index]
    return None
