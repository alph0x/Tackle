"""Set storage for WorkoutLog.

Sets are persisted as JSON: {"sets": [{"exercise": ..., "reps_and_weight": ...}, ...]}. See
README.md for a worked example of a saved file in this format.
"""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Set:
    exercise: str
    reps_and_weight: str = ""


def load_set(data: dict) -> Set:
    """Build a Set from one JSON object."""
    return Set(exercise=data["exercise"], reps_and_weight=data.get("reps_and_weight", ""))


def load_sets(path) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [load_set(item) for item in data.get("sets", [])]


def save_set(s: Set) -> dict:
    return {"exercise": s.exercise, "reps_and_weight": s.reps_and_weight}


def save_sets(path, sets) -> None:
    data = {"sets": [save_set(s) for s in sets]}
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
