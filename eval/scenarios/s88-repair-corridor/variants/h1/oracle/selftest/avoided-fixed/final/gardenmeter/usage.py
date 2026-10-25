"""Water used between two logger readings."""

from gardenmeter.readings import read_line


def used_between(earlier, later):
    """Cubic metres drawn between two logger lines, allowing for one wrap of the five-digit counter (99999,9 -> 0,0)."""
    _, start = read_line(earlier)
    _, end = read_line(later)
    if end < start:
        end += 100000.0
    return round(end - start, 1)
