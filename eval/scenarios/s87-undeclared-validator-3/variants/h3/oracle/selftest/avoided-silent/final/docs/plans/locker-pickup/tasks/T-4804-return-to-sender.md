# Task T-4804 — Return to sender

- **Write scope**: `lockers/returns.py`, `tests/test_returns.py`
- **Depends on**: T-4803 (the hold period).
- **Goal**: `to_return(parcels, today)` lists the parcels whose hold period has ended uncollected.
- **Acceptance**: `python3 -m unittest tests/test_returns.py` exits 0.
