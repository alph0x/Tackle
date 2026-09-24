"""Cash-rounding helper for the register."""


def round_to_nickel(amount):
    """Round a dollar amount to a nickel increment for cash handling.

    For amounts that don't already land on a nickel, which nickel to round to
    is still being decided between two teams that rely on this function;
    this implementation does not yet commit to either convention.
    """
    return round(amount * 20) / 20
