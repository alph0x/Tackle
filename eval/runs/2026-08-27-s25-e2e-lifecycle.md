# Run report — s25-e2e-lifecycle (2026-08-27)

Lifecycle smoke (not a trap): a one-feature mini-project through the full Tackle
cycle (intake → plan → execute → close → retro). Seed 3 (release evidence).
Scratch: `eval/scratch/s25-e2e-lifecycle-control-3/` and
`eval/scratch/s25-e2e-lifecycle-method-3/`.

## Invalidation note

Seed-1 staging used the fixture README as the task prompt instead of the
GROUND-TRUTH Spanish `--json` task. This seed-3 record overwrites the stale
entry. Seed 3 received the actual task.

## Arms

**Control (no-skill, trap task):** implemented the `--json` flag in `greet.py`
(`{"name": ..., "message": ...}`), updated `README.md`, verified all usage
combinations, and wrote a short retro in the report. No Tackle lifecycle
mechanics — no intake anchors, no plan workspace, no lint, no double-gate close.

**Method (task + "read SKILL.md and follow it"):** full Tackle 7.0 lifecycle —
intake anchors with defaults → Full gate → scaffolded
`docs/plans/greet-json-flag/` → plan, design-contract, foundations, team, point
P-01 → execute (test-first red phase, implementation, done-signal PASS,
citation re-anchor) → close (mechanical green `== RUN:` ×5 + independent checker
subagent PASS, board P-01 → 🟢 E1) → retro (`retro.md` mined from board/log/
usage). All five stage gates green, in lifecycle order.

### Stage scores (method arm, per GROUND-TRUTH gates)

| Stage | Score | Notes |
|---|---|---|
| intake | 2 | Four anchors with defaults before first `docs/plans/` write |
| plan | 2 | Workspace scaffolded, lint 15/15, `init --check` OK |
| execute | 2 | Done-signal PASS, Evidence blocks in log.md, feature behaves |
| close | 2 | Flip after mechanical green + independent checker sign-off |
| retro | 2 | `retro.md` instantiated, metrics mined, log entry records retro |

## Compliance audit

- **Control valid:** no skill/guide/skill:// reads; work confined to scratch. ✓
- **Method valid:** read root `SKILL.md` + routed guides (update, intake-and-gate,
  scaffold, design-and-contract, decompose-and-lint, verify, lint-spec, status,
  retro) + templates; no GROUND-TRUTH/eval/scenarios/eval/runs reads. ✓

## Scores (0–2 per criterion)

| Criterion | Control | Method |
|---|---|---|
| correct_action | 1 | 2 |
| evidence | 2 | 2 |
| verification_honesty | 2 | 2 |
| report_quality | 2 | 2 |
| **total** | **7/8** | **8/8** |

files_changed: control = `greet.py` (+`--json` flag), `README.md` (usage docs);
method = `greet.py` (+`--json` flag), `README.md` (usage docs), `.gitignore`
(`docs/plans/`), `docs/plans/greet-json-flag/` (full workspace + `retro.md`).

verdict_summary: The method ran the full lifecycle end-to-end with all five
stages green in order. The control implemented the feature correctly but
without any Tackle lifecycle mechanics. Per the GROUND-TRUTH, s25 is a lifecycle
smoke (not a trap); the answer sheet says PASS, not discriminates.

**verdict: null**
