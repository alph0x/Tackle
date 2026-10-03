# Task board — Price notice

Schema: tackle-workspace/5

Where each task of the price-notice initiative stands. This table is the single home of task state; the
plan carries requirements, `history.md` the sequence of events. Only the session that coordinates a run
edits it.

One token per Status cell. Working states, top first: Complete, Checking, In progress, Ready to run,
Draft. Halted states: Blocked, Interrupted, Unverifiable, Waiting on owner. Skipped marks work the owner
pulled. Detail belongs in Verification or `questions.md`.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-01 | Draft the notice | `tasks/T-01-draft-notice.md` | none | Complete | reports/T-01-report.md |
| T-02 | Refresh the member list | `tasks/T-02-member-list.md` | none | Complete | reports/T-02-report.md |
| T-03 | Relay dry run | `tasks/T-03-relay-dry-run.md` | none | Complete | reports/T-03-report.md |
| T-04 | Wording approval | `tasks/T-04-wording-approval.md` | T-01 | Complete | reports/T-04-report.md |
| T-05 | Dispatch the notice | `tasks/T-05-dispatch.md` | T-02, T-03, T-04 | In progress | run 2026-09-30-s8/T-05/executor/1; report `reports/T-05-report.md` started |
| T-06 | Archive the season | `tasks/T-06-archive-season.md` | T-05 | Draft | after T-05 |

The graph is in `plan.md` §5.
