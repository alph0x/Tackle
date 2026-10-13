# Task board — Invite redeem

Schema: tackle-workspace/5

Task status lives only here, one state per row.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-01 | Issue and lookup | [T-01](tasks/T-01-issue-lookup.md) | — | Complete | reports/T-01-report.md; `node --test test/` exit 0 |
| T-02 | Single-use redemption | [T-02](tasks/T-02-single-use.md) | T-01 | Waiting on owner | waiting: owner to pick the check for the scenario case |

<a id="obligations"></a>
## Obligations

| Obligation | What | Owner | Trigger | State | Discharge check | Reference |
|---|---|---|---|---|---|---|
