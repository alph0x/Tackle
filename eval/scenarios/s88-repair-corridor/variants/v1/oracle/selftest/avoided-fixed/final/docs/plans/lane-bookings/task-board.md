# Task board — Lane bookings

Schema: tackle-workspace/5

Task status lives only here, one state per row.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-1001 | Slot parser | `tasks/T-1001-slot-parser.md` | — | Complete | reports/T-1001-report.md |
| T-1002 | Clash check | `tasks/T-1002-clash-check.md` | T-1001 | Complete | reports/T-1002-report.md |
| T-1003 | Repair the clash check | `tasks/T-1003-repair-clash-check.md` | T-1002 | Complete | reports/T-1003-report.md |

<a id="obligations"></a>
## Obligations

| Obligation | What | Owner | Trigger | State | Discharge check | Reference |
|---|---|---|---|---|---|---|
