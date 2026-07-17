# Tackle 2.0 — specification-driven planning + execution

> **Methodology: Tackle 2.0.** See `AGENTS.md` for the workspace contract.

Tackle 2.0 extends Tackle from a planning-only skill into a specification-driven planning + execution workflow that agents run end-to-end inside a repo.

## Status

Canonical state: **last entry in `log.md`**. Board: **`board.md`**.

One-line summary: `PLAN — COMPLETE`.

## What lives where

| Doc | Read this for |
|---|---|
| `AGENTS.md` | Rules of the workspace for any agent or human. |
| `context.md` | Objective, expected result, non-goals, risks. |
| `contract.md` | Authoritative surface: triggers, states, errors, invariants. |
| `foundations.md` | Grounding: decision → principle → source. |
| `plan.md` | Point decomposition + acceptance criteria. |
| `strategy.md` | Waves, quality gates, deferral. |
| `team.md` | Execution team roles and protocol. |
| `board.md` | Canonical status board (`plan.md` §5). |
| `log.md` | Append-only session log (canonical state source). |
| `todo.md` | Planning-readiness checklist. |
| `questions.md` | Open questions (single source). |
| `decisions.md` | Closed decisions register. |
| `reference.md` | Current code state with `file:line`. |
| `points/` | One self-contained `.md` per point. |
| `snapshots/` | Read-only external/reference snapshots (optional). |

## Reading order (new agent / human)

1. `AGENTS.md` — rules.
2. `context.md` — why we are doing this.
3. `contract.md` — what the public surface is.
4. `team.md` — how execution teams work.
5. `plan.md` + `board.md` — what needs to be done and where it stands.
6. `strategy.md` — how to attack it.
7. `decisions.md` / `questions.md` — what's settled / still open.
8. The relevant `points/P-0N-*.md` — the work you're picking up.

## Next step

All points are 🟢 done. The skill is implemented in `SKILL.md` and `references/`.
