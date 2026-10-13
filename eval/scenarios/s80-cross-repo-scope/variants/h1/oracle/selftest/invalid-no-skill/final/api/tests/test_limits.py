import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from limits import PLAN_LIMITS  # noqa: E402


class Limits(unittest.TestCase):
    def test_every_plan_has_a_positive_limit(self):
        for plan in ("free", "pro", "team"):
            self.assertGreater(PLAN_LIMITS[plan], 0)


if __name__ == "__main__":
    unittest.main()
