"""One line per day from the standpipe logger: ``YYYY-MM-DD;<cubic metres>``.

Since the logger firmware update the value carries a decimal comma, e.g. ``2026-10-01;12,5``.
"""


def read_line(line):
    """``'2026-10-01;12,5'`` -> ``('2026-10-01', 12.5)``."""
    day, value = line.strip().split(';')
    return day, float(value.replace(',', '.'))
