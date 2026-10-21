# Task T-0804 — Ranker

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-0801 (`CatalogSchema`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/catalog/ranker.py`; `tests/test_ranker.py`; this workspace's board, history, resource usage and `reports/T-0804-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `Ranker` scores a `Record` for the index.
- **Non-goals**: the search index format and the scheduling of the sync.
- **Inputs**:
  - `src/catalog/record.py:7 — "class Record"` — the shared record shape.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `CatalogSchema` from T-0801
- **Produces**: named outputs
  - `Ranker` — function from a record to a score

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | record priced 500 | score 5 | tests/test_ranker.py |
| invalid | record priced -1 | `ValueError` | tests/test_ranker.py |

## Acceptance

```sh
python3 -m unittest tests.test_ranker
```
