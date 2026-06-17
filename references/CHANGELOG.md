# Tackle changelog
## Tackle 2.0

- **SDD phase entry points**: `/tackle-init`, `/tackle-constitution`, `/tackle-specify`, `/tackle-tasks`, `/tackle-implement`, `/tackle-next`, `/tackle-checklist`.
- **Plan execution**: `/tackle-implement` runs the plan point-by-point; `/tackle-next` executes one ready point.
- **Template-resolution stack**: `docs/plans/<initiative>/overrides/` → `presets/<preset>/` → `references/sdd/` → `references/`.
- **Visible plan-local customization**: `presets/` and `overrides/` live inside `docs/plans/<initiative>/`, not at the repo root.
- **New depth artifacts**: `team.md` (execution team protocol) and `board.md` (canonical status board).
- **Variable execution teams**: Solo / Pair / Pod / Squad, sized to point complexity.
- Bumped default `Methodology:` stamp to **Tackle 2.0** in `AGENTS.tmpl.md`, `lite-plan.tmpl.md`, and `README.tmpl.md`.

## Tackle 1.5

- **Step 1.5 — Anchor the intake before sizing**: lock problem, observable result, top 2 non-goals, and highest-shape decision before choosing a gate.
- **Step 5.75 — Stabilize the design contract before decomposition (Full-gate hard gate)**: no point briefings until `design-contract.md`/`api-spec.md` survives a session unchanged; points cite contract sections instead of inlining spec.
- **Step 6 — Skeleton-board-first checkpoint**: validate only a skeleton table (P-0N / What / Depends-on / Touches / done-signal shape) before writing full point briefings.
- **Step 6.5 — Q-guard + contract-churn guard**: active points may not depend on unresolved user-owned questions; contract changes since the last log entry fail the lint until all citing points are reconciled.
- **Step 10 — Improve / upgrade mode**: detect Tackle plans (current/old) or unstructured sources and migrate/convert them to the current methodology without re-planning.
- **Step 11 — Versioning and release notes**: optional changelog for the skill itself.
- Bumped default `Methodology:` stamp to **Tackle 1.5** in `AGENTS.tmpl.md`, `lite-plan.tmpl.md`, and `README.tmpl.md`.

## Tackle 1.4

- Initial stable methodology with Create / Resume / Status / List / Next / Migrate modes.
- Full vs Lite vs None gate sizing.
- Decision ownership, provisional questions, batched doubts.
- `points/*.md` briefings with `Depends-on` / `Touches` / runnable done-signals.
- `plan.md` §6.1 universal per-point acceptance.
- `design-contract.md`, `foundations.md`, `execution-strategy.md` depth artifacts.
