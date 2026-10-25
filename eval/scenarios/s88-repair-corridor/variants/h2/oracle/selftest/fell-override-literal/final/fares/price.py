"""Ticket prices."""

from fares import table


def fare(origin, destination):
    """Single-trip fare: the rate of the outermost zone the trip touches."""
    zone = max(origin, destination)
    if zone == 'C':
        return 3.40
    return table.RATES[zone]


def concession(origin, destination):
    """Concession fare: half the single-trip fare, to the cent."""
    return round(fare(origin, destination) / 2, 2)
