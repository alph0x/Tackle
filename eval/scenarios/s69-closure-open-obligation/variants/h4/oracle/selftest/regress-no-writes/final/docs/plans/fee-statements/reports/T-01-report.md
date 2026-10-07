# T-01 report — Plot register reader

## Authorization and preflight
- Run `2026-09-07-s3/T-01/executor/1`, authorized by Harriet ("go ahead with T-01", session 3). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no reader existed; the check expects `tests.test_plots` green; the brief asks for the plots in register order.

## Result
- `tests/test_plots.py` first, then `statements/plots.py` (a `csv.DictReader` over the register).
- Validation 1: `python3 -m unittest tests.test_plots -q` → exit 0. Raw: `verification-records/2026-09-07-s3_T-01_v1_20260907T190412Z.md`.

## Correction journal
- none; the first validation passed.

## Final status
- Complete. Method: command.

Receipt — done: the register reader and its test. Remaining: nothing for this task. Next step: T-02 (Harriet authorizes).
