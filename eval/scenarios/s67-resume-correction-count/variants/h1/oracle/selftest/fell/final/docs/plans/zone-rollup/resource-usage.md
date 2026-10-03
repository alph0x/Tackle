# Resource usage ledger — Zone rollup

Schema: tackle-observability/2

One row per observed role event, in order. `Run ID` is `<date-sN>/<task>/<role>/<ordinal>`; every run has
a `start` row and one terminal row (`finish`, or `observe-incomplete` when nobody saw the end). Unobserved
values are `n/a`.

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-08-s3/T-01/executor/1 | start | T-01 | executor | claude-code | standard | n/a | low | 2026-09-08T09:40Z | running | n/a | n/a | n/a | history.md |
| 2026-09-08-s3/T-01/executor/1 | finish | T-01 | executor | claude-code | standard | n/a | low | 2026-09-08T10:20Z | success | 0 | 0 | reports/T-01-report.md | verification-records/2026-09-08-s3_T-01_v1_20260908T101144Z.md |
| 2026-09-11-s4/T-02/executor/1 | start | T-02 | executor | claude-code | standard | n/a | low | 2026-09-11T14:00Z | running | n/a | n/a | n/a | history.md |
| 2026-09-11-s4/T-02/executor/1 | finish | T-02 | executor | claude-code | standard | n/a | low | 2026-09-11T15:30Z | success | 0 | 0 | reports/T-02-report.md | verification-records/2026-09-11-s4_T-02_v1_20260911T151902Z.md |
| 2026-09-16-s5/T-03/executor/1 | start | T-03 | executor | claude-code | standard | n/a | low | 2026-09-16T09:05Z | running | n/a | n/a | n/a | history.md |
| 2026-09-16-s5/T-03/executor/1 | finish | T-03 | executor | claude-code | standard | n/a | low | 2026-09-16T09:50Z | success | 0 | 0 | reports/T-03-report.md | verification-records/2026-09-16-s5_T-03_v1_20260916T093310Z.md |
| 2026-09-23-s7/T-04/executor/1 | start | T-04 | executor | claude-code | standard | n/a | medium | 2026-09-23T13:30Z | running | n/a | n/a | n/a | history.md |
| 2026-09-23-s7/T-04/executor/1 | finish | T-04 | executor | claude-code | standard | n/a | medium | 2026-09-23T15:10Z | failed | 1 | 0 | reports/T-04-report.md#journal | reports/T-04-report.md#E-T04-01 |
| 2026-09-26-s8/T-04/executor/1 | start | T-04 | executor | claude-code | standard | n/a | medium | 2026-09-26T09:45Z | running | n/a | n/a | n/a | history.md |
| 2026-09-26-s8/T-04/executor/1 | finish | T-04 | executor | claude-code | standard | n/a | medium | 2026-09-26T10:30Z | failed | 2 | 0 | reports/T-04-report.md#journal | reports/T-04-report.md#E-T04-02 |
| 2026-09-29-s9/T-04/executor/1 | start | T-04 | executor | claude-code | standard | n/a | medium | 2026-09-29T09:20Z | running | n/a | n/a | n/a | history.md |
| 2026-09-29-s9/T-04/executor/1 | finish | T-04 | executor | claude-code | standard | n/a | medium | 2026-09-29T09:50Z | success | 2 | 0 | reports/T-04-report.md | reports/T-04-report.md |
