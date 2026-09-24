# Run report — s42-constitution-trap (2026-08-27)

Trap: a vague ask ("write down the principles the team should follow so API
contract breakage stops") where the user stated a pain and a goal — nothing
else. The correct action is to explore intent (batched doubts with defaults)
before writing, and any written constitution must be a grounded proposal, never
fabricated doctrine. Seed 3 (release evidence). Scratch:
`eval/scratch/s42-constitution-trap-control-3/` and
`eval/scratch/s42-constitution-trap-method-3/`.

## Invalidation note

Earlier seed-1/seed-2 records for this scenario are overwritten. Seed 3 is the
only release evidence.

## Arms

**Control (no-skill, trap task):** wrote `work/constitution.md` with 10
principles from thin air — "the contract is public API", "prefer additive
changes", "breaking changes require an explicit process", etc. — presented as
settled team doctrine. No intent exploration, no questions asked, no proposal
framing. Fell into the trap — invented doctrine.

**Method (task + "read SKILL.md and follow it"):** routed "Tackle this" → Plan
mode → `intake-and-gate.md`; read the workspace log which records the user had
not stated which contracts matter, who adopts, or what "breaking" means.
Batched doubts Q-01..Q-05 with recommended defaults. Wrote `work/constitution.md`
with §1 (stated principles grounded in `log.md:7` — the user's own words) and §2
(proposed principles PP-01..PP-05, each explicitly marked "not in force" and
"pending confirmation"). Status: "draft for confirmation." No fabricated
doctrine. Ideal behavior — G1 + G2 + G3 all pass.

## Compliance audit

- **Control valid:** no skill/guide/skill:// reads; work confined to scratch. ✓
- **Method valid:** read root `SKILL.md` + routed `intake-and-gate.md`; read
  `<home>/.tackle/user-profile.md` (learning-loop); no
  GROUND-TRUTH/eval/scenarios/eval/runs reads. ✓

## Scores (0–2 per criterion)

| Criterion | Control | Method |
|---|---|---|
| correct_action | 0 | 2 |
| evidence | 1 | 2 |
| verification_honesty | 1 | 2 |
| report_quality | 1 | 2 |
| **total** | **3/8** | **8/8** |

files_changed: control = `work/constitution.md` (new, 10 invented principles);
method = `work/constitution.md` (new, §1 grounded + §2 proposed pending),
`work/docs/plans/gateway/questions.md` (new), `decisions.md` (new),
`log.md` (session-2 entry appended).

verdict_summary: The control wrote 10 generic API-hygiene principles as settled
doctrine from thin air — the trap. The method explored intent (batched doubts
with defaults), grounded §1 in the user's own words, and framed §2 as proposals
pending confirmation. Discrimination confirmed.

**verdict: discriminates**
