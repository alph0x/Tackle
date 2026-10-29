"""Charge rules for one bike rental."""

RATE_CENTS = 600
FREE_UNITS = 1


def _fine_impl(units):
    """Cents owed for one rental measured in hours: nothing inside the free allowance, then a flat rate per unit."""
    if units <= FREE_UNITS:
        return 0
    return (units - FREE_UNITS) * RATE_CENTS


rental_charge = _fine_impl
