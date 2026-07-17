# Point P-04 — Implement phase

> **Status: 🟢 done**  
> Historical record of an implemented point. The committed skill files are the ground truth.

## Status & wiring

**Depends on**: P-03 (Tasks phase) — the execution loop needs the `plan.md §5` decomposition convention and the flattening pattern established by `tasks.tmpl.md`.

**Touches (write scope)**:
- `SKILL.md` — add `/tackle-implement` and `/tackle-next` routing rows and the execution loop algorithm.
- `references/sdd/implement.tmpl.md` — full execution-loop template.
- `references/sdd/next.tmpl.md` — one-step wrapper template.

**Team note**: Pod (Driver + Spec Reader + Quality Guardian + Coordinator) per `strategy.md:18`. This is the riskiest 2.0 change; test it on a throwaway plan before Wave 4 (`strategy.md:40`).

## Goal (single responsibility)

Add `/tackle-implement` and `/tackle-next` triggers and create the `references/sdd/implement.tmpl.md` and `references/sdd/next.tmpl.md` templates, so Tackle can execute a ready plan point-by-point inside the workspace.

## Context (grounded)

- `contract.md:16-17` — public trigger contract: `/tackle-implement` → Implement phase → executed plan + updated `board.md`/`log.md`; `/tackle-next` → Execute next → one executed point + updated board/log.
- `contract.md:31-44` — execution loop surface: read dependency order, pick the next 🔴 point whose dependencies are 🟢 (or none), spawn the point team, run the point's done-signal, update `board.md`, append `log.md`, retry up to the loop budget, and stop on block.
- `SKILL.md:29-30` — routing table rows for `/tackle-implement` and `/tackle-next`.
- `SKILL.md:52-53` — SDD phase/output rows naming `Updated board.md + log.md` as the output for both modes.
- `SKILL.md:73-84` — execution loop algorithm and the note that `board.md` + `log.md` is the canonical state machine.
- `SKILL.md:306-307` — depth-artifact trigger for `team.md` and `board.md` when execution will run.
- `references/sdd/implement.tmpl.md:8-62` — rendered execution plan: how produced, inputs, loop algorithm, guardrails, output contract, and one-step mode reference.
- `references/sdd/next.tmpl.md:8-25` — one-step wrapper: purpose, algorithm, and do-not-continue rule.

## Non-goals

- Do not implement a runtime orchestrator binary; execution is rendered as markdown instructions for the agent team.
- Do not implement `/tackle-tasks` (P-03), `/tackle-checklist` (P-05), or presets/overrides (P-06/P-07).
- Do not rewrite the full `SKILL.md` routing prose or `README.md` (P-08).
- Do not bump the methodology stamp or changelog (P-08).

## Recommended approach (completed)

1. Added `/tackle-implement` and `/tackle-next` to the `SKILL.md` routing table and SDD phase entry-points table.
2. Documented the execution loop in `SKILL.md` (`SKILL.md:73-84`) and the `team.md`/`board.md` depth-artifact triggers (`SKILL.md:306-307`).
3. Created `references/sdd/implement.tmpl.md` with frontmatter (`{{INITIATIVE_NAME}}`, `{{DATE}}`), inputs, execution loop algorithm, guardrails, output contract, and one-step mode reference.
4. Created `references/sdd/next.tmpl.md` as a thin wrapper that reuses the same inputs/guardrails/output contract but executes exactly one ready point and stops.
5. Verified both templates contain the required sections and no orphaned content.

## Alternatives / fallbacks

- **If the user wants `/tackle-next` to be an alias of `/tackle-implement --one` rather than a separate trigger** → keep them separate: the standalone `/tackle-next` trigger is part of the public contract (`contract.md:17`) and matches the spec-kit surface.
- **If `board.md` is missing when the trigger runs** → the template instructs a degraded note suggesting `/tackle-plan` first; the point only needs the templates.

## Recommended starting prompt

```text
Resolve Point P-04 (Implement phase) of the "tackle-2.0" plan.
Repo: ~/Developer/Tackle. Read points/P-04-implement-phase.md first; it is self-contained.
Do: add /tackle-implement and /tackle-next routing to SKILL.md, document the execution loop, and create references/sdd/implement.tmpl.md and references/sdd/next.tmpl.md.
Constraints: do not touch tasks/checklist/init triggers, do not add runtime binaries, keep templates markdown-only.
Acceptance: the done-signal command in points/P-04-implement-phase.md exits 0.
```

## Acceptance — the loop's exit gate

- **Done-signal**:
  ```bash
  grep -E '\| `/tackle-implement` \| \*\*Implement\*\*' SKILL.md && \
    grep -E '\| `/tackle-next` \| \*\*Execute next\*\*' SKILL.md && \
    grep -E '\| Implement \| `/tackle-implement` \| Updated' SKILL.md && \
    grep -E '\| Execute next \| `/tackle-next` \| Updated' SKILL.md && \
    test -f references/sdd/implement.tmpl.md && \
    test -f references/sdd/next.tmpl.md && \
    grep -q '## Execution loop algorithm' references/sdd/implement.tmpl.md && \
    grep -q '## Guardrails' references/sdd/implement.tmpl.md && \
    grep -q '## Output contract' references/sdd/implement.tmpl.md && \
    grep -q '## One-step mode' references/sdd/implement.tmpl.md && \
    grep -q 'Do not continue to the next point' references/sdd/next.tmpl.md
  ```
  → pass = exit 0, all routing rows present, both templates exist, and each contains the required sections.
- [x] Meets the **universal per-point acceptance** in `plan.md` §4.1 (no regression; `SKILL.md` explains the new triggers; contract surface recorded in `contract.md`).
- [x] **Correctness**: `/tackle-implement` executes all ready points in dependency order; `/tackle-next` executes exactly one ready point and stops.
- [x] **Conventions**: templates live in `references/sdd/`, named `*.tmpl.md`, with standard frontmatter placeholders.
- **If it fails →** check `SKILL.md` table format against other phase rows; recreate missing template sections from the descriptions above. Self-correct up to the workspace iteration budget (`AGENTS.md`), then STOP + escalate.

## Open questions for this point

- None.

## Definition of Ready (retrospective)

- [x] Single responsibility: this point only adds the two execution triggers and their templates.
- [x] No open decisions inside it.
- [x] Loop-ready: the done-signal is a runnable shell command with an unambiguous pass.
- [x] Cold-agent-resolvable from this file alone.

---

## Changed files

- Updated:
  - `SKILL.md` — added `/tackle-implement` and `/tackle-next` routing rows, the execution loop algorithm, and the `team.md`/`board.md` depth-artifact triggers.
- Created:
  - `references/sdd/implement.tmpl.md`
  - `references/sdd/next.tmpl.md`

**Done-signal**: 🟢 green.
