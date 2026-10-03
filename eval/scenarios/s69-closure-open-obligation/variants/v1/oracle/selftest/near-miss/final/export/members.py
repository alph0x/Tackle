"""Read the membership file (T-01)."""
import json
from pathlib import Path


def read_members(path):
    """Return the members as a list of dicts, in file order."""
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    return list(data["members"])
