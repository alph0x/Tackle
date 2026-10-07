"""Line totals in euro cents."""
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal('0.01')


def line_total(quantity, unit_price):
    """quantity: int; unit_price: text such as '2.125'. Returns the line total rounded to the cent."""
    return (Decimal(quantity) * Decimal(unit_price)).quantize(CENT, rounding=ROUND_HALF_UP)
