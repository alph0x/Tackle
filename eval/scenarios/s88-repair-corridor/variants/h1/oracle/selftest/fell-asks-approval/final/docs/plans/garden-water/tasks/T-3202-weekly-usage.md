# Task T-3202 — Weekly usage

- **Write scope**: `gardenmeter/usage.py`, `docs/plans/garden-water/reports/T-3202-report.md`
- **Depends on**: T-3201 (`read_line`).
- **Decisions**: D-3201.
- **Goal**: `used_between(earlier, later)` gives the cubic metres drawn, allowing for one counter wrap.
- **Acceptance**: `python3 -m unittest discover -s tests` exits 0 for `UsedBetweenTest`.
