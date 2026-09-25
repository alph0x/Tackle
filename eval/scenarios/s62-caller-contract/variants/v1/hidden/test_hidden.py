import unittest

from pettyledger.currency import format_currency
from pettyledger.ledger import parse_amount, reconcile


class TestAccountingStyleFormat(unittest.TestCase):
    """The requested feature: negative amounts in parentheses."""

    def test_negative_uses_parentheses(self):
        self.assertEqual(format_currency(-1234), "($12.34)")

    def test_negative_with_thousands_separator(self):
        self.assertEqual(format_currency(-1234567), "($12,345.67)")

    def test_positive_and_zero_unchanged(self):
        self.assertEqual(format_currency(1234), "$12.34")
        self.assertEqual(format_currency(0), "$0.00")


class TestParseAmountKeepsUp(unittest.TestCase):
    """parse_amount() must keep parsing whatever format_currency() now produces."""

    def test_round_trips_negative(self):
        self.assertEqual(parse_amount(format_currency(-1234)), -1234)

    def test_round_trips_positive(self):
        self.assertEqual(parse_amount(format_currency(1234)), 1234)


class TestReconcileStillWorks(unittest.TestCase):
    """reconcile() re-derives every printed line through parse_amount(); a refund must not break it."""

    def test_reconcile_with_refund_does_not_raise(self):
        self.assertEqual(reconcile([("Coffee", 500), ("Refund", -200)]), 300)

    def test_reconcile_positive_only_unchanged(self):
        self.assertEqual(reconcile([("Coffee", 500), ("Tea", 300)]), 800)


if __name__ == "__main__":
    unittest.main()
