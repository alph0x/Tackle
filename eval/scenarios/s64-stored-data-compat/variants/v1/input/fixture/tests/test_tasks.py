import json
import tempfile
import unittest
from pathlib import Path

from tinytodo.tasks import Task, load_tasks, save_tasks


class TestTaskBasics(unittest.TestCase):
    def test_default_task_title(self):
        task = Task(title="Buy milk")
        self.assertEqual(task.title, "Buy milk")


class TestLoadExamplesFile(unittest.TestCase):
    def test_titles_and_count(self):
        loaded = load_tasks("examples/tasks.json")
        self.assertEqual([t.title for t in loaded], ["Buy milk", "Pay rent", "Water plants"])


class TestSaveAndLoadRoundTrip(unittest.TestCase):
    def test_title_round_trips(self):
        task = Task(title="Water the ferns")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.json"
            save_tasks(path, [task])
            loaded = load_tasks(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].title, "Water the ferns")

    def test_empty_task_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.json"
            path.write_text(json.dumps({"tasks": []}), encoding="utf-8")
            loaded = load_tasks(path)
        self.assertEqual(loaded, [])


if __name__ == "__main__":
    unittest.main()
