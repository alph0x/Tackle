"""Invoices."""
from rates import LATE_FEE_BP, LATE_FEE_CAP_BP, PERIOD_DAYS  # noqa: F401


def invoice_total_cents(lines):
    """Sum of (unit_cents, quantity) lines."""
    return sum(unit * quantity for unit, quantity in lines)


def late_fee_cents(amount_cents, days_late):
    """Fee added to an overdue invoice."""
    if days_late <= 0:
        return 0
    periods = -(-days_late // PERIOD_DAYS)
    fee = amount_cents * LATE_FEE_BP * periods // 10000
    return min(fee, amount_cents * LATE_FEE_CAP_BP // 10000)
