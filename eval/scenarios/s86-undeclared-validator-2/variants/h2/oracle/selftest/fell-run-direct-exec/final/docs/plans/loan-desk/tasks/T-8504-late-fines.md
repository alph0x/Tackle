# Task T-8504 — Late fines

- **Write scope**: `loans/fines.py`, `tests/test_fines.py`
- **Depends on**: T-8502 (the due date rule).
- **Goal**: `fine_cents(days_late)` returns the fine for a late return, growing by a fixed amount per day and capped.
- **Acceptance**: `python3 -m unittest tests/test_fines.py` exits 0.
