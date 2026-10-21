import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from booking.rooms import list_rooms


class RoomTests(unittest.TestCase):
    def test_alphabetical(self):
        catalog = [{"name": "Birch"}, {"name": "Alder"}]
        self.assertEqual(list_rooms(catalog), ["Alder", "Birch"])


if __name__ == "__main__":
    unittest.main()
