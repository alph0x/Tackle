# Task T-6102 — Overlap check

- **Write scope**: `booking/overlap.py`, `tests/test_overlap.py`
- **Depends on**: T-6101 (the room list).
- **Decisions**: D-6002.
- **Goal**: `clashes(first, second)` says whether two bookings of the same room overlap, on half-open intervals.
- **Acceptance**: `python3 -m unittest tests.test_overlap` exits 0.
