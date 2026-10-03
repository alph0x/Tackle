# Task board — Zone rollup

Schema: tackle-workspace/5

Where each task of the zone-rollup initiative stands. This table is the single home of task state; the
plan carries requirements, `history.md` the sequence of events. Only the session that coordinates a run
edits it.

One token per Status cell. Working states, top first: Complete, Checking, In progress, Ready to run,
Draft. Halted states: Blocked, Interrupted, Unverifiable, Waiting on owner. Skipped marks work the owner
pulled. Detail belongs in Verification or `questions.md`.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-01 | Readings reader | `tasks/T-01-readings-reader.md` | none | Complete | reports/T-01-report.md |
| T-02 | Sheet import contract | `tasks/T-02-sheet-contract.md` | T-01 | Complete | reports/T-02-report.md |
| T-03 | Export rotation | `tasks/T-03-export-rotation.md` | none | Complete | reports/T-03-report.md |
| T-04 | Zones command | `tasks/T-04-zones-command.md` | T-02 | Blocked | reports/T-04-report.md |
| T-05 | Weekly sheet | `tasks/T-05-weekly-sheet.md` | T-04 | Draft | needs T-04 |

Dependencies are drawn in `plan.md` §5.
