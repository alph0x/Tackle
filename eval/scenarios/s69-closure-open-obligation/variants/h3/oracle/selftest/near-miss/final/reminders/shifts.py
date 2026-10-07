"""Read the weekly rota (T-01)."""
import csv
from pathlib import Path

FIELDS = ("shift_id", "volunteer", "email", "date", "start", "role")


def read_shifts(path):
    """Return the shifts as a list of dicts, in rota order; a missing column is an error."""
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in FIELDS if name not in (reader.fieldnames or ())]
        if missing:
            raise ValueError("rota lacks column(s): %s" % ", ".join(missing))
        return [{name: row[name] for name in FIELDS} for row in reader]
