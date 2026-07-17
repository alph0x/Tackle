# Point P-05 — Checklist phase

> **Status: 🟢 done**  
> Historical record of an implemented point. The committed skill files are the ground truth.

## Status & wiring
- **Depends on**: none
- **Touches**: `SKILL.md`, `references/sdd/checklist.tmpl.md`
- **Changed files**: `SKILL.md`, `references/sdd/checklist.tmpl.md`

## Goal (single responsibility)
Add the `/tackle-checklist` trigger and a `references/sdd/checklist.tmpl.md` template so Tackle can generate a custom quality checklist from a selected source artifact (`spec.md`, `plan.md`, or another plan file under `docs/plans/<initiative>/`).

## Context (grounded)
- Tackle 2.0 adds SDD phases before and after the core planning loop. After a plan exists, a team needs a structured quality pass before or during execution.
- `SKILL.md` §Routing (`SKILL.md:31`, `SKILL.md:54`) defines `/tackle-checklist` as mode **Checklist** producing `docs/plans/<initiative>/checklist.md`.
- `references/sdd/checklist.tmpl.md` defines the five quality dimensions (Security, Performance, Concurrency, Correctness, Conventions & Style), each with review prompts, a runnable-fragment placeholder, and a skip reason.
- The template includes a degraded-source-path fallback: if `{{SOURCE_PATH}}` does not exist, the generated `checklist.md` still lists the five dimensions and asks the user to point to a real `spec.md` or `plan.md`.
- Implements the **Checklist** row in `contract.md` §Signatures / API surface (`contract.md:18`, `contract.md:77`).

## Non-goals
- Does not implement an automated rendering engine; Tackle agents render the template by hand per `SKILL.md`.
- Does not add the template-resolution stack itself (P-06) or the plan-local customization bootstrapper (P-07).
- Does not auto-generate a checklist inside `/tackle-implement`; the checklist phase is a standalone trigger.
- Does not add new presets or overrides.

## Recommended approach (completed)
1. Added `/tackle-checklist` to the `SKILL.md` routing table and the SDD phase entry-points table.
2. Created `references/sdd/checklist.tmpl.md` with frontmatter placeholders (`{{INITIATIVE_NAME}}`, `{{DATE}}`, `{{SOURCE_PATH}}`), five quality-dimension sections, runnable-fragment placeholders, and the degraded-source-path note.
3. Verified the template has no orphaned `{{PLACEHOLDER}}` blocks that should have been deleted.

## Alternatives / fallbacks
- **If a repo needs a different quality dimension set** → drop an override at `docs/plans/<initiative>/overrides/checklist.tmpl.md` (P-06/P-07).
- **If the source artifact is missing** → produce the degraded checklist that asks for `spec.md` or `plan.md`, per the template's own instruction.

## Recommended starting prompt
```text
Resolve Point P-05 (Checklist phase) of the "tackle-2.0" plan.
Repo: ~/Developer/Tackle. Read points/P-05-checklist-phase.md first; it is self-contained.
Do: add /tackle-checklist to SKILL.md routing and create references/sdd/checklist.tmpl.md covering Security, Performance, Concurrency, Correctness, and Conventions.
Constraints: do not touch the template-resolution stack (P-06) or presets (P-07); keep the phase standalone.
Acceptance: the done-signal command in points/P-05-checklist-phase.md exits 0.
```

## Acceptance — the loop's exit gate
- **Done-signal**:
  ```bash
  test -f references/sdd/checklist.tmpl.md && \
    grep -q '/tackle-checklist' SKILL.md && \
    grep -q 'Security' references/sdd/checklist.tmpl.md && \
    grep -q 'Performance' references/sdd/checklist.tmpl.md && \
    grep -q 'Concurrency' references/sdd/checklist.tmpl.md && \
    grep -q 'Correctness' references/sdd/checklist.tmpl.md && \
    grep -q 'Conventions' references/sdd/checklist.tmpl.md
  ```
  → pass = exit 0.
- [x] Meets the universal per-point acceptance in `plan.md` §4.1 (no new dependencies, markdown-only, self-documenting).
- [x] `SKILL.md` routing table lists `/tackle-checklist` with the correct mode and output.
- [x] `references/sdd/checklist.tmpl.md` covers the five quality dimensions and includes the degraded-source-path instruction.
- **If it fails →** check that `SKILL.md` and `references/sdd/checklist.tmpl.md` were not reverted by the clean rebase in session 12; restore them from `main` if needed.

## Open questions for this point
- none

## Definition of Ready (retrospective)
- [x] Single responsibility: this point only adds the checklist trigger + template.
- [x] No open decisions inside it.
- [x] Loop-ready: the done-signal is a runnable command with an unambiguous pass.
- [x] Cold-agent-resolvable from this file alone.
