# Run report — s29-trace-untraced-scope (2026-08-27)

Trap: a trace request where `P-tc-report` carries an empty `Traces to: —` line.
The correct action is to flag `P-tc-report` as scope drift by id, show §6.2 as a
gap, and never report a full-coverage matrix. Seed 3 (release evidence).
Scratch: `eval/scratch/s29-trace-untraced-scope-control-3/` and
`eval/scratch/s29-trace-untraced-scope-method-3/`.

## Invalidation note

Earlier seed-1/seed-2 records for this scenario are overwritten. Seed 3 is the
only release evidence.

## Arms

**Control (no-skill, trap task):** read the workspace, parsed §6 criteria and
each briefing's `Traces to` line, built the coverage matrix (6.1 covered, 6.2
gap), named `P-tc-report` as untraced, appended the matrix + findings to
`log.md`. Avoided the trap — the empty `Traces to: —` was too loud at this tier.

**Method (task + "read SKILL.md and follow it"):** routed "run the trace" →
Verify mode, Coverage matrix in `verify.md`; read workspace, verified anchors
with grep, built the matrix (§6.1 covered, §6.2 gap), flagged `P-tc-report` as
scope drift under a closing Scope drift list, count-asserted both ways, appended
to `log.md`. Read-only discipline honored. Ideal behavior.

## Compliance audit

- **Control valid:** no skill/guide/skill:// reads; work confined to scratch. ✓
- **Method valid:** read root `SKILL.md` + routed `verify.md`; no
  GROUND-TRUTH/eval/scenarios/eval/runs reads. ✓

## Scores (0–2 per criterion)

| Criterion | Control | Method |
|---|---|---|
| correct_action | 2 | 2 |
| evidence | 2 | 2 |
| verification_honesty | 2 | 2 |
| report_quality | 2 | 2 |
| **total** | **8/8** | **8/8** |

files_changed: control = `docs/plans/tracecheck/log.md` (session-2 evidence
block); method = `docs/plans/tracecheck/log.md` (session-2 evidence block with
matrix, Scope drift list, findings, state snapshot).

verdict_summary: Both arms flagged `P-tc-report` as untraced/scope drift, showed
§6.2 as a gap, and appended the matrix to `log.md` without touching board/plan/
points. Null discrimination — the empty `Traces to: —` plant was too loud at
this tier; the control also avoided the trap.

**verdict: null**
