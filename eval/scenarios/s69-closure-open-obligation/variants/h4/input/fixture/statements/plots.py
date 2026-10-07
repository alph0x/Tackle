"""Read the plot register (T-01)."""
import csv
from pathlib import Path


def read_plots(path):
    """Return the plots as a list of dicts, in register order."""
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
