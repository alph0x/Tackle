"""Pricing: checkout discount math with a 50% cap."""

DISCOUNT_CAP = 0.50


def final_price(line_total, discount):
    """Apply discount (0..1) clamped to DISCOUNT_CAP."""
    d = min(discount, DISCOUNT_CAP)
    return line_total * (1 - d)
