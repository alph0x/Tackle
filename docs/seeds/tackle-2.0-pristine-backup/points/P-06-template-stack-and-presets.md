# Point P-06 — Template-resolution stack + presets

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone. Links are for depth, not prerequisites — EXCEPT `contract.md`
> §Template-resolution stack, which IS required reading.

## Status & wiring

**Depends on**: P-01 (constitution phase + `references/sdd/constitution.tmpl.md`), P-02 (specify phase + `references/sdd/specify.tmpl.md`), P-03 (tasks phase + `references/sdd/tasks.tmpl.md`), P-04 (implement phase + `references/sdd/implement.tmpl.md`), P-05 (checklist phase + `references/sdd/checklist.tmpl.md`) — the stack needs all SDD phase templates to exist before it can reference them as a layer.

- **Status**: 🟢 done
- **Touches (write scope)**:
  - `references/presets/default/*.tmpl.md`
  - `references/sdd/*.tmpl.md` (confirm / align, not add new ones)
  - `SKILL.md` §Template-resolution stack
  - `docs/plans/tackle-2.0/contract.md` §Template-resolution stack
  - `references/CHANGELOG.md`

## Goal (single responsibility)

Define the template-resolution stack (`overrides > presets > sdd > core`) and land the
`references/presets/default/` and `references/sdd/` template trees so later points
(`/tackle-init`, `/tackle-implement`, `SKILL.md` update) have a concrete stack to resolve
against.

## Context (grounded)

- Tackle 2.0 mirrors spec-kit's command surface but keeps everything markdown-first and
  repo-local. Phases before/after planning need templates that are NOT the core planning
  templates in `references/`.
- `SKILL.md:58` documents the stack: `overrides > presets > sdd > core` — first match wins.
- `contract.md:26-30` records the resolution order as a public contract:
  1. `docs/plans/<initiative>/overrides/<name>.tmpl.md`
  2. `docs/plans/<initiative>/presets/<preset>/<name>.tmpl.md`
  3. `references/sdd/<name>.tmpl.md`
  4. `references/<name>.tmpl.md`
- `SKILL.md:69-70` and `contract.md:54-67` state that presets live in
  `references/presets/<preset>/` and are copied plan-locally by `/tackle-init`; overrides
  live in `docs/plans/<initiative>/overrides/` and start empty.
- `references/CHANGELOG.md:7-8` records the stack and visible plan-local customization as
  2.0 features.

## Non-goals

- Do NOT implement `/tackle-init` itself — that is P-07.
- Do NOT update the routing table or write `SKILL.md` 2.0 prose — that is P-08.
- Do NOT add new non-default presets (e.g. `web`, `api`) unless explicitly requested later.
- Do NOT install anything at the repo root.

## Recommended approach

1. Create `references/sdd/` and add phase templates that wrap/extend the base planning
   templates:
   - `constitution.tmpl.md`, `specify.tmpl.md`, `tasks.tmpl.md`, `implement.tmpl.md`,
     `next.tmpl.md`, `checklist.tmpl.md`
2. Create `references/presets/default/` with the full default workspace template set so
   `/tackle-init` has a preset to copy:
   - `README.tmpl.md`, `lite-plan.tmpl.md`, `AGENTS.tmpl.md`, `team.tmpl.md`,
     `board.tmpl.md`, `todo.tmpl.md`, `decisions.tmpl.md`, `design-contract.tmpl.md`,
     `execution-strategy.tmpl.md`, `external-question.tmpl.md`, `foundations.tmpl.md`,
     `log.tmpl.md`, `plan.tmpl.md`, `point.tmpl.md`, `questions.tmpl.md`,
     `reference-docs-README.tmpl.md`, `reference.tmpl.md`
3. Add the stack rule to `SKILL.md` §Template-resolution stack and `contract.md` §Template
   resolution.
4. Verify the four layers are documented and the default + SDD trees are complete.

## Alternatives / fallbacks

- **If a preset file is missing when `/tackle-init` runs** → fall back to
  `references/presets/default/` (documented in `SKILL.md:94` and `contract.md:86`).
- **If a template is missing in `references/sdd/`** → fall back to `references/` (core
  templates), since the stack's bottom layer is the core tree.

## Recommended starting prompt

