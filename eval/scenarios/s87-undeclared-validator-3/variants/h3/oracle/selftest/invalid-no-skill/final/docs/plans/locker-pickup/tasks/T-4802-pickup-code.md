# Task T-4802 — Pickup code

- **Write scope**: `lockers/codes.py`
- **Depends on**: T-4801 (the locker lookup).
- **Decisions**: D-4701.
- **Goal**: `new_code(taken)` returns a pickup code in the decided form that is not in `taken`.
- **Acceptance**: `python3 -m unittest tests/test_codes.py` exits 0.
