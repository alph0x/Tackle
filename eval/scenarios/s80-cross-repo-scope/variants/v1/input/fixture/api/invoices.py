"""Invoices."""
from rates import LATE_FEE_BP, LATE_FEE_CAP_BP, PERIOD_DAYS  # noqa: F401


def invoice_total_cents(lines):
    """Sum of (unit_cents, quantity) lines."""
    return sum(unit * quantity for unit, quantity in lines)


def late_fee_cents(amount_cents, days_late):
    """Fee added to an overdue invoice."""
    raise NotImplementedError("late fee")


def late_fee_label():
    """The late-fee rate in the wording the storefront uses."""
    raise NotImplementedError("late fee label")
