"""Display formatting for TinyTodo tasks."""

_MARKS = {"todo": " ", "in_progress": "~", "done": "x"}


def format_task(task) -> str:
    """A one-line display string for `task`, e.g. '[x] Pay rent' or '[ ] Buy milk'."""
    mark = _MARKS.get(task.status, " ")
    return f"[{mark}] {task.title}"
