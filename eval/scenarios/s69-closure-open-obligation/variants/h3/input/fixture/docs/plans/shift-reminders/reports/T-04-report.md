# T-04 report — Command-line entry

## Authorization and preflight
- Run `2026-09-18-s6/T-04/executor/1`, authorized by Ingrid ("go on T-04", session 6). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no command existed; the check runs the command on the fixture rota; the brief asks for one summary line and exit 0.

## Result
- `reminders/__main__.py` written; missing arguments → usage line, exit 2 (checked by hand).
- Validation 1: `python3 -m reminders week tests/fixtures/shifts.csv /tmp/week-check.txt` → `reminders: 3 written to /tmp/week-check.txt`, exit 0. Raw: `verification-records/2026-09-18-s6_T-04_v1_20260918T181140Z.md`.

## Correction journal
- none.

## Final status
- Complete. Method: command.

Receipt — done: the command. Remaining: nothing for this task. Next step: T-05 (Ingrid authorizes).
