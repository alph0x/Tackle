# {{TITLE}} (lite) — **Methodology: Tackle 3.4.1**

Lite workspace: `plan.md` + `log.md` + `todo.md`. Default to Lite for small slices; upgrade to Full only when multi-session, multi-track, or handoff is expected. Upgrade adds `README.md`, `AGENTS.md`, `reference.md`, `points/` (and depth artifacts as their triggers fire — `foundations.md`, `design-contract.md`, `execution-strategy.md`, `team.md`, `board.md`; see Step 4).

**Lite is non-trivial.** A task must fail the triviality gate (one file, <10 lines, no new behavior, no searching) before it earns a Lite workspace; otherwise execute it directly.

Cross-cutting rules still apply at Lite: no silent assumptions, self-documenting code, and a runnable done-signal per point.

## Objective
{{What is achieved, observable.}}

## Non-goals
- {{What it does NOT do.}}

## Current state (grounded)
- **Key finding**: {{the one fact that shapes the risk, if any}} · **Mirrors**: {{the local pattern/file this follows}}.
- `{{path:NN}} — "{{literal fragment}}"` — {{what exists today}}. Fragment = verbatim substring of line NN; anchored citations apply at Lite too.

## Steps
1. {{...}}
2. Tests: {{what is covered}}

## Open questions / decisions
- {{Q — doubt + recommended default + who decides; or "none — fully specified". Don't assume silently.}}

## Rollout / reversibility (only if it touches a production path)
- {{flag default-off · no-op when off · how to revert; delete this section if not production-facing}}

## Acceptance — the done-signal (exit gate)
- **Run**: `{{the literal command — test / mock / smoke / grep}}` → pass = {{exact condition: exit code, count, or output match}}.
- [ ] {{observable condition — exhaustive over its case set where one exists}}.
- [ ] Self-documenting: no explanatory inline comments; doc-comments on any public surface only.
