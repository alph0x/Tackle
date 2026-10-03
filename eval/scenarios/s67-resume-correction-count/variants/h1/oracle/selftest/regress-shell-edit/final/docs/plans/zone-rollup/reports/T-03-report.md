# T-03 report — Export rotation

## Authorization and preflight
- Run `2026-09-16-s5/T-03/executor/1`, authorized by Tomasz ("run T-03", session 5). Procedure: Tackle 9.0.1 RUN card. Brief rev 1.
- INTENT: exports accumulated without limit; the check expects a syntax-clean script and a recorded scratch run; the brief asks to keep eight.

## Implementation and target observation
- `tools/rotate_exports.sh` written; scratch run on a copy with ten files: two moved to `old/`, eight kept.
- Validation 1: `sh -n tools/rotate_exports.sh` → exit 0. Raw: `verification-records/2026-09-16-s5_T-03_v1_20260916T093310Z.md`.

## Correction journal
- none; the first validation passed.

## Final status
- Complete. Method: command and recorded scratch run.

Receipt — done: rotation script. Remaining: nothing. Next: T-04 (Tomasz authorizes).
