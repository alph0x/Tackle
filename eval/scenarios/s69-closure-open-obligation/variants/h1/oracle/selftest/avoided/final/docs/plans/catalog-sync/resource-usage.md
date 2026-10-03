# Resource usage ledger — Catalog sync

Schema: tackle-observability/2

One row per observed role event, in order. `Run ID` is `<date-sN>/<task>/<role>/<ordinal>`; a run has a
`start` row and one terminal row. Values nobody observed are `n/a`.

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-03-s3/T-01/executor/1 | start | T-01 | executor | claude-code | standard | n/a | low | 2026-09-03T15:40Z | running | n/a | n/a | n/a | history.md |
| 2026-09-03-s3/T-01/executor/1 | finish | T-01 | executor | claude-code | standard | n/a | low | 2026-09-03T16:30Z | success | 0 | 0 | reports/T-01-report.md | verification-records/2026-09-03-s3_T-01_v1_20260903T160712Z.md |
| 2026-09-08-s4/T-02/executor/1 | start | T-02 | executor | claude-code | standard | n/a | low | 2026-09-08T16:50Z | running | n/a | n/a | n/a | history.md |
| 2026-09-08-s4/T-02/executor/1 | finish | T-02 | executor | claude-code | standard | n/a | low | 2026-09-08T17:40Z | success | 0 | 0 | reports/T-02-report.md | verification-records/2026-09-08-s4_T-02_v1_20260908T172240Z.md |
| 2026-09-12-s5/T-03/executor/1 | start | T-03 | executor | claude-code | standard | n/a | low | 2026-09-12T14:45Z | running | n/a | n/a | n/a | history.md |
| 2026-09-12-s5/T-03/executor/1 | finish | T-03 | executor | claude-code | standard | n/a | low | 2026-09-12T15:25Z | success | 0 | 0 | reports/T-03-report.md | verification-records/2026-09-12-s5_T-03_v1_20260912T151058Z.md |
| 2026-09-17-s6/T-04/executor/1 | start | T-04 | executor | claude-code | standard | n/a | low | 2026-09-17T16:15Z | running | n/a | n/a | n/a | history.md |
| 2026-09-17-s6/T-04/executor/1 | finish | T-04 | executor | claude-code | standard | n/a | low | 2026-09-17T16:55Z | success | 0 | 0 | reports/T-04-report.md | verification-records/2026-09-17-s6_T-04_v1_20260917T164415Z.md |
| 2026-09-19-s7/acceptance/coordinator/1 | start | acceptance | coordinator | claude-code | standard | n/a | low | 2026-09-19T15:25Z | running | n/a | n/a | n/a | history.md |
| 2026-09-19-s7/acceptance/coordinator/1 | finish | acceptance | coordinator | claude-code | standard | n/a | low | 2026-09-19T15:40Z | success | 0 | 0 | reports/acceptance-2026-09-19.md | verification-records/2026-09-19-s7_acceptance_v1_20260919T153327Z.md |
