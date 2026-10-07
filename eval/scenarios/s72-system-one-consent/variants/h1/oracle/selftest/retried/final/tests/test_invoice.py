import unittest
from decimal import Decimal

from billing.invoice import invoice_total


class InvoiceTotals(unittest.TestCase):
    def test_empty_invoice(self):
        self.assertEqual(invoice_total([]), Decimal('0.00'))

    def test_whole_cents(self):
        self.assertEqual(invoice_total([(2, '1.10'), (1, '3.00')]), Decimal('5.20'))


if __name__ == '__main__':
    unittest.main()
