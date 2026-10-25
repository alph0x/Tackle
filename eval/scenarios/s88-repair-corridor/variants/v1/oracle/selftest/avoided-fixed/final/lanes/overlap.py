"""Clash check for two bookings of the same lane."""

from lanes.slots import parse_slot


def clashes(first, second):
    """True when the two slot texts share any minute of the lane; a slot ends just before its end minute."""
    a_start, a_end = parse_slot(first)
    b_start, b_end = parse_slot(second)
    return a_start < b_end and b_start < a_end
