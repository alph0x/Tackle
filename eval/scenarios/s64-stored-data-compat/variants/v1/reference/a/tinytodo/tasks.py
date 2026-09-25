"""Task storage for TinyTodo.

Tasks are persisted as JSON: {"tasks": [{"title": ..., "status": ...}, ...]}. See README.md for the
on-disk format, and examples/tasks.json for a saved file in the older format this still has to read.
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

    Newer files store "status" directly. Older files (see examples/tasks.json) instead store
    completion as a boolean "done"; that must still come through as "done" or "todo", not silently
    reset to "todo" just because there is no "status" key.
    """
    if "status" in data:
        status = data["status"]
    elif data.get("done"):
        status = "done"
    else:
        status = "todo"
    return Task(title=data["title"], status=status)


def load_tasks(path) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [load_task(item) for item in data.get("tasks", [])]


def save_task(task: Task) -> dict:
    return {"title": task.title, "status": task.status}


def save_tasks(path, tasks) -> None:
    data = {"tasks": [save_task(t) for t in tasks]}
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def set_status(path, title, status) -> None:
    """Set the status of the task titled `title` in the file at `path`, and save it back.

    Raises KeyError if no task with that title exists.
    """
    tasks = load_tasks(path)
    for task in tasks:
        if task.title == title:
            task.status = status
            save_tasks(path, tasks)
            return
    raise KeyError(title)
