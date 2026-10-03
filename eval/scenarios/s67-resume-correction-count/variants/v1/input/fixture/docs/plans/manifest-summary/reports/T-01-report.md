# T-01 report — Parse export rows

## Authorization and preflight
- Run `2026-09-15-s3/T-01/executor/1`, authorized by Imogen's "run T-01" in session 3. Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: the repo had no reader; the check expects `tests/test_rows.py` green; the brief asks for one record per data row.

## Implementation and target observation
- `manifest/rows.py` added with `Parcel` and `read_rows`; `tests/test_rows.py` written before the reader.
- Validation 1: `python3 -m unittest tests.test_rows -q` → exit 0 (2 tests). Raw: `verification-records/2026-09-15-s3_T-01_v1_20260915T113512Z.md`.

## Correction journal
- none: the first validation passed.

## Final status
- Complete. Method: command. Independence: same-session observation, no reviewer required by the brief.

Receipt — done: the reader and its tests. Remaining: nothing for this task. Next step: T-02 (owner: Imogen reviews the fixture).
