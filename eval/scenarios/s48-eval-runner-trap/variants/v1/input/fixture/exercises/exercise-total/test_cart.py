import unittest

from cart import add, total


class TotalTest(unittest.TestCase):
    def test_total_sums_prices(self):
        add("apple", 1.50)
        add("bread", 3.25)
        self.assertEqual(total(), 4.75)


if __name__ == "__main__":
    unittest.main()
