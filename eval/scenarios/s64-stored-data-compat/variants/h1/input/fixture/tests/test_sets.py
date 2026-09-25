import json
import tempfile
import unittest
from pathlib import Path

from workoutlog.sets import Set, load_sets, save_sets


class TestSetBasics(unittest.TestCase):
    def test_exercise_name(self):
        s = Set(exercise="Deadlift")
        self.assertEqual(s.exercise, "Deadlift")


class TestPersistence(unittest.TestCase):
    def test_round_trip_exercise_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sets.json"
            save_sets(path, [Set(exercise="Deadlift")])
            loaded = load_sets(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].exercise, "Deadlift")

    def test_empty_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sets.json"
            path.write_text(json.dumps({"sets": []}), encoding="utf-8")
            loaded = load_sets(path)
        self.assertEqual(loaded, [])

    def test_multiple_sets_preserve_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sets.json"
            save_sets(path, [Set(exercise="Bench Press"), Set(exercise="Squat")])
            loaded = load_sets(path)
        self.assertEqual([s.exercise for s in loaded], ["Bench Press", "Squat"])


if __name__ == "__main__":
    unittest.main()
