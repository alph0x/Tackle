import tempfile
import unittest
from pathlib import Path

from tinytodo.formatting import format_task
from tinytodo.tasks import Task, load_tasks, save_tasks, set_status


class TestLoadExistingFileMigratesDone(unittest.TestCase):
    """examples/tasks.json was saved with the old "done" boolean; it must still load correctly."""

    def test_previously_done_task_has_status_done(self):
        loaded = load_tasks("examples/tasks.json")
        by_title = {t.title: t for t in loaded}
        self.assertEqual(by_title["Pay rent"].status, "done")

    def test_previously_not_done_task_has_status_todo(self):
        loaded = load_tasks("examples/tasks.json")
        by_title = {t.title: t for t in loaded}
        self.assertEqual(by_title["Buy milk"].status, "todo")
        self.assertEqual(by_title["Water plants"].status, "todo")

    def test_titles_and_count_preserved(self):
        loaded = load_tasks("examples/tasks.json")
        self.assertEqual([t.title for t in loaded], ["Buy milk", "Pay rent", "Water plants"])


class TestSetStatus(unittest.TestCase):
    """The requested feature: a three-state status, defaulting to "todo", settable by title."""

    def _write(self, tmp, tasks):
        path = Path(tmp) / "tasks.json"
        save_tasks(path, tasks)
        return path

    def test_new_task_defaults_to_todo(self):
        self.assertEqual(Task(title="Feed the cat").status, "todo")

    def test_round_trips_through_set_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [Task(title="Feed the cat")])
            set_status(path, "Feed the cat", "in_progress")
            loaded = load_tasks(path)
        self.assertEqual(loaded[0].status, "in_progress")

    def test_missing_title_raises_key_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [Task(title="Feed the cat")])
            with self.assertRaises(KeyError):
                set_status(path, "Nonexistent", "done")


class TestSaveAndLoadNewFormat(unittest.TestCase):
    """Regression: saving and loading in the new format still works for freshly written data."""

    def test_status_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.json"
            save_tasks(path, [Task(title="Renew license", status="in_progress")])
            loaded = load_tasks(path)
        self.assertEqual(loaded[0].status, "in_progress")


class TestFormatTaskReflectsStatus(unittest.TestCase):
    """Regression: format_task() (tinytodo/formatting.py) must still render a task correctly."""

    def test_format_task_shows_each_status(self):
        for status in ("todo", "in_progress", "done"):
            format_task(Task(title="Buy milk", status=status))  # must not raise for any status
        # done/todo keep the marker format_task already produced for done/not-done before this change.
        self.assertEqual(format_task(Task(title="Buy milk", status="todo")), "[ ] Buy milk")
        self.assertEqual(format_task(Task(title="Pay rent", status="done")), "[x] Pay rent")
        # in_progress has no specified marker; only its title needs to appear in the line.
        self.assertIn("Renew license",
                       format_task(Task(title="Renew license", status="in_progress")))


if __name__ == "__main__":
    unittest.main()
