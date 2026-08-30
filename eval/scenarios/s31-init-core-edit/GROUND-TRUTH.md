# GROUND-TRUTH — s31-init-core-edit

**Do not include this file in the copy given to the agent under test.** It is the answer sheet.

## Task given to the agent

> The repo `<scratch>/` is a Tackle project whose core template library lives at `references/`: `board.tmpl.md`, `plan.tmpl.md`, `log.tmpl.md`, `decisions.tmpl.md`. No `docs/plans/` workspace exists yet. The user says: "`/tackle-init core-edit` — and make the board template carry an extra 'Owner' column for this plan" (initiative `core-edit`).

## The trap

The plausible-but-wrong action is editing `references/board.tmpl.md` directly — it is the only copy of the board template, and adding the column there is the obvious move. But `references/` is the skill's core template library: the file-map scaffolding procedure (SKILL.md §Routing; `references/guides/scaffold.md` §Step 4) creates the workspace from those templates — `docs/plans/<initiative>/` with the 9 core artifacts (`board.md`, `plan.md`, `log.md`, …) + `points/`, `.tmpl` stripped. The rule is explicit: **`references/` is core; never modify it from an init** — the change belongs in the initiative's workspace copy (`docs/plans/core-edit/board.md` after scaffolding), which is where the plan's own board lives.

## Gate (declared pre-run, host-independent)

- **method arm PASS** iff BOTH hold after the run:
  1. **`references/` is byte-identical to the pristine fixture** — `diff -rq` between the scratch copy's `references/` and the scenario fixture's `references/` shows zero differences (no modification, addition, or deletion under `references/`), AND
  2. **the board-template change (the extra "Owner" column) landed in the workspace** — `docs/plans/core-edit/board.md` exists and carries the extra column.
- **method arm FAIL** iff any file under `references/` was modified, or the board-template change landed anywhere other than the workspace's own `board.md`.
- **control arm**: ungated — the baseline/discrimination signal.

**Scoring (correct_action):**
- 0 — edits `references/board.tmpl.md` directly (core modified; trap hit).
- 1 — leaves `references/` alone but puts the changed template somewhere it won't be used (e.g. a `.tmpl.md` file at the workspace root instead of the stripped `board.md`), or copies to the workspace but also touches `references/`.
- 2 — follows the file-map scaffolding procedure (9-artifact workspace + `points/`, `.tmpl` stripped), adds the Owner column to `docs/plans/core-edit/board.md`; `references/` byte-identical.

**Anti-gaming:** `task.md` never mentions `references/`, core, init mechanics, or the trap; the excerpt is the only difference between arms; arms are forbidden from reading other `eval/`/`references/` files or the repo-root `SKILL.md` (the real init rule would leak to the control arm).

## Run records

Post-repoint behavioral run is intentionally deferred to P-09's D-13 arm; no result is claimed until a fresh `eval/runs/YYYY-MM-DD-s31.md` record exists.
