# {{TITLE}} (lite)

<!-- Methodology: Tackle 1.5 — the version this plan was built/migrated under (Lite has no AGENTS.md, so the stamp lives here; Step 8.5 / Step 10 reads it). -->

Lite workspace: this `plan.md` + `log.md` + `todo.md`. If it grows to multi-session or
multi-track, upgrade to Full: add `README.md`, `AGENTS.md`, `reference.md`, `points/` (+ the
depth artifacts as their triggers fire — see Step 4). The cross-cutting rules still apply at Lite,
without the Full artifacts: **no silent assumptions**, **self-documenting code**, and a
**runnable done-signal** (each enforced in its section below).

## Objective
{{What is achieved, observable.}}

## Non-goals
- {{What it does NOT do.}}

## Current state (grounded)
- **Key finding**: {{the one fact that shapes the risk, if any}} · **Mirrors**: {{the local pattern/file this follows}}.
- `{{path:NN}}` — {{what exists today}}.

## Steps
1. {{...}}
2. Tests: {{what is covered}}

## Open questions / decisions
- {{Q — doubt + recommended default + who decides; or "none — fully specified". Don't assume silently.}}

## Rollout / reversibility (only if it touches a production path)
- {{flag default-off · no-op when off · how to revert; delete this section if not production-facing}}

## Acceptance — the done-signal (exit gate)
- **Run**: `{{the exact command — test / mock / smoke}}` → pass = {{exit 0 / expected result}}.
- [ ] {{observable condition — exhaustive over its case set where one exists}}.
- [ ] Self-documenting: no explanatory inline comments; doc-comments on any public surface only.
