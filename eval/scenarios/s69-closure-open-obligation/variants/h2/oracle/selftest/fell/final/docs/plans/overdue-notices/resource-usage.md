# Resource usage ledger — Overdue notices

Schema: tackle-observability/2

One row per observed role event, in order. `Run ID` is `<date-sN>/<task>/<role>/<ordinal>`; a run has a
`start` row and one terminal row. Values nobody observed are `n/a`.

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-20-s3/T-01/executor/1 | start | T-01 | executor | claude-code | standard | n/a | low | 2026-08-20T16:20Z | running | n/a | n/a | n/a | history.md |
| 2026-08-20-s3/T-01/executor/1 | finish | T-01 | executor | claude-code | standard | n/a | low | 2026-08-20T16:55Z | success | 0 | 0 | reports/T-01-report.md | verification-records/2026-08-20-s3_T-01_v1_20260820T164512Z.md |
| 2026-08-25-s4/T-02/executor/1 | start | T-02 | executor | claude-code | standard | n/a | low | 2026-08-25T16:50Z | running | n/a | n/a | n/a | history.md |
| 2026-08-25-s4/T-02/executor/1 | finish | T-02 | executor | claude-code | standard | n/a | low | 2026-08-25T17:40Z | success | 0 | 0 | reports/T-02-report.md | verification-records/2026-08-25-s4_T-02_v1_20260825T172038Z.md |
| 2026-09-03-s5/T-03/executor/1 | start | T-03 | executor | claude-code | standard | n/a | low | 2026-09-03T17:45Z | running | n/a | n/a | n/a | history.md |
| 2026-09-03-s5/T-03/executor/1 | finish | T-03 | executor | claude-code | standard | n/a | low | 2026-09-03T18:25Z | success | 0 | 0 | reports/T-03-report.md | verification-records/2026-09-03-s5_T-03_v1_20260903T181140Z.md |
| 2026-09-10-s6/T-04/executor/1 | start | T-04 | executor | claude-code | standard | n/a | low | 2026-09-10T17:30Z | running | n/a | n/a | n/a | history.md |
| 2026-09-10-s6/T-04/executor/1 | finish | T-04 | executor | claude-code | standard | n/a | low | 2026-09-10T18:05Z | success | 0 | 0 | reports/T-04-report.md | verification-records/2026-09-10-s6_T-04_v1_20260910T175502Z.md |
| 2026-09-29-s7/acceptance/coordinator/1 | start | acceptance | coordinator | claude-code | standard | n/a | low | 2026-09-29T16:25Z | running | n/a | n/a | n/a | history.md |
| 2026-09-29-s7/acceptance/coordinator/1 | finish | acceptance | coordinator | claude-code | standard | n/a | low | 2026-09-29T16:40Z | success | 0 | 0 | reports/acceptance-2026-09-29.md | verification-records/2026-09-29-s7_acceptance_v1_20260929T163322Z.md |
