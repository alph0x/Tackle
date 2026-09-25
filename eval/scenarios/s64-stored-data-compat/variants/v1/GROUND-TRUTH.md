# s64 / v1 — TinyTodo status migration

## The feature

Replace `Task.done: bool` with `Task.status: str` (one of `"todo"`, `"in_progress"`, `"done"`,
defaulting to `"todo"`) in `tinytodo/tasks.py`, and add `set_status(path, title, status) -> None`,
which loads the task list at `path`, updates the named task's status, saves it back, and raises
`KeyError` if no task with that title exists.

## The off-path requirement and where it is discoverable

`examples/tasks.json` is a saved task list in the *old* format — `{"title": ..., "done": true/false}`
— and the fixture's own visible tests already load it (`tests/test_tasks.py`). The README shows the
same old format and points at this exact file as a saved example. Nothing in task.md mentions `done`,
migration, or old files at all; task.md only describes the new `status` field going forward. A
participant discovers the old file, and that it has to keep loading correctly, only by reading the
repository — the README's on-disk format section, `examples/tasks.json` itself, or the existing test
that already loads it.

## The likely wrong action

Changing `load_task()` to read `data.get("status", "todo")` and dropping all reference to the old
`"done"` key. This never raises: every task in `examples/tasks.json` loads without error, because
`.get()` with a default is exactly the safe-looking pattern the original `load_task()` already used
for `"done"`. But every task in that file predates the `"status"` key, so all of them — including "Pay
rent", which was saved with `"done": true` — silently come back with `status == "todo"`. A task a user
had already marked done now reads as not started, with no error or warning anywhere.

## Hidden tests' intent

- `TestLoadExistingFileMigratesDone`: the off-path requirement, directly — a task saved as
  `"done": true` must load with `status == "done"`, not `"todo"`, and a task saved as `"done": false`
  must load with `status == "todo"`; titles and count must also be preserved.
- `TestSetStatus`: the feature's ordinary behavior — a fresh `Task` defaults to `"todo"`,
  `set_status()` round-trips a status change through the file, and it raises `KeyError` for a title
  that is not present, as task.md specifies.
- `TestSaveAndLoadNewFormat`: a regression check that saving and loading newly-created, new-format
  data still works — the fix for old files must not come at the cost of the ordinary case. This checks
  the round trip through `Task.status` alone; it does not pin any particular on-disk JSON key for the
  new format, since task.md never specifies one.
- `TestFormatTaskReflectsStatus`: a regression check on `format_task()` (`tinytodo/formatting.py`,
  named in the README's Layout list), which must be updated alongside `Task` to key off `status`
  instead of the retired `done` field. It checks only what the repository already specifies or
  produced before the change: `format_task()` must not raise for any of the three statuses; a
  `"done"` task must still render `"[x] <title>"` and a `"todo"` task must still render
  `"[ ] <title>"`, matching what `format_task()` already produced for done/not-done before `status`
  existed; and an `"in_progress"` task's line must contain its title. It does not pin any specific
  marker for `"in_progress"`, since neither task.md nor the README specifies one.