```text
Resolve Point P-06 (Template-resolution stack + presets) of the "Tackle 2.0" plan.
Repo: ~/Developer/Tackle. Read points/P-06-template-stack-and-presets.md first; it is self-contained.

Do:
1. Create references/sdd/ with the SDD phase templates (constitution, specify, tasks, implement, next, checklist).
2. Create references/presets/default/ with the full default workspace template set.
3. Document the resolution stack (overrides > presets > sdd > core) in SKILL.md and contract.md.

Constraints: no new dependencies, no repo-root files, preserve existing triggers, no new presets beyond default.
Acceptance: done-signal passes.
Loop until green: test -d references/presets/default && test -d references/sdd && grep -q "overrides > presets > sdd > core" SKILL.md && grep -q "Template-resolution stack" docs/plans/tackle-2.0/contract.md
```

## Acceptance — the loop's exit gate

- **Done-signal**:
  ```bash
  test -d references/presets/default && \
  test -d references/sdd && \
  grep -q 'overrides > presets > sdd > core' SKILL.md && \
  grep -q '1. `docs/plans/<initiative>/overrides/<name>.tmpl.md`' docs/plans/tackle-2.0/contract.md && \
  grep -q '2. `docs/plans/<initiative>/presets/<preset>/<name>.tmpl.md`' docs/plans/tackle-2.0/contract.md && \
  grep -q '3. `references/sdd/<name>.tmpl.md`' docs/plans/tackle-2.0/contract.md && \
  grep -q '4. `references/<name>.tmpl.md`' docs/plans/tackle-2.0/contract.md && \
  find references/presets/default -name '*.tmpl.md' | wc -l | grep -q '17' && \
  find references/sdd -name '*.tmpl.md' | wc -l | grep -q '6'
  ```
  → pass = exit 0, 17 default preset templates, 6 SDD phase templates, stack documented in
  both files (shorthand in `SKILL.md`, ordered list in `contract.md`).
- [ ] Meets the **universal per-point acceptance** in `plan.md` §4.1.
- [ ] **Correctness**: resolution order is `overrides > presets > sdd > core` everywhere it
  appears and matches `contract.md`.
- [ ] **Completeness**: every base planning template referenced by the SDD phases has a
  corresponding phase-specific or preset template, or a documented fallback to core.
- **If it fails →** fix the missing template or documentation gap, re-run. If the count is
  wrong, compare to the lists in this briefing.

## Open questions for this point

- None.

## Definition of Ready (the gates that can FAIL)

- [x] **Single responsibility**: defines the stack and lands the two template trees; init logic is out of scope.
- [x] **No open decisions inside it**: all design choices recorded in `contract.md`.
- [x] **Loop-ready**: done-signal is a runnable shell command with an unambiguous pass (count-asserted).
- [x] **Cold-agent-resolvable from this file alone**.

---

## Changed files

- Created:
  - `references/sdd/constitution.tmpl.md`
  - `references/sdd/specify.tmpl.md`
  - `references/sdd/tasks.tmpl.md`
  - `references/sdd/implement.tmpl.md`
  - `references/sdd/next.tmpl.md`
  - `references/sdd/checklist.tmpl.md`
  - `references/presets/default/README.tmpl.md`
  - `references/presets/default/lite-plan.tmpl.md`
  - `references/presets/default/AGENTS.tmpl.md`
  - `references/presets/default/team.tmpl.md`
  - `references/presets/default/board.tmpl.md`
  - `references/presets/default/todo.tmpl.md`
  - `references/presets/default/decisions.tmpl.md`
  - `references/presets/default/design-contract.tmpl.md`
  - `references/presets/default/execution-strategy.tmpl.md`
  - `references/presets/default/external-question.tmpl.md`
  - `references/presets/default/foundations.tmpl.md`
  - `references/presets/default/log.tmpl.md`
  - `references/presets/default/plan.tmpl.md`
  - `references/presets/default/point.tmpl.md`
  - `references/presets/default/questions.tmpl.md`
  - `references/presets/default/reference-docs-README.tmpl.md`
  - `references/presets/default/reference.tmpl.md`
- Updated:
  - `SKILL.md` — added §Template-resolution stack
  - `docs/plans/tackle-2.0/contract.md` — added template-resolution order and local customization layout
  - `references/CHANGELOG.md` — recorded the stack and visible plan-local customization

**Done-signal**: 🟢 green.
