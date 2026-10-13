import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from quota import remaining_requests  # noqa: E402


class Remaining(unittest.TestCase):
    def test_fresh_day(self):
        self.assertEqual(remaining_requests("free", 0), 100)

    def test_partly_used(self):
        self.assertEqual(remaining_requests("pro", 2500), 7500)

    def test_over_the_limit(self):
        self.assertEqual(remaining_requests("free", 150), 0)

    def test_unknown_plan(self):
        with self.assertRaises(KeyError):
            remaining_requests("gold", 1)


if __name__ == "__main__":
    unittest.main()
