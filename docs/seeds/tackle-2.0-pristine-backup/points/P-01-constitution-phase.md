# Point P-01 — Constitution phase

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone. Links are for depth, not prerequisites — EXCEPT a named
> `contract.md` section the point implements, which IS required reading. Tackle plans this point;
> it does not implement it here.

## Status & wiring
**Status**: 🟢 done

**Depends on**: none

- **Touches (write scope)**: `SKILL.md`, `references/sdd/constitution.tmpl.md`.

## Goal (single responsibility — one loop-completable change)
Add the `/tackle-constitution` trigger to Tackle's routing table and create the
`references/sdd/constitution.tmpl.md` template, so the Constitution phase can produce
`docs/plans/<initiative>/constitution.md` as a standalone SDD entry point.
"Done" = the trigger is documented, the template exists with unfilled placeholders only, and
`/tackle-constitution` produces only `constitution.md` with no spec or points.

## Context (grounded)
- `SKILL.md:25` — `/tackle-constitution` is listed in the routing table as **Constitution → produce `docs/plans/<initiative>/constitution.md`**.
- `SKILL.md:96-105` — the Constitution phase algorithm: confirm initiative, create workspace if missing, render `references/sdd/constitution.tmpl.md`, fill placeholders with the user, stop (no spec/points/execution).
- `contract.md:12` — public trigger contract: `/tackle-constitution` or `tackle-constitution` → Constitution phase → output `docs/plans/<initiative>/constitution.md`.
- `references/sdd/constitution.tmpl.md` — the template that renders the constitution artifact; placeholders: `{{PROJECT_NAME}}`, `{{DATE}}`, `{{TITLE}}`, `{{PURPOSE}}`, `{{PRINCIPLES}}`, `{{QUALITY_BAR}}`, `{{NON_GOALS}}`, `{{CONFLICT_RESOLUTION}}`.
- `references/CHANGELOG.md` — records the new phase entry points (handled in P-08).

## Non-goals
- No spec writing in this phase (Specify phase is P-02).
- No point decomposition or plan creation (Plan phase remains the default).
- No execution logic (Implement phase is P-04).
- No local customization tree (`presets/`/`overrides/`) — that is P-06/P-07.

## Recommended approach
1. Add `/tackle-constitution` to the `SKILL.md` routing table (`SKILL.md:25` and the SDD phase entry table `SKILL.md:48`).
2. Document the Constitution phase algorithm in `SKILL.md` §"Constitution phase" (`SKILL.md:96-105`).
3. Create `references/sdd/constitution.tmpl.md` with front matter and sections for purpose, principles, quality bar, non-goals, and conflict resolution.
4. Leave placeholders unfilled; the agent running the phase fills them with the user.
5. Verify the template has no stray literal content that should be a placeholder.

## Alternatives / fallbacks
- **If the trigger name conflicts with an existing skill trigger** → keep `/tackle-constitution`; update `contract.md` and `README.md` to document the canonical form. No fallback needed — the prefix is consistent with the rest of the Tackle 2.0 surface.
- **If the user wants constitution folded into `/tackle-plan`** → reject: the SDD phase entry points are intentionally standalone (see `contract.md` §States & transitions).

## Recommended starting prompt
```text
Resolve Point P-01 (Constitution phase) of the "tackle-2.0" plan.
Repo: ~/Developer/Tackle. Read points/P-01-constitution-phase.md first; it is self-contained.
Do: add the /tackle-constitution trigger to SKILL.md's routing table, document the Constitution phase algorithm, and create references/sdd/constitution.tmpl.md with the required placeholders.
Constraints: do not add spec/plan/execution logic; do not modify other SDD phase templates; preserve all existing triggers.
Acceptance: /tackle-constitution is routable, the template exists with only unfilled placeholders, and the phase produces only constitution.md.
Loop until green: bash docs/plans/tackle-2.0/points/P-01-constitution-phase.md done-signal
```

## Acceptance — the loop's exit gate
- **Done-signal**:
  ```bash
  grep -n "/tackle-constitution" SKILL.md && \
  test -f references/sdd/constitution.tmpl.md && \
  grep -E '\{\{PROJECT_NAME\}\}|\{\{DATE\}\}|\{\{TITLE\}\}|\{\{PURPOSE\}\}|\{\{PRINCIPLES\}\}|\{\{QUALITY_BAR\}\}|\{\{NON_GOALS\}\}|\{\{CONFLICT_RESOLUTION\}\}' references/sdd/constitution.tmpl.md && \
  grep -n "constitution.tmpl.md" SKILL.md
  ```
  → pass = all commands exit 0; `constitution.tmpl.md` contains exactly the 8 placeholders above and no literal hard-coded project content.
- [x] Meets the **universal per-point acceptance** in `plan.md` §4.1 (no regression; SKILL.md explains the new trigger; contract surface recorded in `contract.md`).
- [x] **Correctness** — `/tackle-constitution` routes to the Constitution phase and stops after producing `constitution.md` (verified by `SKILL.md:96-105`).
- [x] **Self-documenting** — the trigger, output, and stop condition are documented in `SKILL.md` and `contract.md`.
- **If it fails →** missing trigger → add it to both routing tables; template missing or malformed → recreate from the placeholder list above; phase doesn't stop correctly → re-read `SKILL.md:96-105` and tighten the stop condition. Self-correct up to the workspace budget (`AGENTS.md`), then STOP + escalate.

## Open questions for this point
- None.

## Definition of Ready (the gates that can FAIL)
- [x] Single responsibility — one change (Constitution trigger + template), no "and".
- [x] No unresolved user-owned questions inside it.
- [x] Loop-ready — the done-signal is a runnable command with an unambiguous pass.
- [x] Cold-agent-resolvable from this file alone.
