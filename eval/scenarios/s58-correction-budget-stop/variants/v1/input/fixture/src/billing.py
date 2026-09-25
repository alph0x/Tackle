"""Cash-rounding helper for the register."""


def round_to_nickel(amount):
    """Round a dollar amount to a nickel increment for cash handling."""
    return round(amount * 20) / 20
