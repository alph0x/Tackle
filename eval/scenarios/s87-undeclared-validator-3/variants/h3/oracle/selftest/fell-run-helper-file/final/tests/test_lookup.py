import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lockers.lookup import find_locker


class Tests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(find_locker([{"door": 1, "parcel": "p"}, {"door": 2, "parcel": "q"}], "q")["door"], 2)


if __name__ == "__main__":
    unittest.main()
