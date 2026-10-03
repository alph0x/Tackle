"""Per-zone mean temperature (T-04)."""
from collections import OrderedDict

from rollup.readings import read_readings

SEPARATOR = ";"
HEADER = ("zone", "avg_c")


def zone_means(path):
    totals = OrderedDict()
    for reading in read_readings(path):
        count, total = totals.get(reading.zone, (0, 0.0))
        totals[reading.zone] = (count + 1, total + reading.temp_c)
    return [(zone, total / count) for zone, (count, total) in totals.items()]


def render(means):
    lines = [SEPARATOR.join(HEADER)]
    lines.extend("%s%s%.2f" % (zone, SEPARATOR, mean) for zone, mean in means)
    return "\n".join(lines)
