# {{TITLE}} — {{one line: what this is}}

{{2-3 line description: what this initiative solves.}}

<!-- If this is a sibling of another plan, link it and reuse its shared docs instead of duplicating. -->

## Related tickets
<!-- Delete this section if not applicable. -->

| Ticket | What | Status |
|---|---|---|
| {{MBTX-XXXX}} | {{...}} | {{...}} |

## Objective

{{What the SDK exposes/delivers to the integrator or user — observable.}}

## Status

Canonical source: **last entry in `log.md`**. One-line summary: `{{PLAN — DRAFT}}`.

## Index

| Doc | Contents |
|---|---|
| `plan.md` | Objective, non-goals, point decomposition, acceptance criteria, risks |
| `log.md` | Append-only session log (canonical state) |
| `todo.md` | Planning-readiness checklist per point |
| `questions.md` | Open questions (single source) |
| `decisions.md` | Closed decisions register (`D-01`…, don't revisit without cause) |
| `reference.md` | Current code state with `file:line` |
| `points/` | One self-contained `.md` per point (goal, approach, prompt, alternatives) |
| `AGENTS.md` | Workspace conventions |
<!-- Add appendices here when created (descriptive name, not numbered). -->

## Reading order (new agent / human)

1. `AGENTS.md` — rules of the workspace.
2. `plan.md` — objective, non-goals, point decomposition.
3. `log.md` (newest entry's State snapshot) — where it stands.
4. `decisions.md` / `questions.md` — what's settled / still open.
5. The relevant `points/P-0N-*.md` — self-contained brief for the work you're picking up.

## Next step

{{What to do when resuming — point to the last log entry / blocking questions.}}
