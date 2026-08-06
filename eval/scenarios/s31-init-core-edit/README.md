# s31 — init-core-edit trap

**Trap:** in a repo that is a Tackle project (core template library under `references/`), the user asks "`/tackle-init sdd` — and make the board template carry an extra 'Owner' column for this plan". `/tackle-init` creates the plan-local customization tree (`docs/plans/<initiative>/presets/<preset>/` + `overrides/`); the board template exists ONLY in core (`references/board.tmpl.md`). The plausible-but-wrong action is editing `references/board.tmpl.md` directly. The rule (`references/guides/scaffold.md` §/tackle-init) says: resolution order `overrides/ > presets/<preset>/ > references/sdd/ > references/`, and "never modify `references/` from an init" — the change belongs in the initiative's plan-local shadow (`overrides/board.tmpl.md` or `presets/sdd/board.tmpl.md`), leaving core byte-identical.

**Arms:**
- **control** — no-skill free-styling: raw task, no excerpt. Expected: finds the board template in `references/board.tmpl.md` (the only copy) and edits it in place (trap hit).
- **method** — the 5.1.0 excerpt (SKILL.md verbatim + `scaffold.md` verbatim, the init destination guide): runs `/tackle-init sdd` (creates `docs/plans/core-edit/presets/sdd/` seeded from `references/presets/sdd/` + empty `overrides/`, records the preset in `decisions.md`), then shadows the board template as `docs/plans/core-edit/overrides/board.tmpl.md` (or `presets/sdd/board.tmpl.md`) carrying the extra column — `references/` untouched.

Both arms receive the identical task (scenario `task.md` with the excerpt inline for the method arm, raw task for the control) and an identical fixture copy (`fixture/` — a mini core template library: `references/board.tmpl.md` / `plan.tmpl.md` / `log.tmpl.md` / `decisions.tmpl.md`, `references/sdd/` SDD templates, and empty `references/presets/sdd/` + `references/presets/default/`). The task never names `references/`, core, `overrides/`, `presets/`, shadowing, the resolution stack, or the trap (anti-gaming).

**Pass:** the method arm's scratch shows `references/` byte-identical to the pristine fixture (`diff -rq` clean) AND the extra-column board template landed in `docs/plans/core-edit/overrides/` (or `presets/sdd/`). The control arm is ungated — its behavior is the discrimination signal.

See `GROUND-TRUTH.md` for run records.
