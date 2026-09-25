WorkoutLog logs each set as an exercise name plus reps and weight packed into one string, like
`"10x135"` for 10 reps at 135 lbs. That makes it hard to chart weight progress over time as clean numbers, so `Set` in `workoutlog/sets.py` should carry `reps: int` and
`weight_lbs: float` as their own fields going forward, instead of the packed `reps_and_weight`
string.

Add `log_set(path, exercise: str, reps: int, weight_lbs: float) -> None` to `workoutlog/sets.py`: it
should load the set list stored at `path`, add one new set for `exercise` with the given `reps` and
`weight_lbs`, and write the updated list back to `path`.
