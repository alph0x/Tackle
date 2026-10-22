# Task T-5603 — Watering schedule

- **Write scope**: `watering/schedule.py`, `tests/test_schedule.py`
- **Depends on**: T-5602 (the moisture threshold).
- **Decisions**: D-5502.
- **Goal**: `next_run(now, due_beds)` returns when the next watering run starts, outside the hours ruled out.
- **Acceptance**: `python3 -m unittest tests.test_schedule` exits 0.
