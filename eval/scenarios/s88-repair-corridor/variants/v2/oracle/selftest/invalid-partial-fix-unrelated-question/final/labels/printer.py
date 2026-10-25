"""Prints one shelf label per item to restock."""

from pantry.stock import low_items, restock_list


def label_lines(items):
    low = low_items(items)
    return ['RESTOCK %s +%d' % (name, gap) for name, gap in restock_list(items) if name in low]
