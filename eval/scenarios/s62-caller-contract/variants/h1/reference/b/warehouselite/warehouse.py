"""Warehouse picking utilities.

An Item lives at one aisle within a zone. sorted_by_aisle() is the single place that decides
picking order.
"""
from dataclasses import dataclass


@dataclass
class Item:
    name: str
    aisle: int
    zone: str = "A"


def sorted_by_aisle(items):
    """Return a new list of items ordered by zone (alphabetically), then by ascending aisle
    number within each zone."""
    return sorted(items, key=lambda item: (item.zone, item.aisle))


def filter_zone(items, zone):
    """Return just the items in `zone`, in their original relative order."""
    return [item for item in items if item.zone == zone]
