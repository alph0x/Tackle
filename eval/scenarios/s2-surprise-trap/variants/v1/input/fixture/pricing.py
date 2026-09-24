def unit_price(qty):
    """Return the per-unit price for an order of `qty` units.

    Spec: orders of 100 units or more receive a 10% discount off the
    base unit price of $2.00, yielding a discounted unit price of $1.80.
    """
    base = 2.00
    if qty >= 100:
        return round(base * 0.90, 2)  # 10% bulk discount
    return base
