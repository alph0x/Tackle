# Task board — parcel kilos

Schema: tackle-workspace/5

Task status lives only here, one state per row.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-01 | Grams total | [T-01](tasks/T-01-grams-total.md) | — | Complete | [report](reports/T-01-report.md) |
| T-02 | Kilogram weights | [T-02](tasks/T-02-kilogram-weights.md) | T-01 | Complete | [report](reports/T-02-report.md) |

<a id="obligations"></a>
## Obligations

| Obligation | What | Owner | Trigger | State | Discharge check | Reference |
|---|---|---|---|---|---|---|
| O-01 | Import T-01's executor usage from `runs/T-01-executor.jsonl` (D-02) | coordinator | next RUN session | Open | `resource-usage.telemetry.jsonl` holds one observation per completed turn of the stream; receipt under `verification-records/T-01/`; T-01 finish row Source cites it | D-02 |
