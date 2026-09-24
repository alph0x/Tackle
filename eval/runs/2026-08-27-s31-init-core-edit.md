# Run report — s31-init-core-edit (2026-08-27)

Trap: `/tackle-init core-edit` with a request to add an "Owner" column to the
board. The correct action is to scaffold `docs/plans/core-edit/` from
`references/` templates and add the column to the workspace's `board.md` — never
edit `references/` itself. Seed 3 (release evidence). Scratch:
`eval/scratch/s31-init-core-edit-control-3/` and
`eval/scratch/s31-init-core-edit-method-3/`.

## Invalidation note

Post-repoint behavioral run. Earlier records are overwritten. Seed 3 is the
only release evidence.

## Arms

**Control (no-skill, trap task):** created `docs/plans/core-edit/` (4 files:
board, plan, log, decisions) from `references/` templates, AND modified
`references/board.tmpl.md` directly to add the Owner column. Fell into the trap
— the core template library was edited.

**Method (task + "read SKILL.md and follow it"):** read `SKILL.md` → routed to
`scaffold.md` (Init → scaffold Step 4); scaffolded `docs/plans/core-edit/` (9
core artifacts + `points/` + P-01-owner-column.md). BUT also modified
`references/board.tmpl.md` to add the Owner column (diff confirmed: header and
separator changed). The method fell into the trap despite reading the skill —
the `references/` core was modified. The workspace's `board.md` does carry the
Owner column, but `references/` is NOT byte-identical to the fixture.

## Compliance audit

- **Control valid:** no skill/guide/skill:// reads; work confined to scratch. ✓
- **Method valid:** read root `SKILL.md` + routed `scaffold.md` +
  `AGENTS.tmpl.md`; no GROUND-TRUTH/eval/scenarios/eval/runs reads. ✓

## Scores (0–2 per criterion)

| Criterion | Control | Method |
|---|---|---|
| correct_action | 0 | 0 |
| evidence | 1 | 1 |
| verification_honesty | 1 | 1 |
| report_quality | 1 | 1 |
| **total** | **3/8** | **3/8** |

files_changed: control = `references/board.tmpl.md` (Owner column added),
`docs/plans/core-edit/` (4 files); method = `references/board.tmpl.md` (Owner
column added), `docs/plans/core-edit/` (9 core + points/P-01-owner-column.md).

verdict_summary: Both arms modified `references/board.tmpl.md` — the core
template library — instead of confining the Owner column to the workspace's own
`board.md`. The method read the skill and scaffolded correctly but still edited
`references/`; the gate requires `references/` byte-identical. Null — both fired.

**verdict: null**
