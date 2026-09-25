"""Meeting room bookings.

A Booking's date range is inclusive on both ends: a booking from 2026-01-10 to 2026-01-12 occupies
the 10th, 11th and 12th -- three days, not two. days_occupied() below is the reference
implementation of that rule: it is (end - start).days + 1, not just (end - start).days. overlaps()
below applies the same inclusive convention to comparing two ranges: a shared boundary day (one
booking's end equal to another's start) counts as a real overlap, not a gap.
"""
from dataclasses import dataclass
from datetime import date


@dataclass
class Booking:
    room: str
    start: date
    end: date


def days_occupied(booking: Booking) -> int:
    """Number of days `booking` occupies, both ends inclusive."""
    return (booking.end - booking.start).days + 1


def overlaps(a: Booking, b: Booking) -> bool:
    """True if `a` and `b` are in the same room and their inclusive ranges share a day."""
    return a.room == b.room and a.start <= b.end and b.start <= a.end


def occupied_days_in_window(booking: Booking, window_start: date, window_end: date) -> int:
    """Days of `booking` that fall within [window_start, window_end], clipped to the window.

    Both the booking's range and the window are inclusive on both ends, so a booking and a window
    that share only a single boundary day still count as 1 occupied day, not 0 -- the same inclusive
    convention as days_occupied() and overlaps() above.
    """
    clipped_start = max(booking.start, window_start)
    clipped_end = min(booking.end, window_end)
    if clipped_start > clipped_end:
        return 0
    return (clipped_end - clipped_start).days + 1
