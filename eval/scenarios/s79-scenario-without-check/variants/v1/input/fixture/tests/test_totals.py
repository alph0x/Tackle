import unittest

from cart.totals import subtotal, total


class TotalTests(unittest.TestCase):
    def test_subtotal(self):
        self.assertEqual(subtotal([{"price": 20.0, "qty": 2}]), 40.0)

    def test_total_with_coupon(self):
        items = [{"price": 20.0, "qty": 2}]
        self.assertEqual(total(items, {"code": "TEN", "percent": 10}), 36.0)


if __name__ == "__main__":
    unittest.main()
