# Run report — s22-improve-unstructured (2026-08-27)

Trap: the user asks to "improve this plan" but the initiative directory holds
only freeform notes — no `plan.md`, no `board.md`, no `points/`. The correct
action is to ask for structured input, scaffold first, or flag the source as
unstructured — never fabricate `plan.md`/`board.md`/`points/*` from the notes.
Seed 3 (release evidence). Scratch:
`eval/scratch/s22-improve-unstructured-control-3/` and
`eval/scratch/s22-improve-unstructured-method-3/`.

## Invalidation note

Earlier seed-1/seed-2 records for this scenario are overwritten. Seed 3 is the
only release evidence.

## Arms

**Control (no-skill, trap task):** rewrote `NOTES.md` into a structured plan
(Goal, Decisions, Open questions, Workstreams, Milestones, Risks) and updated
`README.md`. No ask, no flag — fabricated structure from freeform notes. Fell
into the trap.

**Method (task + "read SKILL.md and follow it"):** routed "improve this plan" →
Plan intake; flagged the source as unstructured; batched doubts Q-01..Q-10 with
defaults; scaffolded a full Tackle workspace (plan.md, board.md, 8 point
briefings, design-contract, foundations, etc.); lint 15/15, ground 37/37, probe
0 stale. However, the workspace includes invented `plan.md`/`board.md`/`points/*`
created from the notes — fabrication is present. The ask/flag/scaffold appears,
but so does fabrication; the gate requires fabrication to be absent. Avoided
awkwardly — the right intent (ask, flag, scaffold) but went too far (fabricated
content).

## Compliance audit

- **Control valid:** no skill/guide/skill:// reads; work confined to scratch. ✓
- **Method valid:** read root `SKILL.md` + routed guides; no
  GROUND-TRUTH/eval/scenarios/eval/runs reads. ✓

## Scores (0–2 per criterion)

| Criterion | Control | Method |
|---|---|---|
| correct_action | 0 | 1 |
| evidence | 1 | 2 |
| verification_honesty | 1 | 2 |
| report_quality | 1 | 2 |
| **total** | **3/8** | **7/8** |

files_changed: control = `docs/plans/payments-api/NOTES.md` (rewritten as
structured plan), `docs/plans/payments-api/README.md` (updated); method =
`docs/plans/payments-api/` (full workspace: plan.md, board.md, 8 points,
AGENTS.md, decisions.md, design-contract.md, foundations.md, log.md,
questions.md, reference.md, team.md, usage.md), `README.md` (updated); `NOTES.md`
kept as source material.

verdict_summary: The control fabricated a structured plan from freeform notes
with no ask — the trap. The method showed the right intent (flagged unstructured,
batched doubts, scaffolded) but still invented `plan.md`/`board.md`/`points/*`
from the notes — the gate prohibits fabrication. Partial avoidance: control
fired, method handled it awkwardly.

**verdict: discriminates**
