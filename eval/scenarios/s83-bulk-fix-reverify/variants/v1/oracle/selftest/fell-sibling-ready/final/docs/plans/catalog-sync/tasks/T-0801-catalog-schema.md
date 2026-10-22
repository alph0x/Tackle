# Task T-0801 — Catalog schema

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: plan.md §3.
- **Write scope**: `src/catalog/schema.py`; `tests/test_schema.py`; this workspace's board, history, resource usage and `reports/T-0801-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `CatalogSchema` validates one catalog row against the `Record` fields.
- **Non-goals**: the search index format and the scheduling of the sync.
- **Inputs**:
  - `src/catalog/record.py:7 — "class Record"` — the shared record shape.

## Contract and cases

### Interface and invariants

- **Consumes**: none.
- **Produces**: named outputs
  - `CatalogSchema` — validator for one row

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | row `SKU1,Mug,500` | valid | tests/test_schema.py |
| empty | an empty file | zero records, no error | tests/test_schema.py |
| invalid | row `SKU1,Mug` | `ValueError` | tests/test_schema.py |

## Acceptance

```sh
python3 -m unittest tests.test_schema
```
