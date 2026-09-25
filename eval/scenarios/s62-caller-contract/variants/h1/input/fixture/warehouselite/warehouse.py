"""Warehouse picking utilities.

An Item lives at one aisle. sorted_by_aisle() is the single place that decides picking order.
"""
from dataclasses import dataclass


@dataclass
class Item:
    name: str
    aisle: int


def sorted_by_aisle(items):
    """Return a new list of items ordered by ascending aisle number."""
    return sorted(items, key=lambda item: item.aisle)
