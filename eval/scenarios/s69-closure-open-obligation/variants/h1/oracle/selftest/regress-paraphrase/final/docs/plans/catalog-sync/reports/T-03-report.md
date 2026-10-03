# T-03 report — Nightly runner

## Authorization and preflight
- Run `2026-09-12-s5/T-03/executor/1`, authorized by Marcus ("run T-03", session 5). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no runner existed; the check is a syntax check plus the recorded cron entry; the brief asks for the 02:00–03:00 window.

## Result
- `tools/nightly.sh` written; cron entry `15 2 * * * /srv/shopfront-sync/tools/nightly.sh` installed on the operations host by Marcus (D-04).
- Validation 1: `sh -n tools/nightly.sh` → exit 0. Raw: `verification-records/2026-09-12-s5_T-03_v1_20260912T151058Z.md`.

## Correction journal
- none.

## Final status
- Complete. Method: command plus the recorded cron entry.

Receipt — done: the runner and its cron entry. Remaining: nothing for this task. Next step: T-04 (Marcus authorizes).
