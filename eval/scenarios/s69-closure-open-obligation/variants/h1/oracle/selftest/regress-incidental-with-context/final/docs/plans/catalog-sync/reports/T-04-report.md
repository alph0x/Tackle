# T-04 report — Acceptance run

## Authorization and preflight
- Run `2026-09-17-s6/T-04/executor/1`, authorized by Marcus ("run T-04", session 6). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no acceptance script existed; the check expects `sh checks/accept.sh` exit 0; the brief asks for tests plus the sample comparison.

## Result
- `checks/accept.sh` written; negative case on a scratch copy with `stock` renamed → `accept: feed differs from the agreed sample`, exit 1 (in the raw record).
- Validation 1: `sh checks/accept.sh` → `accept: ok`, exit 0. Raw: `verification-records/2026-09-17-s6_T-04_v1_20260917T164415Z.md`.

## Correction journal
- none; the first validation passed.

## Final status
- Complete. Method: command, with the negative case recorded.

Receipt — done: the acceptance script. Remaining: nothing for this task. Next step: deliverable acceptance on the integrated tree (coordinator).
