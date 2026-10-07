# T-03 report — Layout document

## Authorization and preflight
- Run `2026-09-14-s5/T-03/executor/1`, authorized by Harriet ("go ahead with T-03", session 5). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: the layout was only in the committee minutes; the check counts the documented lines; the brief asks for the five lines.

## Result
- `docs/statement-format.md` written: the five lines, the rates they use (D-03), encoding and line endings.
- Validation 1: `grep -c '^| \`' docs/statement-format.md` → `5`, exit 0. Raw: `verification-records/2026-09-14-s5_T-03_v1_20260914T174120Z.md`.

## Correction journal
- none.

## Final status
- Complete. Method: command.

Receipt — done: the layout document. Remaining: nothing for this task. Next step: T-04 (Harriet authorizes).
