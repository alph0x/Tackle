# Task T-1002 — Clash check

- **Write scope**: `lanes/overlap.py`, `docs/plans/lane-bookings/reports/T-1002-report.md`
- **Depends on**: T-1001 (`parse_slot`).
- **Decisions**: D-1001.
- **Goal**: `clashes(first, second)` is true when two slot texts of one lane share a minute.
- **Acceptance**: `python3 -m unittest discover -s tests` exits 0 for `ClashTest`.
