# Task T-3201 — Logger line reader

- **Write scope**: `gardenmeter/readings.py`, `docs/plans/garden-water/reports/T-3201-report.md`
- **Depends on**: none.
- **Decisions**: D-3201.
- **Goal**: `read_line(line)` returns the day and the reading of one logger line.
- **Acceptance**: `python3 -m unittest discover -s tests` exits 0 for `ReadLineTest`.
