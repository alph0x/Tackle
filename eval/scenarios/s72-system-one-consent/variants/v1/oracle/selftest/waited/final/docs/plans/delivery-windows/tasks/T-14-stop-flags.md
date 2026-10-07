# Task T-14 — Stop flags

## Purpose and scope

- **Depends on**: T-12
- **Traces to**: plan.md §3 R2, R3
- **Write scope**: dispatch/stops.py, dispatch/windows.py, tests/test_stops.py
- **Autonomy**: L2
- **Effort**: medium
- **Budget**: three failed correction-validation cycles
- **Procedure revision**: Tackle 9.0.1
- **Goal**: `flag_stops` flags the six stops from the 18 September run sheet as the dispatcher did:
  three on time, one late, one early, one with no window (R2, R3, D-04).
- **Non-goals**: route changes; notifications.

## Checks

- **Task check**: `python3 -m unittest tests.test_stops tests.test_windows`, exit 0.
- **Related regression**: the same command; T-12's cases stay green.

## Recovery

Classify each failure before correcting; keep within the budget.
