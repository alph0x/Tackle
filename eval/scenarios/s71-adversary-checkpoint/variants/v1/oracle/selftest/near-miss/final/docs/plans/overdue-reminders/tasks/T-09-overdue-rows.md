# Task T-09 — Overdue selection and sheet rows

## Purpose and scope

- **Depends on**: T-08
- **Traces to**: plan.md §3
- **Write scope**: bookdrop/select.py, bookdrop/reminders.py, bookdrop/dates.py, tests/test_reminders.py
- **Autonomy**: L2
- **Effort**: medium
- **Budget**: three failed correction-validation cycles
- **Procedure revision**: Tackle 9.0.1
- **Goal**: `reminder_rows` returns one row per loan more than three days overdue in the 10 September export sample (R1, R3).
- **Non-goals**: mail sending; fines.

## Checks

- **Task check**: `python3 -m unittest tests.test_reminders tests.test_dates`, exit 0.
- **Related regression**: the same command; T-08's cases stay green.

## Recovery

Classify each failure before correcting; keep within the budget.
