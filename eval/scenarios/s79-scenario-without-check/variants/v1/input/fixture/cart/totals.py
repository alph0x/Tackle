"""Cart totals."""


def subtotal(items):
    return round(sum(i["price"] * i["qty"] for i in items), 2)


def total(items, coupon=None):
    base = subtotal(items)
    if coupon is None:
        return base
    return round(base * (1 - coupon["percent"] / 100), 2)
