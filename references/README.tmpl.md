# {{TITLE}} — {{one line: what this is}}

> **Methodology: Tackle 8.4.1.** See `AGENTS.md` for the workspace contract.

{{2-3 line description: what this initiative solves.}}

<!-- If this is a sibling of another plan, link it and reuse its shared docs instead of duplicating. -->

## Related tickets
<!-- Delete this section if not applicable. -->

| Ticket | What | Status |
|---|---|---|
| {{TICKET-ID}} | {{...}} | {{...}} |

## Objective

{{What the initiative delivers to its users — observable.}}


## Index

| Doc | Contents |
|---|---|
| `plan.md` | Objective, non-goals, task decomposition, acceptance criteria, risks |
| `task-board.md` | Canonical current task state |
| `history.md` | Append-only history (current state is in task-board.md) |
| `resource-usage.md` | Lifecycle and resource-usage ledger |
| `questions.md` | Open questions (single source) |
| `decisions.md` | Closed decisions register (`D-01`…, don't revisit without cause) |
| `reference.md` | Current code state with `file:line` |
| `tasks/` | One self-contained `.md` per task (goal, approach, prompt, alternatives) |
| `AGENTS.md` | Workspace conventions |
<!-- Add the lines below only for the artifacts you actually created (delete the rest):
| `design-contract.md` | Authoritative API/state/error surface tasks implement |
| `foundations.md` | Reference verification: decision → principle → source |
| `reference-docs/` | Read-only snapshots of external material (+ provenance) |
| `external-questions/` | Packets sent to other teams |
Add appendices here too (descriptive name, not numbered). -->

## Reading order (new agent / human)

1. `AGENTS.md` — rules of the workspace.
2. `plan.md` — objective, non-goals, task decomposition.
3. `task-board.md` — current state of every task; `history.md` for how it got there.
4. `decisions.md` / `questions.md` — what's settled / still open.
5. The relevant `tasks/T-0N-*.md` — self-contained brief for the work you're picking up.

## Next step

{{Use STATUS for a read-only digest or next selection. Use RUN only after explicit execution intent.}}
