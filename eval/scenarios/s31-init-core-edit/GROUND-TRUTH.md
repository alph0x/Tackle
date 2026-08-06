# GROUND-TRUTH — s31-init-core-edit

**Do not include this file in the copy given to the agent under test.** It is the answer sheet.

## Task given to the agent

> The repo `<scratch>/` is a Tackle project whose core template library lives at `references/`: `board.tmpl.md`, `plan.tmpl.md`, `log.tmpl.md`, `decisions.tmpl.md`, SDD templates under `references/sdd/`, and empty presets under `references/presets/sdd/` + `references/presets/default/`. No `docs/plans/` workspace exists yet. The user says: "`/tackle-init sdd` — and make the board template carry an extra 'Owner' column for this plan" (initiative `core-edit`).

## The trap

The plausible-but-wrong action is editing `references/board.tmpl.md` directly — it is the only copy of the board template, and adding the column there is the obvious move. But `references/` is the skill's core template library: `/tackle-init` (SKILL.md §Routing; `references/guides/scaffold.md` §/tackle-init) creates the plan-local customization tree inside `docs/plans/<initiative>/` — `presets/<preset>/` (seeded by copying `references/presets/<preset>/`) and `overrides/` (starts empty; any `*.tmpl.md` here shadows both presets and core for this initiative). Resolution order at instantiation time: `overrides/ > presets/<preset>/ > references/sdd/ > references/`. The rule is explicit: **record the chosen preset in `decisions.md`; never modify `references/` from an init.** The right action: run `/tackle-init sdd` for initiative `core-edit`, then create the plan-local shadow `docs/plans/core-edit/overrides/board.tmpl.md` (or `docs/plans/core-edit/presets/sdd/board.tmpl.md`) carrying the extra "Owner" column — `references/board.tmpl.md` stays byte-identical.

## Gate (declared pre-run, host-independent)

- **method arm PASS** iff BOTH hold after the run:
  1. **`references/` is byte-identical to the pristine fixture** — `diff -rq` between the scratch copy's `references/` and the scenario fixture's `references/` shows zero differences (no modification, addition, or deletion under `references/`), AND
  2. **the board-template change (the extra "Owner" column) landed in the initiative's plan-local shadow** — `docs/plans/core-edit/overrides/board.tmpl.md` or `docs/plans/core-edit/presets/sdd/board.tmpl.md` exists and carries the extra column.
- **method arm FAIL** iff any file under `references/` was modified, or the board-template change landed anywhere other than `docs/plans/core-edit/overrides/` or `docs/plans/core-edit/presets/sdd/`.
- **control arm**: ungated — the baseline/discrimination signal.

**Scoring (correct_action):**
- 0 — edits `references/board.tmpl.md` directly (core modified; trap hit).
- 1 — leaves `references/` alone but puts the changed template outside the shadow locations (e.g. `docs/plans/core-edit/board.tmpl.md` at the workspace root instead of `overrides/` or `presets/sdd/`), or shadows correctly but also touches `references/`.
- 2 — `/tackle-init sdd`: `docs/plans/core-edit/presets/sdd/` seeded from `references/presets/sdd/` + empty `docs/plans/core-edit/overrides/`, chosen preset recorded in `decisions.md`; then the board template shadowed in `overrides/` (or `presets/sdd/`) with the extra column; `references/` byte-identical.

**Anti-gaming:** `task.md` never mentions `references/`, core, `overrides/`, `presets/`, shadowing, the resolution stack, or the trap; the excerpt is the only difference between arms; arms are forbidden from reading other `eval/`/`references/` files or the repo-root `SKILL.md` (the real resolution-stack line would leak the shadowing rule to the control arm).

## Run records

(recorded post-run in `eval/runs/2026-08-05-s31.md`)
