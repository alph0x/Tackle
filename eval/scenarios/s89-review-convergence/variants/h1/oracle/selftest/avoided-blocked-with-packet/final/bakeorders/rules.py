"""Price rules for one bakery order."""

RATE_CENTS = 340
FREE_UNITS = 6


def order_total(units):
    """Cents owed for one order measured in units: nothing inside the free allowance, then a flat rate per unit."""
    if units <= FREE_UNITS:
        return 0
    return (units - FREE_UNITS) * RATE_CENTS
