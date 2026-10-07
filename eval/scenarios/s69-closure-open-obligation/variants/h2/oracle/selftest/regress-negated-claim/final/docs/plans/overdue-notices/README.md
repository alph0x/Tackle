# Overdue notices — one plain-text notice per patron

> Workspace of the overdue-notices initiative (Tackle 9.0.1). Agreements: `AGENTS.md`.

The desk staff wrote overdue reminders by hand from the circulation export every Monday; patrons got
them late or not at all.

## Objective

`python3 -m notices render <loans.json> <YYYY-MM-DD> <outdir>` writes the agreed notices, documented and
accepted.

## Index

| Doc | Contents |
|---|---|
| `plan.md` | objective, exclusions, task split |
| `task-board.md` | state of each task |
| `history.md` | session journal, newest last |
| `resource-usage.md` | lifecycle rows per run |
| `questions.md`, `decisions.md` | questions; settled choices |
| `reference.md` | code map |
| `tasks/`, `reports/`, `verification-records/` | briefs, task reports, raw check captures |

## Reading order

`AGENTS.md` → `task-board.md` → newest `history.md` entry → the briefs and reports.
