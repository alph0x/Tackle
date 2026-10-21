# Task T-3202 — Retry policy

- **Write scope**: `sync/retry.py`, `tests/test_retry.py`
- **Depends on**: T-3201 (the fetch function).
- **Decisions**: D-1201.
- **Goal**: `with_retries(call, attempts)` retries a failing fetch up to the decided cap and re-raises the last error.
- **Acceptance**: `python3 -m unittest tests.test_retry` exits 0.
