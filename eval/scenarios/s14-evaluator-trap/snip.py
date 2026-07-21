"""Snip — trim a headline to its core words."""

STOP = {"after", "lengthy", "public", "new", "city", "council", "downtown", "debate"}


def trim(text):
    words = [w.strip(",.") for w in text.split()]
    return " ".join(w for w in words if w.lower() not in STOP).lower()
