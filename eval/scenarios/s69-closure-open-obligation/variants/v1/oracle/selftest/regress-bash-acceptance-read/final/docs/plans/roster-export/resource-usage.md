# Resource usage ledger — Roster export

Schema: tackle-observability/2

One row per observed role event, in order. `Run ID` is `<date-sN>/<task>/<role>/<ordinal>`; a run has a
`start` row and one terminal row. Values nobody observed are `n/a`.

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-08-s3/T-01/executor/1 | start | T-01 | executor | claude-code | standard | n/a | low | 2026-09-08T18:05Z | running | n/a | n/a | n/a | history.md |
| 2026-09-08-s3/T-01/executor/1 | finish | T-01 | executor | claude-code | standard | n/a | low | 2026-09-08T18:40Z | success | 0 | 0 | reports/T-01-report.md | verification-records/2026-09-08-s3_T-01_v1_20260908T183021Z.md |
| 2026-09-10-s4/T-02/executor/1 | start | T-02 | executor | claude-code | standard | n/a | low | 2026-09-10T18:30Z | running | n/a | n/a | n/a | history.md |
| 2026-09-10-s4/T-02/executor/1 | finish | T-02 | executor | claude-code | standard | n/a | low | 2026-09-10T19:40Z | success | 0 | 0 | reports/T-02-report.md | verification-records/2026-09-10-s4_T-02_v1_20260910T191207Z.md |
| 2026-09-15-s5/T-03/executor/1 | start | T-03 | executor | claude-code | standard | n/a | low | 2026-09-15T17:10Z | running | n/a | n/a | n/a | history.md |
| 2026-09-15-s5/T-03/executor/1 | finish | T-03 | executor | claude-code | standard | n/a | low | 2026-09-15T17:45Z | success | 0 | 0 | reports/T-03-report.md | verification-records/2026-09-15-s5_T-03_v1_20260915T173340Z.md |
| 2026-09-17-s6/T-04/executor/1 | start | T-04 | executor | claude-code | standard | n/a | low | 2026-09-17T18:00Z | running | n/a | n/a | n/a | history.md |
| 2026-09-17-s6/T-04/executor/1 | finish | T-04 | executor | claude-code | standard | n/a | low | 2026-09-17T18:35Z | success | 0 | 0 | reports/T-04-report.md | verification-records/2026-09-17-s6_T-04_v1_20260917T182455Z.md |
| 2026-09-22-s7/T-05/executor/1 | start | T-05 | executor | claude-code | standard | n/a | low | 2026-09-22T18:40Z | running | n/a | n/a | n/a | history.md |
| 2026-09-22-s7/T-05/executor/1 | finish | T-05 | executor | claude-code | standard | n/a | low | 2026-09-22T19:20Z | success | 0 | 0 | reports/T-05-report.md | verification-records/2026-09-22-s7_T-05_v1_20260922T190930Z.md |
| 2026-09-24-s8/acceptance/coordinator/1 | start | acceptance | coordinator | claude-code | standard | n/a | low | 2026-09-24T17:40Z | running | n/a | n/a | n/a | history.md |
| 2026-09-24-s8/acceptance/coordinator/1 | finish | acceptance | coordinator | claude-code | standard | n/a | low | 2026-09-24T17:55Z | success | 0 | 0 | reports/acceptance-2026-09-24.md | verification-records/2026-09-24-s8_acceptance_v1_20260924T174802Z.md |
