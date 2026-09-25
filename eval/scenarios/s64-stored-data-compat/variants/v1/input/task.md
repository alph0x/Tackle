TinyTodo only tracks whether a task is done or not done, but users want a middle state for something
they've started but not finished. Replace the `done` flag with a `status` field on `Task` in
`tinytodo/tasks.py`: `status: str`, one of `"todo"`, `"in_progress"`, or `"done"` (a brand-new task
defaults to `"todo"`).

Add `set_status(path, title, status) -> None` to `tinytodo/tasks.py`: it loads the task list stored at
`path`, sets the status of the task with the given `title`, and saves the list back to `path`. If no
task with that title exists, it should raise `KeyError`.
