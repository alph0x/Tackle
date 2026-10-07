# T-01 report — Loan reader

## Authorization and preflight
- Run `2026-08-20-s3/T-01/executor/1`, authorized by Tomás ("go on T-01", session 3). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no reader existed; the check expects `tests.test_loans` green; the brief asks for grouping by card with D-03's cut-off.

## Result
- `tests/test_loans.py` first, then `notices/loans.py` with `read_loans` and `overdue_by_patron`.
- Boundary case run by hand: a loan due 2026-09-01 on a 2026-09-01 run is not grouped (D-03).
- Validation 1: `python3 -m unittest tests.test_loans -q` → exit 0. Raw: `verification-records/2026-08-20-s3_T-01_v1_20260820T164512Z.md`.

## Correction journal
- none; the first validation passed.

## Final status
- Complete. Method: command.

Receipt — done: `notices/loans.py`, `tests/test_loans.py`. Remaining: nothing for this task. Next step: T-02 (Tomás authorizes).
