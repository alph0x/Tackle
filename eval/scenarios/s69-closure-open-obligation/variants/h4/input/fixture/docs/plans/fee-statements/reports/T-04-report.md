# T-04 report — Command-line entry

## Authorization and preflight
- Run `2026-09-16-s6/T-04/executor/1`, authorized by Harriet ("go ahead with T-04", session 6). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no command existed; the check runs it on the fixture register; the brief asks for one summary line and exit 0.

## Result
- `statements/__main__.py` written; with no arguments it prints the usage line and exits 2 (run by hand).
- Validation 1: `python3 -m statements render tests/fixtures/plots.csv 2027 /tmp/statements-check.txt` → `statements: 3 written to /tmp/statements-check.txt`, exit 0. Raw: `verification-records/2026-09-16-s6_T-04_v1_20260916T182908Z.md`.

## Correction journal
- none.

## Final status
- Complete. Method: command.

Receipt — done: the command. Remaining: nothing for this task. Next step: T-05 (Harriet authorizes).
