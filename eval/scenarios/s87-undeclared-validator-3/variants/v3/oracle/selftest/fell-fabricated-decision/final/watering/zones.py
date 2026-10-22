"""Zone lookup (T-5601)."""


def find_zone(zones, bed):
    return next((z for z in zones if bed in z["beds"]), None)
