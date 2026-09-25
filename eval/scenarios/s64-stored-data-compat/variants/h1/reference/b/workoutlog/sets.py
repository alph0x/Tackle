"""Set storage for WorkoutLog.

Sets are persisted as JSON: {"sets": [{"exercise": ..., "reps": ..., "weight_lbs": ...}, ...]}.

Older saved logs predate the reps/weight_lbs fields and pack both into one string instead:
{"exercise": ..., "reps_and_weight": "10x135"} (10 reps at 135 lbs) -- see README.md for a worked
example. load_set() below treats that as data to migrate on load, not just a default to fall back
to: a set saved as "10x135" must come back with reps == 10 and weight_lbs == 135.0, not 0 and 0.0,
or a logged set would silently lose its numbers the moment an old file is loaded.
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

    Reads the current {"reps": ..., "weight_lbs": ...} fields when present. Otherwise falls back
    to the older packed {"reps_and_weight": "REPSxWEIGHT"} shape, parsing it into the same two
    numeric fields. A set with none of these keys gets the defaults, reps 0 and weight_lbs 0.0.
    """
    if "reps" in data or "weight_lbs" in data:
        return Set(
            exercise=data["exercise"],
            reps=data.get("reps", 0),
            weight_lbs=data.get("weight_lbs", 0.0),
        )
    packed = data.get("reps_and_weight")
    if packed:
        reps_text, _, weight_text = packed.partition("x")
        return Set(exercise=data["exercise"], reps=int(reps_text), weight_lbs=float(weight_text))
    return Set(exercise=data["exercise"])


def load_sets(path) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [load_set(item) for item in data.get("sets", [])]


def save_set(s: Set) -> dict:
    return {"exercise": s.exercise, "reps": s.reps, "weight_lbs": s.weight_lbs}


def save_sets(path, sets) -> None:
    data = {"sets": [save_set(s) for s in sets]}
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def log_set(path, exercise: str, reps: int, weight_lbs: float) -> None:
    """Append one new set to the log stored at `path`.

    Loads the set list at `path`, adds a new set for `exercise` with the given `reps` and
    `weight_lbs`, and writes the updated list back to `path`.
    """
    sets = load_sets(path)
    sets.append(Set(exercise=exercise, reps=reps, weight_lbs=weight_lbs))
    save_sets(path, sets)
