"""Display formatting for TinyTodo tasks."""


def format_task(task) -> str:
    """A one-line display string for `task`, e.g. '[x] Pay rent' or '[ ] Buy milk'."""
    mark = "x" if task.status == "done" else " "
    return f"[{mark}] {task.title}"
