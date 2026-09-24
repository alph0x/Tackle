import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from billing import round_to_nickel


class TestTillTotals(unittest.TestCase):
    def test_common_amount(self):
        self.assertEqual(round_to_nickel(0.12), 0.15)

    def test_exact_nickel(self):
        self.assertEqual(round_to_nickel(0.10), 0.10)


if __name__ == "__main__":
    unittest.main()
