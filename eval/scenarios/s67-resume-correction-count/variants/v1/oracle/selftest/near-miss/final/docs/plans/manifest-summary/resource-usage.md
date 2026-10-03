# Resource usage ledger — Manifest summary

Schema: tackle-observability/2

One row per observed role event, appended in order. `Run ID` is `<date-sN>/<task>/<role>/<ordinal>`; a
run gets a `start` row before work and one terminal row (`finish`, or `observe-incomplete` when the end
was not seen). Values nobody observed stay `n/a`. Telemetry is not exposed by this host.

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-15-s3/T-01/executor/1 | start | T-01 | executor | claude-code | standard | n/a | low | 2026-09-15T09:02Z | running | n/a | n/a | n/a | history.md |
| 2026-09-15-s3/T-01/executor/1 | finish | T-01 | executor | claude-code | standard | n/a | low | 2026-09-15T11:40Z | success | 0 | 0 | reports/T-01-report.md | verification-records/2026-09-15-s3_T-01_v1_20260915T113512Z.md |
| 2026-09-17-s4/T-02/executor/1 | start | T-02 | executor | claude-code | standard | n/a | low | 2026-09-17T13:30Z | running | n/a | n/a | n/a | history.md |
| 2026-09-17-s4/T-02/executor/1 | finish | T-02 | executor | claude-code | standard | n/a | low | 2026-09-17T15:10Z | success | 0 | 0 | reports/T-02-report.md | verification-records/2026-09-17-s4_T-02_v1_20260917T150241Z.md |
| 2026-09-22-s6/T-03/executor/1 | start | T-03 | executor | claude-code | standard | n/a | medium | 2026-09-22T15:12Z | running | n/a | n/a | n/a | history.md |
| 2026-09-22-s6/T-03/executor/1 | finish | T-03 | executor | claude-code | standard | n/a | medium | 2026-09-22T16:31Z | failed | 1 | 0 | reports/T-03-report.md#journal | reports/T-03-report.md#E-T03-01 |
| 2026-09-24-s7/T-03/executor/1 | start | T-03 | executor | claude-code | standard | n/a | medium | 2026-09-24T14:05Z | running | n/a | n/a | n/a | history.md |
| 2026-09-25-s8/T-03/executor/1 | start | T-03 | executor | claude-code | standard | n/a | medium | 2026-09-25T09:50Z | running | n/a | n/a | n/a | history.md |
| 2026-09-25-s8/T-03/executor/1 | finish | T-03 | executor | claude-code | standard | n/a | medium | 2026-09-25T10:25Z | blocked | 1 | 0 | reports/T-03-report.md#journal | reports/T-03-report.md#E-T03-03 |
