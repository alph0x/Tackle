"""Read parcel rows for the report."""


def read_rows(text):
    if not text.strip():
        return []
    return [line.split(',') for line in text.splitlines()]
