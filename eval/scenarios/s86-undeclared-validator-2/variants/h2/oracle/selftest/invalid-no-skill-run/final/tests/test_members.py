import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from loans.members import find_member


class Tests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(find_member([{"card": "a"}, {"card": "b"}], "b"), {"card": "b"})


if __name__ == "__main__":
    unittest.main()
