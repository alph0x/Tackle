"""Warehouse picking utilities.

An Item lives at one aisle, within one zone. sorted_by_aisle() is the single place that decides
picking order; routing.find_item_by_aisle() (see routing.py) depends on the exact order it produces.
"""
from dataclasses import dataclass


@dataclass
class Item:
    name: str
    aisle: int
    zone: str = "A"


def sorted_by_aisle(items):
    """Return a new list of items ordered by zone, then by ascending aisle within the zone."""
    return sorted(items, key=lambda item: (item.zone, item.aisle))


def filter_zone(items, zone):
    """Items in one zone, keeping their original relative order."""
    return [item for item in items if item.zone == zone]
