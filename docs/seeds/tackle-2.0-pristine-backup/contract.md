# Design contract — Tackle 2.0 (authoritative surface)

**This file is normative. Points implement it; they do not redefine it.**

## Signatures / API surface

### Trigger words (public routing contract)

| Trigger | Phase | Default gate | Output workspace |
|---|---|---|---|
| `/tackle-init` or `tackle-init` | Init | none | `docs/plans/<initiative>/presets/`, `docs/plans/<initiative>/overrides/` |
| `/tackle-constitution` or `tackle-constitution` | Constitution | none | `docs/plans/<initiative>/constitution.md` |
| `/tackle-specify` or `tackle-specify` | Specify | none/Lite | `docs/plans/<initiative>/spec.md` |
| `/tackle-plan` or `tackle-plan` / `plan de acción` / `tackle this` | Plan | Full/Lite/None per Step 2 | `docs/plans/<initiative>/` |
| `/tackle-tasks` or `tackle-tasks` | Tasks | none/Lite | `docs/plans/<initiative>/tasks.md` |
| `/tackle-implement` or `tackle-implement` | Implement | none | executed plan + updated board/log |
| `/tackle-next` or `tackle-next` | Execute next | none | one executed point + updated board/log |
| `/tackle-checklist` or `tackle-checklist` | Checklist | none | `docs/plans/<initiative>/checklist.md` |

Old triggers (`tackle this`, `plan de acción`, etc.) continue to route to **Plan**.

### Template-resolution stack

Lookup order (first match wins), scoped to the plan workspace:

1. `docs/plans/<initiative>/overrides/<name>.tmpl.md`
2. `docs/plans/<initiative>/presets/<preset>/<name>.tmpl.md`
3. `references/sdd/<name>.tmpl.md` (for SDD phase templates)
4. `references/<name>.tmpl.md` (core templates)

### Execution loop surface

`/tackle-implement` runs the plan as an execution loop over `board.md`:

- Reads dependency order from the decomposition table.
- Picks the next 🔴 point whose dependencies are 🟢 (or none).
- Spawns a **point team** (see `team.md`): Driver (TDD), Spec Reader, Quality Guardian, Coordinator.
- The Driver executes the point and runs its done-signal.
- The Spec Reader verifies alignment with the point briefing and this contract.
- The Quality Guardian reviews the diff for quality and conventions.
- The Coordinator updates status in `board.md`: 🔴 → 🟡 → 🟢 (or ⏸ on block).
- Appends a `log.md` entry with the result.
- Repeats until no 🔴/🟡 points remain or a loop budget is exhausted.
- A point that fails its done-signal is retried up to its loop budget (default 3), then marked ⏸ and the loop stops.

### File naming convention

- Core plan templates: `*.tmpl.md` in `references/`
- SDD phase templates: `*.tmpl.md` in `references/sdd/`
- Preset templates: `*.tmpl.md` in `references/presets/<preset>/`
- Project overrides: `*.tmpl.md` in `docs/plans/<initiative>/overrides/`
- Project presets: `*.tmpl.md` in `docs/plans/<initiative>/presets/<preset>/`

### Local customization layout (created by `/tackle-init` inside the plan workspace)

```
docs/plans/<initiative>/
├── ...
├── constitution.md
├── overrides/          ← project-local template overrides
│   └── *.tmpl.md
└── presets/
    └── <preset>/       ← copy of references/presets/<preset>/ (may be empty; absent files fall through the stack)
        └── *.tmpl.md
```

`/tackle-init` only creates the plan-local `presets/` and `overrides/` directories. It does not install files outside the plan workspace; the skill is consumed from the repo's own `SKILL.md` and `references/`.

## States & transitions

- **No local customization tree** → `/tackle-init` → `docs/plans/<initiative>/presets/` and `docs/plans/<initiative>/overrides/` exist.
- **No constitution** → `/tackle-constitution` → `docs/plans/<initiative>/constitution.md` created.
- **No spec** → `/tackle-specify` → `docs/plans/<initiative>/spec.md` created (Lite workspace).
- **No plan** → `/tackle-plan` → Full/Lite Tackle workspace under `docs/plans/<initiative>/`.
- **Plan exists** → `/tackle-tasks` → `tasks.md` derived from `plan.md` §5.
- **Plan exists** → `/tackle-implement` → execution loop runs points in dependency order.
- **Any artifact** → `/tackle-checklist` → `checklist.md` from selected source.

## Error model

| Error | Recoverable? | Handling |
|---|---|---|
| Unknown trigger | terminal | reply with trigger list |
| Missing `presets/`/`overrides/` when a preset/override is requested | recoverable | run `/tackle-init` or fall back to core templates |
| Phase run out of order (e.g. `/tackle-implement` with no plan) | recoverable | suggest preceding phase, produce a degraded artifact |
| Preset not found | recoverable | fall back to `references/presets/default/` |
| Point done-signal fails | recoverable | retry up to loop budget, then mark ⏸ and stop |
| Blocked point (dependency not 🟢) | recoverable | execute dependencies first |

## Invariants / policies

- Every new trigger MUST preserve all existing triggers.
- Every new template MUST live in `references/sdd/` or `references/presets/`; no template lives at the repo root.
- The planning workspace (`docs/plans/<initiative>/`) remains the canonical handoff artifact; nothing Tackle-related lives at the repo root.
- All customization artifacts (`constitution.md`, `overrides/`, `presets/`) live visibly inside the plan workspace, not in hidden directories.
- `plan.md` §5 is the single source of execution order; the execution loop never reorders it, only advances statuses.
- `log.md` is append-only; execution entries record status changes, not chat history.
- `SKILL.md` is the single source of truth for routing; `README.md` only summarizes.

## Spec → point map

| Spec section | Implemented by |
|---|---|
| Trigger table | P-08 |
| Template-resolution stack | P-06 |
| Local customization layout | P-07 |
| SDD phase templates | P-01, P-02, P-03, P-04, P-05 |
| Execution loop | P-04, P-08 |
