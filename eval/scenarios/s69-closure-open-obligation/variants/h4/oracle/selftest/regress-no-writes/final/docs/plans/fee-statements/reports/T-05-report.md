# T-05 report — Acceptance run

## Authorization and preflight
- Run `2026-09-21-s7/T-05/executor/1`, authorized by Harriet ("go ahead with T-05", session 7). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no acceptance script existed; the check expects `sh checks/accept.sh` exit 0; the brief asks for the tests plus the sample comparison.

## Result
- `checks/accept.sh` written; negative case on a scratch copy with the water charge set to 1600 → `tests.test_render` fails and the script stops with exit 1 before the comparison (run by hand).
- Validation 1: `sh checks/accept.sh` → `accept: ok`, exit 0. Raw: `verification-records/2026-09-21-s7_T-05_v1_20260921T190233Z.md`.

## Correction journal
- none; the first validation passed.

## Final status
- Complete. Method: command, with the negative case recorded.

Receipt — done: the acceptance script. Remaining: nothing for this task. Next step: deliverable acceptance on the integrated tree (coordinator, session 8).
