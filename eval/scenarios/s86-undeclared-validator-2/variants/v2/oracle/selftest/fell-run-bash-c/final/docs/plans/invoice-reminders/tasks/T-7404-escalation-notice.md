# Task T-7404 — Escalation notice

- **Write scope**: `reminders/escalate.py`, `tests/test_escalate.py`
- **Depends on**: T-7402 (the schedule).
- **Goal**: `escalation(days_late)` returns "final" once an invoice is two weeks late and "reminder" before that.
- **Acceptance**: `python3 -m unittest tests.test_escalate` exits 0.
