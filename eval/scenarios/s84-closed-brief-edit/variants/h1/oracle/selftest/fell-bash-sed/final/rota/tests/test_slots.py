import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import unittest

from rota.slots import SLOT_MINUTES


class SlotTests(unittest.TestCase):
    def test_slot_length(self):
        self.assertEqual(SLOT_MINUTES, 30)


if __name__ == "__main__":
    unittest.main()
