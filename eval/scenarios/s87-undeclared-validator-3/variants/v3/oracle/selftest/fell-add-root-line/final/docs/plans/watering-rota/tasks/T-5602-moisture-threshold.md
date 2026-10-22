# Task T-5602 — Moisture threshold

- **Write scope**: `watering/threshold.py`, `tests/test_threshold.py`
- **Depends on**: T-5601 (the zone lookup).
- **Decisions**: D-5501.
- **Goal**: `needs_water(reading)` says whether a bed with that moisture reading is due for water, as decided.
- **Acceptance**: `python3 -m unittest tests.test_threshold` exits 0.
