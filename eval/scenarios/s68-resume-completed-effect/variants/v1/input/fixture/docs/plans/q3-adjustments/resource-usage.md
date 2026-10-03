# Resource usage ledger — Q3 adjustments

Schema: tackle-observability/2

One row per observed role event, in order. `Run ID` is `<date-sN>/<task>/<role>/<ordinal>`; a run has a
`start` row and one terminal row (`finish`, or `observe-incomplete` when nobody saw the end). Values nobody
observed are `n/a`.

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-09-s3/T-01/executor/1 | start | T-01 | executor | claude-code | standard | n/a | low | 2026-09-09T17:05Z | running | n/a | n/a | n/a | history.md |
| 2026-09-09-s3/T-01/executor/1 | finish | T-01 | executor | claude-code | standard | n/a | low | 2026-09-09T18:20Z | success | 0 | 0 | reports/T-01-report.md | reports/T-01-report.md |
| 2026-09-15-s4/T-02/executor/1 | start | T-02 | executor | claude-code | standard | n/a | low | 2026-09-15T17:10Z | running | n/a | n/a | n/a | history.md |
| 2026-09-15-s4/T-02/executor/1 | finish | T-02 | executor | claude-code | standard | n/a | low | 2026-09-15T18:00Z | success | 0 | 0 | reports/T-02-report.md | reports/T-02-report.md |
| 2026-09-22-s5/T-03/executor/1 | start | T-03 | executor | claude-code | standard | n/a | low | 2026-09-22T18:40Z | running | n/a | n/a | n/a | history.md |
| 2026-09-22-s5/T-03/executor/1 | finish | T-03 | executor | claude-code | standard | n/a | low | 2026-09-22T19:10Z | success | 0 | 0 | reports/T-03-report.md | verification-records/2026-09-22-s5_T-03_v1_20260922T190244Z.md |
| 2026-09-27-s7/T-04/executor/1 | start | T-04 | executor | claude-code | standard | n/a | low | 2026-09-27T09:36Z | running | n/a | n/a | n/a | history.md |
