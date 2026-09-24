"""Alertline — compact an alert message to its core words."""

STOP = {"is", "not", "after", "again"}


def compact(text):
    words = [w.strip(",.") for w in text.split()]
    return " ".join(w for w in words if w.lower() not in STOP).lower()
