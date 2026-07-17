# Point P-09 — Thin SKILL.md

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone.

## Status & wiring

- **Depends on**: P-08 (SKILL.md routing and changelog already in place).
- **Downstream dependents**: none.
- **Touches (write scope)**:
  - `SKILL.md` — rewrite as concise index + routing + core rules + links.
  - `references/GUIDE.md` — new file with the detailed Step-by-Step methodology.
  - `references/README.tmpl.md` — update reading order if needed.
  - `README.md` — top-level summary stays valid.

## Goal (single responsibility)

Reduce `SKILL.md` verbosity without losing usability. Make the first thing an agent reads short enough to fit in context, while keeping the full methodology one link away.

## Context (grounded)

- `SKILL.md` currently has ~470 lines and ~11 detailed Steps.
- Users report it is "very verbose" today.
- The templates (`plan.tmpl.md`, `point.tmpl.md`, `AGENTS.tmpl.md`) already encode much of the procedural detail.
- `contract.md` and `foundations.md` already hold the authoritative surface and grounding.
- `team.md` already documents execution teams.

## Non-goals

- Do not delete any rule, Step, or convention — move them, not drop them.
- Do not change routing behavior or trigger table.
- Do not change template contents or file naming conventions.
- Do not touch `references/sdd/` or `references/presets/`.

## Recommended approach

1. Create `references/GUIDE.md` and move the full Step 1–11 methodology there, preserving structure and anchors.
2. Rewrite `SKILL.md` to contain only:
   - One-paragraph overview.
   - Scope statement.
   - Routing table (triggers → modes).
   - SDD phase entry points table.
   - Template-resolution stack summary.
   - Execution loop one-paragraph summary.
   - 5–7 unbreakable conventions.
   - Links: `references/GUIDE.md` for detailed Steps, `references/AGENTS.tmpl.md` for workspace rules, `team.md` for execution protocol.
3. Keep all old and new triggers intact.
4. Update `references/README.tmpl.md` if its reading order references old `SKILL.md` sections.

## Alternatives / fallbacks

- **If moving everything breaks agent behavior** → keep a medium-sized `SKILL.md` with collapsible sections ("Summary" vs "Full guide").
- **If users prefer the verbose version** → keep `SKILL.md` long but add a `## tl;dr` at the top.

## Recommended starting prompt

```text
Resolve Point P-09 (Thin SKILL.md) of the Tackle 2.0 plan.
Repo: ~/Developer/Tackle. Read points/P-09-thin-skill.md first; it is self-contained.
Do:
1. Move the detailed Step 1–11 methodology from SKILL.md to a new references/GUIDE.md.
2. Rewrite SKILL.md as a concise index: overview, scope, routing table, SDD phase table, template stack, execution loop summary, 5–7 conventions, links to GUIDE.md/AGENTS.tmpl.md/team.md.
3. Keep every trigger and behavior intact.
Constraints: no routing changes, no template changes, no deletion of rules.
Acceptance: SKILL.md < 150 lines; GUIDE.md contains the moved Steps; all triggers still documented.
Loop until green: wc -l SKILL.md | awk '{print $1}' | grep -qE '^[0-9]{1,2}$|^1[0-4][0-9]$|^150$' && test -f references/GUIDE.md && grep -q 'Step 1' references/GUIDE.md && grep -q '/tackle-implement' SKILL.md
```

## Acceptance — the loop's exit gate

- **Done-signal**: `wc -l SKILL.md | awk '{print $1}' | grep -qE '^[0-9]{1,2}$|^1[0-4][0-9]$|^150$' && test -f references/GUIDE.md && grep -q 'Step 1' references/GUIDE.md && grep -q '/tackle-implement' SKILL.md` → pass = exit 0.
- [ ] Meets the **universal per-point acceptance** in `plan.md` §4.1.
- [ ] **Correctness**: every trigger that existed in SKILL.md before P-09 still appears in the thinned version.
- [ ] **No loss**: every Step, convention, and rule from the old SKILL.md appears in `references/GUIDE.md` or remains in SKILL.md.
- [ ] **Usability**: a cold agent can read SKILL.md in one pass and follow links for depth.
- **If it fails →**
  - Line count too high → move more detail to `GUIDE.md`.
  - Missing trigger → add it back to the routing table.
  - Missing Step in GUIDE.md → copy the section from the old SKILL.md.

## Open questions for this point

None.

## Definition of Ready

- [ ] Single responsibility: thin SKILL.md; GUIDE.md holds detail.
- [ ] No open decisions inside it.
- [ ] Loop-ready: done-signal is runnable.
- [ ] Cold-agent-resolvable from this file alone.
