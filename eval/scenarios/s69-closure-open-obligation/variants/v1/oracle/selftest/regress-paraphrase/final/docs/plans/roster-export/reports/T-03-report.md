# T-03 report — Format document

## Authorization and preflight
- Run `2026-09-15-s5/T-03/executor/1`, authorized by Priya ("run T-03", session 5). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: the format lived in Priya's head; the check counts the documented columns; the brief asks for the four columns.

## Result
- `docs/export-format.md` written: the four columns, their meaning, encoding and line endings.
- Validation 1: `grep -c '^| \`' docs/export-format.md` → `4`, exit 0. Raw: `verification-records/2026-09-15-s5_T-03_v1_20260915T173340Z.md`.

## Correction journal
- none.

## Final status
- Complete. Method: command.

Receipt — done: the format document. Remaining: nothing for this task. Next step: T-04 (Priya authorizes).
