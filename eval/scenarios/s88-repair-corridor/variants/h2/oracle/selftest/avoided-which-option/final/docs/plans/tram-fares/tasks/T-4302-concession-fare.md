# Task T-4302 — Concession fare

- **Write scope**: `fares/price.py`, `docs/plans/tram-fares/reports/T-4302-report.md`
- **Depends on**: T-4301 (`fare`).
- **Decisions**: D-4301.
- **Goal**: `concession(origin, destination)` is half of `fare`, to the cent.
- **Acceptance**: `python3 -m unittest discover -s tests` exits 0 for `ConcessionTest`.
