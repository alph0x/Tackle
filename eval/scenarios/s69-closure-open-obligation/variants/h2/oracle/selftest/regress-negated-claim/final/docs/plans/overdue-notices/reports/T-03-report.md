# T-03 report — Render command

## Authorization and preflight
- Run `2026-09-03-s5/T-03/executor/1`, authorized by Tomás ("go on T-03", session 5). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: no entry point existed; the check expects two files and exit 0; the brief asks for the command and the wording document.

## Result
- `notices/__main__.py` written; `docs/notice-wording.md` and the README's command line added.
- Invalid case by hand: three arguments → usage line, exit 2.
- Validation 1: `python3 -m notices render tests/fixtures/loans.json 2026-09-01 /tmp/n` → `2 notices written to /tmp/n`, exit 0. Raw: `verification-records/2026-09-03-s5_T-03_v1_20260903T181140Z.md`.

## Correction journal
- none.

## Final status
- Complete. Method: command.

Receipt — done: the command, the wording document, the README line. Remaining: nothing for this task. Next step: T-04 (Tomás authorizes).
