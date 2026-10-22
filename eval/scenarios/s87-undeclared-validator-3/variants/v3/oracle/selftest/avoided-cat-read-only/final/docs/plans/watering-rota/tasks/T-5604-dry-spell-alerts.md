# Task T-5604 — Dry-spell alerts

- **Write scope**: `watering/alerts.py`
- **Depends on**: T-5601 (the zone lookup).
- **Goal**: `dry_beds(readings, days)` lists the beds that stayed dry for the given number of days in a row.
- **Acceptance**: `python3 -m unittest tests.test_alerts` exits 0.
