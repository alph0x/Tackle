"""Summarize parcel rows for the dispatch desk."""
from pkg.loader import read_rows


def parcel_count(text):
    rows = read_rows(text)
    return rows['count']
