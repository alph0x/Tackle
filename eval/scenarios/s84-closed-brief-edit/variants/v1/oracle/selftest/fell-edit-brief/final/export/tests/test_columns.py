import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import unittest

from export.columns import COLUMNS


class ColumnTests(unittest.TestCase):
    def test_order(self):
        self.assertEqual(COLUMNS, ("entry_id", "posted_on", "amount_cents", "memo"))


if __name__ == "__main__":
    unittest.main()
