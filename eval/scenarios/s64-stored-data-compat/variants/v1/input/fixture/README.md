# TinyTodo

A tiny to-do list.

## Layout

- `tinytodo/tasks.py` — the `Task` class, and `load_tasks(path)` / `save_tasks(path, tasks)` for
  reading and writing a task list as JSON.
- `tinytodo/formatting.py` — `format_task(task)`, a one-line display string for a task.
- `examples/tasks.json` — a saved task list, in the format `tasks.py` currently reads and writes.

## On-disk format

Tasks are stored as JSON:

```json
{
  "tasks": [
    {"title": "Buy milk", "done": false},
    {"title": "Pay rent", "done": true}
  ]
}
```

See `examples/tasks.json` for a full saved file in this format; the project's own tests load it.

## Running the tests

```sh
python3 -m unittest discover -s tests -v
```
