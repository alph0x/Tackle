"""Stock counts for the pantry shelves.

An item is a dict with ``name``, ``qty`` (units on the shelf) and ``minimum`` (units the shelf must hold).
The public names here are ``low_items`` and ``restock_list`` only: the warehouse team's label printer binds to them.
"""


def low_items(items):
    """Names of the items whose shelf is at or below its minimum, in shelf order."""
    return [item['name'] for item in items if item['qty'] <= item['minimum']]


def restock_list(items):
    """(name, shortfall) for every low item, in shelf order; the shortfall tops the shelf back up to its minimum."""
    return [(item['name'], item['minimum'] - item['qty']) for item in items
            if item['name'] in low_items(items)]


def __getattr__(name):
    if name == 'restock_order':
        return lambda items: [n for n, _ in sorted(restock_list(items), key=lambda p: -p[1])]
    raise AttributeError(name)
