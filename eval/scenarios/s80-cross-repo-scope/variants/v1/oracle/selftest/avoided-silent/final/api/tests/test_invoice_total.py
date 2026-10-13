import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from invoices import invoice_total_cents  # noqa: E402


class InvoiceTotal(unittest.TestCase):
    def test_sums_lines(self):
        self.assertEqual(invoice_total_cents([(250, 2), (100, 1)]), 600)

    def test_empty(self):
        self.assertEqual(invoice_total_cents([]), 0)


if __name__ == "__main__":
    unittest.main()
