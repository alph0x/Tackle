# Task board — Catalog sync

Schema: tackle-workspace/5

Where each task of the catalog-sync initiative stands. This table is the single home of task state; the
plan carries requirements, `history.md` the sequence of events. Only the session that coordinates a run
edits it.

One token per Status cell. Working states, top first: Complete, Checking, In progress, Ready to run,
Draft. Halted states: Blocked, Interrupted, Unverifiable, Waiting on owner. Skipped marks work the owner
pulled. Detail belongs in Verification or `questions.md`.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-01 | Catalog reader | `tasks/T-01-catalog-reader.md` | none | Complete | reports/T-01-report.md |
| T-02 | Feed builder | `tasks/T-02-feed-builder.md` | T-01 | Complete | reports/T-02-report.md |
| T-03 | Nightly runner | `tasks/T-03-nightly-runner.md` | T-02 | Complete | reports/T-03-report.md |
| T-04 | Acceptance run | `tasks/T-04-acceptance-run.md` | T-02, T-03 | Complete | reports/T-04-report.md |

Deliverable acceptance of the initiative: `reports/acceptance-2026-09-19.md`. The graph is in `plan.md` §5.
