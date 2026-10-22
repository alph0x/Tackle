# Task T-7403 — Reminder text

- **Write scope**: `reminders/template.py`
- **Depends on**: T-7401 (the due date).
- **Decisions**: D-7302.
- **Goal**: `reminder_text(name, amount)` returns the plain-text body of a reminder.
- **Acceptance**: `python3 -m unittest tests.test_template` exits 0.
