# Task T-8502 — Due date rule

- **Write scope**: `loans/due.py`, `tests/test_due.py`
- **Depends on**: T-8501 (the member lookup).
- **Decisions**: D-8401.
- **Goal**: `due_on(start)` returns the day a loan started on `start` has to come back, as decided.
- **Acceptance**: `python3 -m unittest tests/test_due.py` exits 0.
