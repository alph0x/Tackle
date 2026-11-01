"""Produce the dispatch desk's parcel summary."""
from pkg.loader import read_rows


def first_parcel(text):
    rows = read_rows(text)
    return rows[0] if rows else None
