# Task T-12 — Window reader

## Purpose and scope

- **Depends on**: —
- **Traces to**: plan.md §3 R1
- **Write scope**: dispatch/windows.py, tests/test_windows.py
- **Autonomy**: L2
- **Effort**: small
- **Budget**: three failed correction-validation cycles
- **Procedure revision**: Tackle 9.0.1
- **Goal**: `parse_window` returns (start, end) minutes for a depot window and None for a blank one.

## Checks

- **Task check**: `python3 -m unittest tests.test_windows`, exit 0.
