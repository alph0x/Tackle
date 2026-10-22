# Task T-8503 — Renewal limit

- **Write scope**: `loans/renew.py`
- **Depends on**: T-8501 (the member lookup).
- **Decisions**: D-8402.
- **Goal**: `may_renew(renewals)` says whether another renewal is allowed, as decided.
- **Acceptance**: `python3 -m unittest tests/test_renew.py` exits 0.
