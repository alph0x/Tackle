import unittest
from datetime import date

from roombooking.booking import Booking, days_occupied, overlaps


class TestDaysOccupied(unittest.TestCase):
    def test_single_day(self):
        booking = Booking("Falcon", date(2026, 1, 10), date(2026, 1, 10))
        self.assertEqual(days_occupied(booking), 1)

    def test_multiple_days(self):
        booking = Booking("Falcon", date(2026, 1, 10), date(2026, 1, 12))
        self.assertEqual(days_occupied(booking), 3)


class TestOverlaps(unittest.TestCase):
    def test_different_rooms_never_overlap(self):
        a = Booking("Falcon", date(2026, 1, 10), date(2026, 1, 12))
        b = Booking("Osprey", date(2026, 1, 10), date(2026, 1, 12))
        self.assertFalse(overlaps(a, b))

    def test_shared_boundary_day_overlaps(self):
        a = Booking("Falcon", date(2026, 1, 10), date(2026, 1, 12))
        b = Booking("Falcon", date(2026, 1, 12), date(2026, 1, 14))
        self.assertTrue(overlaps(a, b))

    def test_true_gap_does_not_overlap(self):
        a = Booking("Falcon", date(2026, 1, 10), date(2026, 1, 11))
        b = Booking("Falcon", date(2026, 1, 12), date(2026, 1, 13))
        self.assertFalse(overlaps(a, b))


if __name__ == "__main__":
    unittest.main()
