# Task T-4803 — Hold period

- **Write scope**: `lockers/hold.py`, `tests/test_hold.py`
- **Depends on**: T-4801 (the locker lookup).
- **Decisions**: D-4702.
- **Goal**: `expires_on(delivered)` returns the last day a parcel can be collected, as decided.
- **Acceptance**: `python3 -m unittest tests/test_hold.py` exits 0.
