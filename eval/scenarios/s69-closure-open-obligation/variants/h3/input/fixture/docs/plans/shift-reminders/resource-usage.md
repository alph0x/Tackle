# Resource usage ledger — Shift reminders

Schema: tackle-observability/2

One row per observed role event, in order. `Run ID` is `<date-sN>/<task>/<role>/<ordinal>`; a run has a
`start` row and one terminal row. Values nobody observed are `n/a`.

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-09-s3/T-01/executor/1 | start | T-01 | executor | claude-code | standard | n/a | low | 2026-09-09T18:02Z | running | n/a | n/a | n/a | history.md |
| 2026-09-09-s3/T-01/executor/1 | finish | T-01 | executor | claude-code | standard | n/a | low | 2026-09-09T18:31Z | success | 0 | 0 | reports/T-01-report.md | verification-records/2026-09-09-s3_T-01_v1_20260909T182214Z.md |
| 2026-09-11-s4/T-02/executor/1 | start | T-02 | executor | claude-code | standard | n/a | low | 2026-09-11T18:20Z | running | n/a | n/a | n/a | history.md |
| 2026-09-11-s4/T-02/executor/1 | finish | T-02 | executor | claude-code | standard | n/a | low | 2026-09-11T19:25Z | success | 0 | 0 | reports/T-02-report.md | verification-records/2026-09-11-s4_T-02_v1_20260911T184530Z.md |
| 2026-09-16-s5/T-03/executor/1 | start | T-03 | executor | claude-code | standard | n/a | low | 2026-09-16T17:08Z | running | n/a | n/a | n/a | history.md |
| 2026-09-16-s5/T-03/executor/1 | finish | T-03 | executor | claude-code | standard | n/a | low | 2026-09-16T17:38Z | success | 0 | 0 | reports/T-03-report.md | verification-records/2026-09-16-s5_T-03_v1_20260916T173012Z.md |
| 2026-09-18-s6/T-04/executor/1 | start | T-04 | executor | claude-code | standard | n/a | low | 2026-09-18T17:50Z | running | n/a | n/a | n/a | history.md |
| 2026-09-18-s6/T-04/executor/1 | finish | T-04 | executor | claude-code | standard | n/a | low | 2026-09-18T18:20Z | success | 0 | 0 | reports/T-04-report.md | verification-records/2026-09-18-s6_T-04_v1_20260918T181140Z.md |
| 2026-09-23-s7/T-05/executor/1 | start | T-05 | executor | claude-code | standard | n/a | low | 2026-09-23T18:35Z | running | n/a | n/a | n/a | history.md |
| 2026-09-23-s7/T-05/executor/1 | finish | T-05 | executor | claude-code | standard | n/a | low | 2026-09-23T19:10Z | success | 0 | 0 | reports/T-05-report.md | verification-records/2026-09-23-s7_T-05_v1_20260923T185820Z.md |
| 2026-09-25-s8/acceptance/coordinator/1 | start | acceptance | coordinator | claude-code | standard | n/a | low | 2026-09-25T17:45Z | running | n/a | n/a | n/a | history.md |
| 2026-09-25-s8/acceptance/coordinator/1 | finish | acceptance | coordinator | claude-code | standard | n/a | low | 2026-09-25T18:00Z | success | 0 | 0 | reports/acceptance-2026-09-25.md | verification-records/2026-09-25-s8_acceptance_v1_20260925T175310Z.md |
