# T-02 report — Sheet import contract

## Authorization and preflight
- Run `2026-09-11-s4/T-02/executor/1`, authorized by Tomasz ("run T-02", session 4). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no fixture or contract existed; the check expects the three files in place and a syntax-clean script; the brief asks for the growers' sign-off.

## Implementation and target observation
- `tests/fixtures/week-38.csv` from Tomasz's export; `tests/fixtures/sheet-import-week-38.csv` as the growers' sheet import takes it (from the legacy exporter's output for week 38); `tests/test_zones.py` from the review (header `zone,mean_c`, rows `north,21.5` and `south,19.0`, plus the sample comparison); `checks/verify.sh` so that T-04 runs one command.
- Validation 1: `python3 -m unittest tests.test_readings -q && sh -n checks/verify.sh` → exit 0. Raw: `verification-records/2026-09-11-s4_T-02_v1_20260911T151902Z.md`.
- Review: the growers (Hanna, Piet) and Tomasz signed off on 2026-09-11; D-02 protects the files.

## Correction journal
- none; the first validation passed.

## Final status
- Complete. Method: command plus owner and grower review.

Receipt — done: fixture, sheet import sample, contract test, verify script, sign-off. Remaining: nothing. Next: T-04 after T-03 (Tomasz).
