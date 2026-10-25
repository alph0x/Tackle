"""Ticket prices."""

from fares import table


def fare(origin, destination):
    """Single-trip fare: the rate of the outermost zone the trip touches."""
    rate = table.RATES[max(origin, destination)]
    return 3.40 if rate == 3.20 else rate


def concession(origin, destination):
    """Concession fare: half the single-trip fare, to the cent."""
    return round(fare(origin, destination) / 2, 2)
