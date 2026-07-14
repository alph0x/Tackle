# Pricing

This module computes a unit price with a bulk discount.

**Spec:** orders of 100 units or more receive a 10% discount off the base unit price of $2.00. So the discounted unit price for qty >= 100 is $1.80.

```python
def unit_price(qty):
    """Return the per-unit price for an order of `qty` units."""
    base = 2.00
    if qty >= 100:
        return round(base * 0.90, 2)  # 10% bulk discount
    return base
```
