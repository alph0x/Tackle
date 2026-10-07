# T-02 report — Statement renderer

## Authorization and preflight
- Run `2026-09-09-s4/T-02/executor/1`, authorized by Harriet ("go ahead with T-02", session 4). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no renderer existed; the check expects `tests.test_render` green against the agreed sample; the brief asks for the five lines at the D-03 rates.

## Result
- `tests/test_render.py` first (rendered file equal to the sample), then `statements/render.py` with the D-03 rates in pence, `statement` and `write_statements`.
- Validation 1: `python3 -m unittest tests.test_render -q` → exit 0. Raw: `verification-records/2026-09-09-s4_T-02_v1_20260909T183655Z.md`.
- Invalid case: a scratch plot without `size_rods` raises `KeyError: 'size_rods'` (run by hand, as the brief asks).
- Owner review: Harriet read the three rendered statements in session and confirmed the layout and the totals against her own sums for plots 7A, 12 and 19B.

## Correction journal
- none; the first validation passed.

## Final status
- Complete. Method: command plus owner review.

Receipt — done: `statements/render.py`, `tests/test_render.py`, Harriet's review of the rendered statements. Remaining: nothing for this task. Next step: T-03 and T-04 (Harriet authorizes).
