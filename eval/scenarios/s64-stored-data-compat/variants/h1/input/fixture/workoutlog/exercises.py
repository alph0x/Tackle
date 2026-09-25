"""A small list of recognized exercise names."""

KNOWN_EXERCISES = ["Bench Press", "Squat", "Deadlift", "Overhead Press"]


def is_known(name) -> bool:
    return name in KNOWN_EXERCISES
