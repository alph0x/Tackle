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
    """Number of `booking`'s occupied days that fall within the inclusive [window_start, window_end].

    Clips the booking's inclusive range to the window, then applies the same inclusive-both-ends
    convention as days_occupied() and overlaps(): a booking and window that share exactly one
    boundary day are a genuine 1-day overlap, not 0. A booking that does not overlap the window at
    all returns 0.
    """
    clipped_start = max(booking.start, window_start)
    clipped_end = min(booking.end, window_end)
    if clipped_start > clipped_end:
        return 0
    return (clipped_end - clipped_start).days + 1
