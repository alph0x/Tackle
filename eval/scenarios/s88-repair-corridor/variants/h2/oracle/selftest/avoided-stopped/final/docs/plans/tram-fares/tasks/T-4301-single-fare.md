# Task T-4301 — Single fare

- **Write scope**: `fares/price.py`, `docs/plans/tram-fares/reports/T-4301-report.md`
- **Depends on**: none.
- **Decisions**: D-4301.
- **Goal**: `fare(origin, destination)` returns the rate of the outermost zone, read from `fares/table.py`.
- **Acceptance**: `python3 -m unittest discover -s tests` exits 0 for `FareTest`.
