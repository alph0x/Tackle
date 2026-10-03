# Zone rollup — per-zone temperatures for the growers' sheet

> Workspace of the zone-rollup initiative (Tackle 9.0.1). Working agreements: `AGENTS.md`.

Brackenfield's growers fill a weekly sheet with the mean temperature of each glasshouse zone. Today
they compute it by hand from the logger export; `rollup` should print it.

## Objective

`python3 -m rollup zones <readings.csv>` prints one CSV row per zone, and the weekly sheet imports it.

## Index

| Doc | Contents |
|---|---|
| `plan.md` | objective, exclusions, task split, acceptance |
| `task-board.md` | state of each task |
| `history.md` | session journal, newest last |
| `resource-usage.md` | lifecycle rows per run |
| `questions.md` | questions, open and resolved |
| `decisions.md` | settled choices (D-ids) |
| `reference.md` | code map with lines |
| `tasks/` | one brief per task |
| `reports/` | task reports |
| `verification-records/` | raw captures of check runs |

## Reading order

`AGENTS.md`, then `task-board.md`, then the newest `history.md` entry, then the brief and report of the task in hand.
