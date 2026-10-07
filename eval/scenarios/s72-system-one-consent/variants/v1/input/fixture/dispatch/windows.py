"""Delivery windows as the depot terminal writes them: 'HH:MM-HH:MM'."""


def parse_window(text):
    """Return (start, end) in minutes after midnight, or None for a blank or unreadable window."""
    text = (text or '').strip()
    if '-' not in text:
        return None
    start, _, end = text.partition('-')
    try:
        return _minutes(start), _minutes(end)
    except ValueError:
        return None


def _minutes(clock):
    hours, _, minutes = clock.strip().partition(':')
    return int(hours) * 60 + int(minutes)
