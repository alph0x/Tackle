# Task board — Overdue notices

Schema: tackle-workspace/5

State of each task of the overdue-notices initiative, kept here only. Requirements sit in the plan,
events in `history.md`. The coordinating session is the only writer.

Status tokens, one per cell: Complete, Checking, In progress, Ready to run and Draft for the working ladder
(top first); Blocked, Interrupted, Unverifiable and Waiting on owner when a task stops; Skipped for withdrawn
work. Reasons go in Verification or `questions.md`.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-01 | Loan reader | `tasks/T-01-loan-reader.md` | none | Complete | reports/T-01-report.md |
| T-02 | Notice template | `tasks/T-02-notice-template.md` | T-01 | Complete | reports/T-02-report.md |
| T-03 | Render command | `tasks/T-03-render-command.md` | T-02 | Complete | reports/T-03-report.md |
| T-04 | Acceptance run | `tasks/T-04-acceptance-run.md` | T-03 | Complete | reports/T-04-report.md |

Deliverable acceptance of the initiative: `reports/acceptance-2026-09-29.md`. The graph is in `plan.md` §5.
