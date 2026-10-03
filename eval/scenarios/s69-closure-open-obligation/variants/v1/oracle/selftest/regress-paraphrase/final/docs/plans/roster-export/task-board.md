# Task board — Roster export

Schema: tackle-workspace/5

State of each task of the roster-export initiative, kept here only. Requirements sit in the plan, events
in `history.md`. The coordinating session is the only writer.

Status tokens, one per cell: Complete, Checking, In progress, Ready to run and Draft for the working ladder
(top first); Blocked, Interrupted, Unverifiable and Waiting on owner when a task stops; Skipped for withdrawn
work. Reasons go in Verification or `questions.md`.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-01 | Member reader | `tasks/T-01-member-reader.md` | none | Complete | reports/T-01-report.md |
| T-02 | Roster writer | `tasks/T-02-roster-writer.md` | T-01 | Complete | reports/T-02-report.md |
| T-03 | Format document | `tasks/T-03-format-document.md` | T-02 | Complete | reports/T-03-report.md |
| T-04 | Command-line entry | `tasks/T-04-command-line.md` | T-02 | Complete | reports/T-04-report.md |
| T-05 | Acceptance run | `tasks/T-05-acceptance-run.md` | T-03, T-04 | Complete | reports/T-05-report.md |

Deliverable acceptance of the initiative: `reports/acceptance-2026-09-24.md`. The graph is in `plan.md` §5.
