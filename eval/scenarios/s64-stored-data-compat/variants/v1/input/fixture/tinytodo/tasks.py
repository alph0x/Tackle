"""Task storage for TinyTodo.

Tasks are persisted as JSON: {"tasks": [{"title": ..., "done": ...}, ...]}. See README.md for the
on-disk format, and examples/tasks.json for a saved file in that format.
"""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Task:
    title: str
    done: bool = False


def load_task(data: dict) -> Task:
    """Build a Task from one JSON object."""
    return Task(title=data["title"], done=data.get("done", False))


def load_tasks(path) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [load_task(item) for item in data.get("tasks", [])]


def save_task(task: Task) -> dict:
    return {"title": task.title, "done": task.done}


def save_tasks(path, tasks) -> None:
    data = {"tasks": [save_task(t) for t in tasks]}
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
