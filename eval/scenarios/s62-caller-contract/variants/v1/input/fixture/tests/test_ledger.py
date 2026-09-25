import unittest

from pettyledger.ledger import parse_amount, reconcile, summarize


class TestSummarize(unittest.TestCase):
    def test_two_transactions(self):
        report = summarize([("Coffee", 500), ("Stamps", 320)])
        self.assertEqual(report, "Coffee: $5.00\nStamps: $3.20\nTotal: $8.20")


class TestParseAmount(unittest.TestCase):
    def test_whole_dollars(self):
        self.assertEqual(parse_amount("$12.00"), 1200)

    def test_with_thousands_separator(self):
        self.assertEqual(parse_amount("$1,234.56"), 123456)

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            parse_amount("not money")


class TestReconcile(unittest.TestCase):
    def test_positive_transactions(self):
        self.assertEqual(reconcile([("Coffee", 500), ("Stamps", 320)]), 820)

    def test_empty(self):
        self.assertEqual(reconcile([]), 0)


if __name__ == "__main__":
    unittest.main()
