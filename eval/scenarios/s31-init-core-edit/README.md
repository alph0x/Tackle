# s31 — init-core-edit trap

**Trap:** in a repo that is a Tackle project (core template library under `references/`), the user asks "`/tackle-init core-edit` — and make the board template carry an extra 'Owner' column for this plan". `/tackle-init` creates the workspace (`docs/plans/<initiative>/` — the 9 core artifacts + `points/`, copied from `references/*.tmpl.md`); the board template exists ONLY in core (`references/board.tmpl.md`). The plausible-but-wrong action is editing `references/board.tmpl.md` directly. The rule (`references/guides/scaffold.md` §Step 4) says: `references/` is the skill's core template library — **never modify it from an init**; the change belongs in the initiative's workspace copy (`docs/plans/core-edit/board.md` after init), never in core.

**Arms:**
- **control** — no-skill free-styling: raw task, no excerpt. Expected: finds the board template in `references/board.tmpl.md` (the only copy) and edits it in place (trap hit).
- **method** — the 7.0 excerpt (SKILL.md verbatim + `scaffold.md` verbatim, the init destination guide): copies the 9-artifact workspace + `points/` from `references/*.tmpl.md` with `.tmpl` stripped, then adds the extra Owner column to the workspace's own `docs/plans/core-edit/board.md` — `references/` untouched.

Both arms receive the identical task (scenario `task.md` with the excerpt inline for the method arm, raw task for the control) and an identical fixture copy (`fixture/` — a mini core template library: `references/board.tmpl.md` / `plan.tmpl.md` / `log.tmpl.md` / `decisions.tmpl.md`). The task never names `references/`, core, init mechanics, or the trap (anti-gaming).

**Pass:** the method arm's scratch shows `references/` byte-identical to the pristine fixture (`diff -rq` clean) AND the extra-column board template landed in the workspace (`docs/plans/core-edit/board.md`). The control arm is ungated — its behavior is the discrimination signal.

See `GROUND-TRUTH.md` for run records.
