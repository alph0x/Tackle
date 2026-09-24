def apply_discount(price: float, pct: float) -> float:
    """Apply a percentage discount to a price.

    pct is clamped to [0, 100] so a bad input can't inflate the price or
    push it negative.
    """
    pct = max(0.0, min(100.0, pct))
    return price * (1 - pct / 100)
