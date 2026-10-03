# Resource usage ledger — Price notice

Schema: tackle-observability/2

One row per observed role event, in order. `Run ID` is `<date-sN>/<task>/<role>/<ordinal>`; a run has a
`start` row and one terminal row (`finish`, or `observe-incomplete` when nobody saw the end). Values nobody
observed are `n/a`.

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-17-s3/T-01/executor/1 | start | T-01 | executor | claude-code | standard | n/a | low | 2026-09-17T10:20Z | running | n/a | n/a | n/a | history.md |
| 2026-09-17-s3/T-01/executor/1 | finish | T-01 | executor | claude-code | standard | n/a | low | 2026-09-17T10:55Z | success | 0 | 0 | reports/T-01-report.md | verification-records/2026-09-17-s3_T-01_v1_20260917T104409Z.md |
| 2026-09-19-s4/T-02/executor/1 | start | T-02 | executor | claude-code | standard | n/a | low | 2026-09-19T14:05Z | running | n/a | n/a | n/a | history.md |
| 2026-09-19-s4/T-02/executor/1 | finish | T-02 | executor | claude-code | standard | n/a | low | 2026-09-19T15:15Z | success | 0 | 0 | reports/T-02-report.md | reports/T-02-report.md |
| 2026-09-23-s5/T-03/executor/1 | start | T-03 | executor | claude-code | standard | n/a | low | 2026-09-23T09:00Z | running | n/a | n/a | n/a | history.md |
| 2026-09-23-s5/T-03/executor/1 | finish | T-03 | executor | claude-code | standard | n/a | low | 2026-09-23T10:05Z | success | 0 | 0 | reports/T-03-report.md | reports/T-03-report.md |
| 2026-09-26-s6/T-04/executor/1 | start | T-04 | executor | claude-code | standard | n/a | low | 2026-09-26T19:30Z | running | n/a | n/a | n/a | history.md |
| 2026-09-26-s6/T-04/executor/1 | finish | T-04 | executor | claude-code | standard | n/a | low | 2026-09-26T20:40Z | success | 0 | 0 | reports/T-04-report.md | verification-records/2026-09-26-s6_T-04_v1_20260926T203115Z.md |
| 2026-09-30-s8/T-05/executor/1 | start | T-05 | executor | claude-code | standard | n/a | low | 2026-09-30T07:46Z | running | n/a | n/a | n/a | history.md |
| 2026-09-30-s8/T-05/executor/1 | observe-incomplete | T-05 | executor | claude-code | standard | n/a | low | n/a | incomplete | n/a | n/a | n/a | history.md |
| 2026-10-01-s9/T-05/executor/1 | start | T-05 | executor | claude-code | standard | n/a | low | 2026-10-01T07:58Z | running | n/a | n/a | n/a | history.md |
| 2026-10-01-s9/T-05/executor/1 | finish | T-05 | executor | claude-code | standard | n/a | low | 2026-10-01T08:20Z | success | 0 | 0 | reports/T-05-report.md | verification-records/2026-10-01-s9_T-05_v1_20261001T080915Z.md |
