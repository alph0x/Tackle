import unittest

from lanes.slots import to_minutes


class T(unittest.TestCase):
    def test_colon(self):
        self.assertEqual(to_minutes('07:15'), 435)
