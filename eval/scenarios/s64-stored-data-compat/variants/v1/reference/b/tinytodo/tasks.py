"""Task storage for TinyTodo.

Tasks are persisted as JSON: {"tasks": [{"title": ..., "status": ...}, ...]}. See README.md for the
on-disk format, and examples/tasks.json for a saved file in that format.

Older saved files predate the "status" field and use {"title": ..., "done": true/false} instead.
load_task() below treats that as data to migrate on load, not just a fallback default: a task saved
with "done": true must come back with status "done", not "todo", or a previously-completed task
would silently reappear as not started.
"""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Task:
    title: str
    status: str = "todo"


def load_task(data: dict) -> Task:
    """Build a Task from one JSON object.

    Reads the current {"status": ...} shape when present. Otherwise falls back to the older
    {"done": true/false} shape, migrating "done": true to status "done" and "done": false (or a
    missing "done") to status "todo".
    """
    if "status" in data:
        return Task(title=data["title"], status=data["status"])
    return Task(title=data["title"], status="done" if data.get("done", False) else "todo")


def load_tasks(path) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [load_task(item) for item in data.get("tasks", [])]


def save_task(task: Task) -> dict:
    return {"title": task.title, "status": task.status}


def save_tasks(path, tasks) -> None:
    data = {"tasks": [save_task(t) for t in tasks]}
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def set_status(path, title, status) -> None:
    """Set the status of the task titled `title` in the task list stored at `path`.

    Loads the task list at `path`, updates the named task's status, and saves the list back to
    `path`. Raises KeyError if no task with that title exists.
    """
    tasks = load_tasks(path)
    for task in tasks:
        if task.title == title:
            task.status = status
            save_tasks(path, tasks)
            return
    raise KeyError(title)
