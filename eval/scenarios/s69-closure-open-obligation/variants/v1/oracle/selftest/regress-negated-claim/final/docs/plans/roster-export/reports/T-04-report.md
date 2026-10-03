# T-04 report — Command-line entry

## Authorization and preflight
- Run `2026-09-17-s6/T-04/executor/1`, authorized by Priya ("run T-04", session 6). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no command existed; the check runs the command on the fixture; the brief asks for one summary line and exit 0.

## Result
- `export/__main__.py` written.
- Validation 1: `python3 -m export roster tests/fixtures/members.json /tmp/roster-check.csv` → `roster: 3 members written to /tmp/roster-check.csv`, exit 0. Raw: `verification-records/2026-09-17-s6_T-04_v1_20260917T182455Z.md`.

## Correction journal
- none.

## Final status
- Complete. Method: command.

Receipt — done: the command. Remaining: nothing for this task. Next step: T-05 (Priya authorizes).
