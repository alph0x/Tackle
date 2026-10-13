import unittest

from splitbill.split import split_cents


class SplitTest(unittest.TestCase):
    def test_even(self):
        self.assertEqual(split_cents(900, 3), [300, 300, 300])

    def test_shares_add_up(self):
        self.assertEqual(sum(split_cents(1000, 3)), 1000)


if __name__ == "__main__":
    unittest.main()
