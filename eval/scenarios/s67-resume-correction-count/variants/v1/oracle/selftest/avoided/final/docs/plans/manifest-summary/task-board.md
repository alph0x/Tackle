# Task board — Manifest summary

Schema: tackle-workspace/5

Current state of every task of the manifest-summary initiative. This table is the one place a task's
state is kept; the plan holds requirements and `history.md` records what happened when. Only the
coordinating session edits it.

Status tokens, one per cell: Complete, Checking, In progress, Ready to run and Draft for the working ladder
(top first); Blocked, Interrupted, Unverifiable and Waiting on owner when a task stops; Skipped for withdrawn
work. Reasons go in Verification or `questions.md`.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-01 | Parse export rows | `tasks/T-01-parse-rows.md` | none | Complete | reports/T-01-report.md |
| T-02 | Fixture set | `tasks/T-02-fixture-set.md` | T-01 | Complete | reports/T-02-report.md |
| T-03 | Summarize subcommand | `tasks/T-03-summarize.md` | T-02 | Blocked | reports/T-03-report.md |
| T-04 | Digest line | `tasks/T-04-digest-line.md` | T-03 | Draft | waits for T-03 |

The dependency graph stays in `plan.md` §5.
