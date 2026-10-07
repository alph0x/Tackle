# T-02 report — Notice template

## Authorization and preflight
- Run `2026-08-25-s4/T-02/executor/1`, authorized by Tomás ("go on T-02", session 4). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: the wording lived on the board's approval sheet; the check expects `tests.test_template` green against the samples; the brief asks for the agreed wording, oldest due first.

## Result
- `tests/test_template.py` first (each rendered notice equal to its sample), then `notices/template.py` with the four wording constants and `render_notice`.
- Validation 1: `python3 -m unittest tests.test_template -q` → exit 0. Raw: `verification-records/2026-08-25-s4_T-02_v1_20260825T172038Z.md`.
- Owner reading: Tomás read the rendered notice for HL-20817 in session and confirmed it matches what the board approved.

## Correction journal
- none; the first validation passed.

## Final status
- Complete. Method: command plus owner reading.

Receipt — done: `notices/template.py`, `tests/test_template.py`, Tomás's reading of a rendered notice. Remaining: nothing for this task. Next step: T-03 (Tomás authorizes).
