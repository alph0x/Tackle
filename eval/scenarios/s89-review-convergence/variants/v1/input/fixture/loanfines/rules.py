"""Charge rules for one library loan."""

RATE_CENTS = 25
FREE_UNITS = 2


def overdue_fine(units):
    """Cents owed for one loan measured in days_late: nothing inside the free allowance, then a flat rate per unit."""
    if units <= FREE_UNITS:
        return 0
    return (units - FREE_UNITS) * RATE_CENTS
