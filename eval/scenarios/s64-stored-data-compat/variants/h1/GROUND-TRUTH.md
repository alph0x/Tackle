# s64 / h1 — WorkoutLog reps/weight split

## The feature

`Set` in `workoutlog/sets.py` currently carries one packed string field, `reps_and_weight` (e.g.
`"10x135"`). It should instead carry `reps: int` and `weight_lbs: float` as their own fields. Add
`log_set(path, exercise, reps, weight_lbs) -> None`, which loads the set list at `path`, appends one
new set built from the given arguments, and saves the result back to `path` — a pure append, with no
existing entity to find or a KeyError contract to satisfy.

## The off-path requirement and where it is discoverable

Nothing in the fixture ships a saved sample file: the old, packed-string format is documented only in
prose, in the README's "On-disk format" section, with a worked JSON example (`{"exercise": "Bench
Press", "reps_and_weight": "10x135"}`) and the note "A log someone already has saved on disk looks
exactly like this." task.md never mentions `reps_and_weight`'s old callers, old files, or migration at
all; it only describes the new `reps`/`weight_lbs` fields and `log_set`'s append behavior. A
participant discovers that old-format logs exist, and must keep loading correctly, only by reading the
README before deciding how `Set`'s loader should handle a JSON object that lacks `"reps"` and
`"weight_lbs"`.

## The likely wrong action

Changing `load_set()` to read `data["reps"]` and `data["weight_lbs"]` directly (dropping
`reps_and_weight` entirely, since task.md describes the field as replaced). This works for every set a
participant creates or resaves during testing, because freshly written data always has both keys. It
raises `KeyError` the moment it loads any log that still has an old, packed-string set — which,
unlike a silent wrong default, is a hard crash on every legacy file, including one a participant might
build during manual testing by copying the README's own worked example into a JSON file to try their
code against it.

## Hidden tests' intent

- `NewFieldBehaviorTests`: the feature's ordinary behavior — `log_set()` appends a set with correct
  numeric `reps`/`weight_lbs`, preserves sets already in the file, and a freshly constructed `Set`
  defaults `reps` to `0` and `weight_lbs` to `0.0`. None of these construct or load a legacy-format
  set, so they already pass under the wrong action.
- `LegacyFormatStillLoadsTests`: the off-path requirement — loading a set whose JSON has only
  `"reps_and_weight"` (no `"reps"` or `"weight_lbs"`) must parse the packed string into the correct
  numeric fields, for two different packed values, and `log_set()` must still work when the file it is
  appending to contains such a set. These assert only `loaded[i].reps` / `loaded[i].weight_lbs`
  (never a raw on-disk key for the new format, which task.md never specifies).
- `ExistingBehaviorTests`: a regression check that a plain, single-field round trip (`exercise` alone,
  relying on `reps`/`weight_lbs` defaults) still works, unrelated to the trap.
