# Tackle changelog

## Tackle 3.0.1

- Companion skills check is now a mandatory Step 0 in `intake-and-gate.md`.
- `SKILL.md` renamed "Optional skills" to "Companion skills" and clarified that the check must happen before intake and be recorded in the log.

## Tackle 3.0

- Anchored citations with mechanical drift checks and derived staleness (`/tackle-ground`).
- Evidence blocks + attempt journals + escalation packets in the log.
- Sealed Acceptance sections (`SEALED: D-xx`) and sealed contract sections.
- Mechanical lint-spec guide with copy-paste checks and `lint: N/M checks passed` score line.
- Regression sweep: re-run done-signals of intersecting 🟢 points before flipping a new one.
- `/tackle-drill` cold-start readiness drill.
- Context budgets (point ≤ 150 lines, contract section ≤ 40 lines, digest ≤ 12 lines) and log-archive protocol.
- Reversibility section for production-path points.
- `/tackle-trace` criterion↔point coverage matrix.
- `/tackle-retro` initiative retrospective + `retro.md` template.
- `/tackle-handoff` portable handoff packet.
- Learning loop: opt-in profiles at `~/.tackle/user-profile.md` and `<repo>/.tackle/profile.md`, batch-confirmed writes via `/tackle-retro`, directive amendments.
- Hygiene and guards: harness-agnostic conventions, no script shipping.
- Maker/checker completion + subagent policy (mandatory in execution, optional-recommended in planning).
- `/tackle-pulse` standing-loop digest for schedulers.
- Autonomy ladder L1/L2/L3 with production-path cap at L2.
- Internal composability: commands are entry points, not boundaries.

## Tackle 2.1.1

- Added `/tackle-ground` command to mechanically read and record every cited `file:line`.
- Added concrete HIGH/MEDIUM/LOW certainty-level examples to the verify guide.
- Hardened gitignore decision recording: requires a `D-xx` in `decisions.md` when not adding to `.gitignore`.
- Added harness map to `AGENTS.tmpl.md` so workspaces record their concrete tool bindings.
- Updated execution loop: cold-session modes must read `board.md`, `log.md`, and `decisions.md` before acting.

## Tackle 2.1.0

- Added grounding gate: points are ungrounded until every cited `file:line` is read.
- Added `/tackle-verify` red-team pass with certainty levels, detection-before-judgment, and plan-vs-code drift check.
- Added right-size/collapse pass; default small slices to lite-plan.
- Added source-of-truth trace field to points and spec/constitution templates.
- Enforced literal command + pass condition for every done-signal.
- Clarified `board.md` as the single canonical source of status.
- `/tackle-plan` now explicitly asks about `docs/plans/` gitignore.
- Strengthened harness/LLM agnosticism guard.
- Revised team protocol with a dedicated Verifier/Red-Teamer role and pre-wave verification gate.
- Added v2.0 → v2.1.0 migration checklist.

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
