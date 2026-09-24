"""Shrink — compress a ticket subject to its core words."""

STOP = {"is", "not", "to", "the"}


def compress(text):
    words = [w.strip(",.") for w in text.split()]
    return " ".join(w for w in words if w.lower() not in STOP).lower()
