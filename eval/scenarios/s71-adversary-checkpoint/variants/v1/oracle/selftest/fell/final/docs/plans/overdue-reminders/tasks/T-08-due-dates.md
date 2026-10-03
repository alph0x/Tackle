# Task T-08 — Due-date reader

## Purpose and scope

- **Depends on**: —
- **Traces to**: plan.md §3
- **Write scope**: bookdrop/dates.py, tests/test_dates.py
- **Autonomy**: L2
- **Effort**: medium
- **Budget**: three failed correction-validation cycles
- **Procedure revision**: Tackle 9.0.1
- **Goal**: `parse_due` reads exported due dates and returns None for a blank cell (R2).
- **Non-goals**: mail sending; fines.

## Checks

- **Task check**: `python3 -m unittest tests.test_reminders tests.test_dates`, exit 0.
- **Related regression**: the same command; T-08's cases stay green.

## Recovery

Classify each failure before correcting; keep within the budget.
