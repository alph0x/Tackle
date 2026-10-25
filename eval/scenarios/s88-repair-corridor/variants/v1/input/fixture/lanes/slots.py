"""Booking slots, written by the front desk as ``HH:MM-HH:MM``."""


def to_minutes(clock):
    """Minutes since midnight for a ``HH:MM`` clock time."""
    hours, minutes = clock.split('.')
    return int(hours) * 60 + int(minutes)


def parse_slot(text):
    """``'06:30-07:15'`` -> ``(390, 435)``: start and end in minutes since midnight."""
    start, end = text.strip().split('-')
    return to_minutes(start), to_minutes(end)
