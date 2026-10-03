# Roster export — a CSV for the regatta registration desk

> Workspace of the roster-export initiative (Tackle 9.0.1). Agreements: `AGENTS.md`.

The regatta desk needs the club roster as a CSV in an agreed format before each regatta; until now the
secretary pasted it together by hand.

## Objective

`python3 -m export roster <members.json> <out.csv>` writes the agreed export, documented and accepted.

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

`AGENTS.md` → `task-board.md` → newest `history.md` entry → the reports.
