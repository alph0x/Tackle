# Task board — Catalog sync

Schema: tackle-workspace/5

Task status lives only here, one state per row.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-0801 | Catalog schema | tasks/T-0801-catalog-schema.md | none | Ready to run | ready: history.md session 4 |
| T-0802 | Row reader | tasks/T-0802-row-reader.md | T-0801, T-0803 | Ready to run | ready: history.md session 4 |
| T-0803 | Stemmer | tasks/T-0803-stemmer.md | T-0801, T-0804 | Ready to run | ready: history.md session 4 |
| T-0804 | Ranker | tasks/T-0804-ranker.md | T-0801 | Ready to run | ready: history.md session 4 |
| T-0805 | Sync command | tasks/T-0805-sync-command.md | T-0802, T-0803, T-0804 | Ready to run | ready: history.md session 4 |

<a id="obligations"></a>
## Obligations

| Obligation | What | Owner | Trigger | State | Discharge check | Reference |
|---|---|---|---|---|---|---|
