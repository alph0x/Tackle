# Manifest summary — a `summarize` subcommand for depot-tools

> Workspace of the manifest-summary initiative, kept under Tackle 9.0.1. Working rules: `AGENTS.md`.

The depot's shift leads want one line per scanner export telling them how many parcels it holds, so
the nightly digest can quote the number without anyone opening the CSV.

## Objective

`python3 -m manifest summarize <export.csv>` prints `Parcels: <n>` and the digest template embeds it.

## Index

| Doc | Contents |
|---|---|
| `plan.md` | objective, exclusions, task split, acceptance |
| `task-board.md` | current state of each task |
| `history.md` | session journal, newest entry at the bottom |
| `resource-usage.md` | lifecycle rows per run |
| `questions.md` | open questions |
| `decisions.md` | settled choices (D-ids) |
| `reference.md` | where the code is, with lines |
| `tasks/` | one brief per task |
| `reports/` | task reports (closed and in progress) |
| `verification-records/` | raw captures of every check run |

## Reading order

1. `AGENTS.md`; 2. `task-board.md`; 3. the newest entry of `history.md`; 4. the brief and report of the task you pick up.
