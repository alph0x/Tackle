"""Protected checkout calculation checks."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from change_gate import calculate_order


class OrderTotalTests(unittest.TestCase):
    def test_quantity_contributes_to_subtotal(self):
        result = calculate_order(
            [{"unit_price_cents": 1250, "quantity": 2}],
            discount_bps=0,
            tax_bps=0,
        )
        self.assertEqual(result, {
            "subtotal_cents": 2500,
            "discount_cents": 0,
            "tax_cents": 0,
            "total_cents": 2500,
        })

    def test_discount_precedes_tax(self):
        result = calculate_order(
            [{"unit_price_cents": 2899, "quantity": 1}],
            discount_bps=1250,
            tax_bps=825,
        )
        self.assertEqual(result, {
            "subtotal_cents": 2899,
            "discount_cents": 362,
            "tax_cents": 209,
            "total_cents": 2746,
        })

    def test_half_cent_rounds_up(self):
        result = calculate_order(
            [{"unit_price_cents": 1001, "quantity": 1}],
            discount_bps=5000,
            tax_bps=0,
        )
        self.assertEqual(result["discount_cents"], 501)
        self.assertEqual(result["total_cents"], 500)

    def test_empty_basket(self):
        self.assertEqual(calculate_order([], 0, 825), {
            "subtotal_cents": 0,
            "discount_cents": 0,
            "tax_cents": 0,
            "total_cents": 0,
        })


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OrderTotalTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
