# Action plan — Tackle 2.0

## 1. Objective

Make Tackle a lightweight, model-agnostic, specification-driven planning + execution workflow that agents can run end-to-end inside any repository: establish project principles (`constitution`), write product specs (`specify`), produce a technical plan (`plan`), decompose into tasks (`tasks`), execute the plan (`implement`), and validate quality (`checklist`).

## 2. Current state

See `reference.md` for the exact `SKILL.md` routing table, template inventory, and the Tackle 1.5 file structure.

**Key finding (verified):** Tackle 1.5 already has the core planning engine: gate sizing, point briefings with runnable done-signals, dependency graphs, and a lint step. The missing layer is entry points before planning (`constitution`/`specify`), exit points after planning (`tasks`/`implement`/`checklist`), and execution of the plan itself.

**Precedent we mirror:** spec-kit's command surface (`/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.checklist`) and its template-resolution stack. We adapt the shape to Tackle's markdown-first, repo-local model.

## 3. Point decomposition

See `board.md` for the canonical status board and dependency graph.

## 4. Acceptance criteria

### 4.1 Universal per-point acceptance

- [ ] Tests/docs green: markdown lint / link check passes; templates render without unfilled placeholders.
- [ ] No new external dependencies: stays markdown + optional POSIX shell.
- [ ] Self-documenting: `SKILL.md` explains every new trigger and template.
- [ ] Contract conformance: any new public surface (trigger word, template file name, preset layout) is recorded in `contract.md`.
- [ ] No regression: existing `tackle this`, `plan de acción`, resume/status/list/next/migrate/improve triggers keep working.
- [ ] Board hygiene: `board.md` + `log.md` updated per point.

### 4.2 Initiative-level acceptance

- [ ] A user can run the full SDD chain: `/tackle-init` → `/tackle-constitution` → `/tackle-specify` → `/tackle-plan` → `/tackle-tasks` → `/tackle-implement`.
- [ ] `/tackle-implement` executes points in dependency order and updates `board.md` + `log.md`.
- [ ] A user can still run only `/tackle-plan` (or the old trigger) and get the same 1.5-style workspace.
- [ ] `SKILL.md` 2.0 is the single source of truth; `README.md` summarizes it for humans.
- [ ] `references/CHANGELOG.md` records 2.0 changes and bumps the methodology stamp everywhere it appears.
- [ ] A Tackle 1.5 plan can be migrated to the 2.0 layout via `/tackle-migrate`.

## 5. Risks / dependencies

See `context.md` §Risks.
