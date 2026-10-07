# T-01 report — Rota reader

## Authorization and preflight
- Run `2026-09-09-s3/T-01/executor/1`, authorized by Ingrid ("go on T-01", session 3). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no reader existed; the check expects `tests.test_shifts` green; the brief asks for the shifts in rota order and a refusal when a column is missing.

## Result
- `tests/test_shifts.py` first, then `reminders/shifts.py`; the missing-column case checked by hand on a scratch rota without `start` → `ValueError: rota lacks column(s): start`.
- Validation 1: `python3 -m unittest tests.test_shifts -q` → exit 0. Raw: `verification-records/2026-09-09-s3_T-01_v1_20260909T182214Z.md`.

## Correction journal
- none; the first validation passed.

## Final status
- Complete. Method: command.

Receipt — done: the reader and its test. Remaining: nothing for this task. Next step: T-02 (Ingrid authorizes).
