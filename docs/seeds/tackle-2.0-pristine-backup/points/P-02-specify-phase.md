# Point P-02 — Specify phase

**Status:** 🟢 done

> Self-contained briefing for the Specify SDD phase. A fresh agent can resolve this point from this file alone.

## Status & wiring

- **Depends on**: none.
- **Touches (write scope)**:
  - `SKILL.md` — add `/tackle-specify` to the routing table and add the **Specify mode** section.
  - `references/sdd/specify.tmpl.md` — new template for product specs.
- **Changed files**:
  - `SKILL.md`
  - `references/sdd/specify.tmpl.md`

## Goal

Add a standalone `/tackle-specify` trigger that produces `docs/plans/<initiative>/spec.md` from `references/sdd/specify.tmpl.md`, and provide the template with the required placeholders.

## Context

- Tackle 2.0 mirrors spec-kit's SDD phase surface: `/tackle-constitution`, `/tackle-specify`, `/tackle-plan`, `/tackle-tasks`, `/tackle-implement`, `/tackle-checklist`.
- `SKILL.md:26` routes `/tackle-specify` → **Specify** → `docs/plans/<initiative>/spec.md`.
- `SKILL.md:49` lists Specify in the SDD phase entry table.
- `SKILL.md:108-115` defines the Specify mode steps: confirm initiative, create workspace if needed, render template, fill placeholders, stop.
- `references/sdd/specify.tmpl.md` is the template source for the spec artifact.
- This point implements the Specify row in `contract.md` and the trigger row in `reference.md`.

## Non-goals

- No plan decomposition (that's `/tackle-plan`, P-06..P-08).
- No task checklist generation (that's `/tackle-tasks`, P-03).
- No execution loop (that's `/tackle-implement`, P-04).
- No preset/override/template-resolution logic (that's P-06/P-07).

## Recommended approach

1. In `SKILL.md`, add `/tackle-specify` to:
   - the main routing table (`SKILL.md:26`),
   - the SDD phase entry table (`SKILL.md:49`),
   - a new **Specify mode** subsection (`SKILL.md:106-115`) describing the 5-step flow.
2. Create `references/sdd/specify.tmpl.md` with placeholders for: what is being built, why it matters, non-goals, user stories, acceptance criteria, open questions, references.
3. Run the done-signal below.

## Alternatives / fallbacks

- **If the template should include additional sections** → add them as optional placeholders and document them in the Specify mode section; do not change the phase contract.
- **If the user wants `/tackle-specify` to auto-generate content** → defer to `/tackle-plan`; Specify is intentionally a capture phase, not a generation phase.

## Recommended starting prompt

```text
Resolve Point P-02 (Specify phase) of the "tackle-2.0" plan.
Repo: ~/Developer/Tackle. Read points/P-02-specify-phase.md first; it is self-contained.
Do: add the /tackle-specify trigger to SKILL.md and create references/sdd/specify.tmpl.md.
Constraints: no plan decomposition, no tasks, no execution loop, no preset logic.
Acceptance: the done-signal command exits 0.
Loop until green: bash docs/plans/tackle-2.0/points/P-02-specify-phase.md#done-signal
```

## Acceptance — the loop's exit gate

- **Done-signal**:
  ```bash
  test "$(grep -cF '| `/tackle-specify` | **Specify** →' SKILL.md)" -eq 1 && \
  test "$(grep -cF '| Specify | `/tackle-specify` |' SKILL.md)" -eq 1 && \
  test -f references/sdd/specify.tmpl.md && \
  grep -q '{{What is being built}}' references/sdd/specify.tmpl.md && \
  grep -q '{{Why it matters}}' references/sdd/specify.tmpl.md && \
  grep -q '{{User stories}}' references/sdd/specify.tmpl.md && \
  grep -q '{{Acceptance criteria}}' references/sdd/specify.tmpl.md && \
  grep -q '## Specify mode' SKILL.md
  ```
  → pass = all checks exit 0.
- [x] Meets the **universal per-point acceptance** in `plan.md` §4.1.
- [x] Routing: exactly one `/tackle-specify` row in the main routing table and exactly one row in the SDD phase table.
- [x] Template: `references/sdd/specify.tmpl.md` exists and contains the required placeholders.
- [x] No regression: `/tackle-plan` and legacy triggers remain unchanged.

## Open questions for this point

None.

## Definition of Ready

- [x] **Single responsibility**: this point only adds the Specify trigger and its template.
- [x] **No open decisions inside it**: none.
- [x] **Loop-ready**: the done-signal is a runnable shell command with an unambiguous pass.
- [x] **Cold-agent-resolvable from this file alone**.
