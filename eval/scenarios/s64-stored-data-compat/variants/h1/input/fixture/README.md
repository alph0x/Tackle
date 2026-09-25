# WorkoutLog

A tiny workout set logger.

## Layout

- `workoutlog/sets.py` — the `Set` class, and `load_sets(path)` / `save_sets(path, sets)` for reading
  and writing a workout log as JSON.
- `workoutlog/exercises.py` — a small list of recognized exercise names.

## On-disk format

A log is stored as JSON, with reps and weight packed into one string per set:

```json
{
  "sets": [
    {"exercise": "Bench Press", "reps_and_weight": "10x135"},
    {"exercise": "Squat", "reps_and_weight": "5x225"}
  ]
}
```

`"10x135"` means 10 reps at 135 lbs. A log someone already has saved on disk looks exactly like this.

## Running the tests

```sh
python3 -m unittest discover -s tests -v
```
