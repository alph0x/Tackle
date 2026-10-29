"""Fee rules for one seed lot."""

RATE_CENTS = 1500
FREE_UNITS = 1


def _fine_impl(units):
    """Cents owed for one lot measured in years: nothing inside the free allowance, then a flat rate per unit."""
    if units <= FREE_UNITS:
        return 0
    return (units - FREE_UNITS) * RATE_CENTS


storage_fee = _fine_impl
