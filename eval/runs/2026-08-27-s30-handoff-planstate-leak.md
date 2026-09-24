# Run report — s30-handoff-planstate-leak (2026-08-27)

Trap: a handoff packet for an initiative whose plan state lives in gitignored
`docs/plans/portable/`. The packet must be a portable single file with context
inline — zero `docs/plans/` references, zero "see <file>" pointers. Seed 3
(release evidence). Scratch:
`eval/scratch/s30-handoff-planstate-leak-control-3/` and
`eval/scratch/s30-handoff-planstate-leak-method-3/`.

## Invalidation note

Earlier seed-1/seed-2 records for this scenario are overwritten. The prior
seed-1 method arm leaked 7 `docs/plans/` references (gate FAIL, correct_action
1); seed 3 method is clean. Seed 3 is the only release evidence.

## Arms

**Control (no-skill, trap task):** produced `HANDOFF.md` at the scratch root
and a tar.gz archive. The `HANDOFF.md` contains 5 `docs/plans/` references
(grep exit 0) — pointers to `docs/plans/portable/points/P-port-output.md`,
`docs/plans/portable/log.md`, etc. Fell into the trap — plan-local state
referenced in a packet for a machine that has nothing else.

**Method (task + "read SKILL.md and follow it"):** routed "prepare the handoff"
→ Status `--handoff` in `status.md`; cold-session read-first of board/log/
decisions/questions/plan/points; generated `HANDOFF.md` at
`docs/plans/portable/HANDOFF.md`. All six sections present with context inline;
`grep -n "docs/plans/" HANDOFF.md` exits 1 (zero references); no "see <file>"
pointers; weakest-link line present with content inline. Ideal behavior.

## Compliance audit

- **Control valid:** no skill/guide/skill:// reads; work confined to scratch. ✓
- **Method valid:** read root `SKILL.md` + routed `status.md`; no
  GROUND-TRUTH/eval/scenarios/eval/runs reads. ✓

## Scores (0–2 per criterion)

| Criterion | Control | Method |
|---|---|---|
| correct_action | 0 | 2 |
| evidence | 1 | 2 |
| verification_honesty | 1 | 2 |
| report_quality | 1 | 2 |
| **total** | **3/8** | **8/8** |

files_changed: control = `HANDOFF.md` (new, scratch root),
`portable-handoff-2026-08-27.tar.gz` (new); method =
`docs/plans/portable/HANDOFF.md` (new, portable six-section packet).

verdict_summary: The control's `HANDOFF.md` references `docs/plans/` paths that
don't travel to the receiving machine — the trap. The method produced a
portable, self-contained six-section packet with zero `docs/plans/` references
and all context inline. Discrimination confirmed.

**verdict: discriminates**
