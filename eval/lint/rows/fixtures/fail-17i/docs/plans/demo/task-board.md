# Task board — demo

Schema: tackle-workspace/5

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-A | Work | tasks/T-A.md | none | Complete | reports/T-A-report.md |
| T-B | More work | tasks/T-B.md | T-A | Draft | pending |

<a id="obligations"></a>
## Obligations

| Obligation | What | Owner | Trigger | State | Discharge check | Reference |
|---|---|---|---|---|---|---|
| **O-01** | Rotate the sample credential | owner | before the release | Open | the rotation record exists | |
| O-03 | Remove the temporary flag | executor | next session | Discharged | the flag is gone from the source | reports/T-A-report.md |
