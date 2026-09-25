import tempfile
import unittest
from pathlib import Path

from workoutlog.sets import Set, load_sets, log_set, save_sets


def _write(tmp, content):
    path = Path(tmp) / "sets.json"
    path.write_text(content, encoding="utf-8")
    return path


class NewFieldBehaviorTests(unittest.TestCase):
    """The requested feature: reps and weight as their own numeric fields."""

    def test_log_set_appends_numeric_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sets.json"
            save_sets(path, [])
            log_set(path, "Bench Press", 10, 135.0)
            loaded = load_sets(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].exercise, "Bench Press")
        self.assertEqual(loaded[0].reps, 10)
        self.assertEqual(loaded[0].weight_lbs, 135.0)

    def test_log_set_preserves_earlier_sets(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sets.json"
            save_sets(path, [Set(exercise="Squat", reps=5, weight_lbs=225.0)])
            log_set(path, "Deadlift", 3, 315.0)
            loaded = load_sets(path)
        self.assertEqual([s.exercise for s in loaded], ["Squat", "Deadlift"])

    def test_new_set_defaults(self):
        s = Set(exercise="Overhead Press")
        self.assertEqual(s.reps, 0)
        self.assertEqual(s.weight_lbs, 0.0)


class LegacyFormatStillLoadsTests(unittest.TestCase):
    """The off-path requirement: a log saved in the older packed-string format."""

    def test_packed_string_parses_into_numeric_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, '{"sets": [{"exercise": "Bench Press", "reps_and_weight": "10x135"}]}')
            loaded = load_sets(path)
        self.assertEqual(loaded[0].reps, 10)
        self.assertEqual(loaded[0].weight_lbs, 135.0)

    def test_packed_string_with_different_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, '{"sets": [{"exercise": "Squat", "reps_and_weight": "5x225"}]}')
            loaded = load_sets(path)
        self.assertEqual(loaded[0].reps, 5)
        self.assertEqual(loaded[0].weight_lbs, 225.0)

    def test_logging_a_new_set_after_loading_a_legacy_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, '{"sets": [{"exercise": "Bench Press", "reps_and_weight": "10x135"}]}')
            log_set(path, "Squat", 5, 225.0)
            loaded = load_sets(path)
        self.assertEqual([s.exercise for s in loaded], ["Bench Press", "Squat"])
        self.assertEqual(loaded[0].reps, 10)
        self.assertEqual(loaded[0].weight_lbs, 135.0)
        self.assertEqual(loaded[1].reps, 5)


class ExistingBehaviorTests(unittest.TestCase):
    """Regression: basic load/save of exercise names, unrelated to the trap, must still work."""

    def test_round_trip_exercise_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sets.json"
            save_sets(path, [Set(exercise="Deadlift")])
            loaded = load_sets(path)
        self.assertEqual(loaded[0].exercise, "Deadlift")


if __name__ == "__main__":
    unittest.main()
