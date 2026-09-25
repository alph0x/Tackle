"""Set storage for WorkoutLog.

Sets are persisted as JSON: {"sets": [{"exercise": ..., "reps": ..., "weight_lbs": ...}, ...]}. See
README.md for a worked example of the older, single-string format this still has to read.
"""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Set:
    exercise: str
    reps: int = 0
    weight_lbs: float = 0.0


def load_set(data: dict) -> Set:
    """Build a Set from one JSON object.

    Newer files store "reps" and "weight_lbs" directly. Older files instead pack both into one
    "reps_and_weight" string like "10x135" (see README.md); that must still parse into the same reps
    and weight_lbs a newer file would have stored, not raise and not silently zero them out.
    """
    if "reps" in data and "weight_lbs" in data:
        return Set(exercise=data["exercise"], reps=data["reps"], weight_lbs=data["weight_lbs"])
    reps_text, _, weight_text = data["reps_and_weight"].partition("x")
    return Set(exercise=data["exercise"], reps=int(reps_text), weight_lbs=float(weight_text))


def load_sets(path) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [load_set(item) for item in data.get("sets", [])]


def save_set(s: Set) -> dict:
    return {"exercise": s.exercise, "reps": s.reps, "weight_lbs": s.weight_lbs}


def save_sets(path, sets) -> None:
    data = {"sets": [save_set(s) for s in sets]}
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def log_set(path, exercise, reps, weight_lbs) -> None:
    """Append one new set to the log stored at `path`, and save the result."""
    sets = load_sets(path)
    sets.append(Set(exercise=exercise, reps=reps, weight_lbs=weight_lbs))
    save_sets(path, sets)
