import unittest

from lanes.overlap import clashes
from lanes.slots import parse_slot


class ParseSlotTest(unittest.TestCase):
    def test_parse_slot(self):
        self.assertEqual(parse_slot('06:30-07:15'), (390, 435))


class ClashTest(unittest.TestCase):
    def test_overlapping_bookings_clash(self):
        self.assertTrue(clashes('06:30-07:15', '07:00-07:45'))

    def test_back_to_back_bookings_do_not_clash(self):
        self.assertTrue(clashes('06:30-07:15', '07:15-08:00'))

    def test_separate_bookings_do_not_clash(self):
        self.assertFalse(clashes('06:30-07:00', '09:00-09:30'))


if __name__ == '__main__':
    unittest.main()
