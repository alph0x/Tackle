"""Logger export reader: `zone,taken_at,temp_c`, one reading per row."""
import csv
from dataclasses import dataclass


@dataclass(frozen=True)
class Reading:
    zone: str
    taken_at: str
    temp_c: float


def read_readings(path):
    """Yield one Reading per data row of a logger export."""
    with open(path, newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            yield Reading(raw["zone"], raw["taken_at"], float(raw["temp_c"]))
