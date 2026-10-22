# Task T-7402 — Reminder schedule

- **Write scope**: `reminders/schedule.py`, `tests/test_schedule.py`
- **Depends on**: T-7401 (the due date).
- **Decisions**: D-7301.
- **Goal**: `reminder_day(due)` returns the day a reminder goes out, as decided.
- **Acceptance**: `python3 -m unittest tests.test_schedule` exits 0.
