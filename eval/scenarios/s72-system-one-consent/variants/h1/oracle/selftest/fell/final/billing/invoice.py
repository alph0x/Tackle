"""Invoice totals from line totals."""
from decimal import Decimal

from billing.rounding import line_total


def invoice_total(lines):
    """lines: (quantity, unit_price) pairs. The total is the sum of the rounded line totals."""
    return sum((line_total(quantity, price) for quantity, price in lines), Decimal('0.00'))
