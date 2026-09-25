import unittest
from datetime import date

from roombooking.booking import Booking, days_occupied, occupied_days_in_window, overlaps


class TestOccupiedDaysInWindow(unittest.TestCase):
    """The requested feature: occupied days of a booking that fall within a reporting window."""

    def test_fully_inside_window(self):
        booking = Booking("Falcon", date(2026, 1, 10), date(2026, 1, 12))
        self.assertEqual(occupied_days_in_window(booking, date(2026, 1, 1), date(2026, 1, 31)), 3)

    def test_clips_to_window_end(self):
        booking = Booking("Falcon", date(2026, 1, 10), date(2026, 1, 15))
        self.assertEqual(occupied_days_in_window(booking, date(2026, 1, 1), date(2026, 1, 12)), 3)

    def test_no_overlap_returns_zero(self):
        booking = Booking("Falcon", date(2026, 1, 1), date(2026, 1, 3))
        self.assertEqual(occupied_days_in_window(booking, date(2026, 1, 10), date(2026, 1, 15)), 0)


class TestOccupiedDaysInWindowBoundary(unittest.TestCase):
    """The window is inclusive: a booking that shares only the window's last day still counts."""

    def test_single_day_boundary_overlap_counts_as_one(self):
        booking = Booking("Falcon", date(2026, 1, 10), date(2026, 1, 20))
        self.assertEqual(occupied_days_in_window(booking, date(2026, 1, 5), date(2026, 1, 10)), 1)


class TestExistingBehaviorUnchanged(unittest.TestCase):
    """Regression checks: days_occupied() and overlaps() must still work exactly as before."""

    def test_days_occupied_unchanged(self):
        booking = Booking("Falcon", date(2026, 1, 10), date(2026, 1, 12))
        self.assertEqual(days_occupied(booking), 3)

    def test_overlaps_unchanged(self):
        a = Booking("Falcon", date(2026, 1, 5), date(2026, 1, 10))
        b = Booking("Falcon", date(2026, 1, 8), date(2026, 1, 12))
        self.assertTrue(overlaps(a, b))


if __name__ == "__main__":
    unittest.main()
