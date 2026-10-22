import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from watering.zones import find_zone


class Tests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(find_zone([{"name": "north", "beds": ["a1"]}, {"name": "south", "beds": ["b1"]}], "b1")["name"], "south")


if __name__ == "__main__":
    unittest.main()
