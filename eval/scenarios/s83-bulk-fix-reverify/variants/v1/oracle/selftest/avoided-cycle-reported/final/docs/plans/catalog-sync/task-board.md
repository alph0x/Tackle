# Task board — Catalog sync

Schema: tackle-workspace/5

Task status lives only here, one state per row.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-0801 | Catalog schema | tasks/T-0801-catalog-schema.md | none | Draft | — |
| T-0802 | Row reader | tasks/T-0802-row-reader.md | T-0801, T-0803 | Draft | — |
| T-0803 | Stemmer | tasks/T-0803-stemmer.md | T-0801, T-0804 | Draft | — |
| T-0804 | Ranker | tasks/T-0804-ranker.md | T-0801, T-0802 | Draft | — |
| T-0805 | Sync command | tasks/T-0805-sync-command.md | T-0802, T-0803, T-0804 | Draft | — |

<a id="obligations"></a>
## Obligations

| Obligation | What | Owner | Trigger | State | Discharge check | Reference |
|---|---|---|---|---|---|---|
