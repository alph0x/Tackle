"""Summary line for one scanner export (T-03)."""
from manifest.rows import read_rows


def count_parcels(path):
    return sum(1 for _ in read_rows(path))


def render(count):
    return "Total: %d parcels" % count
