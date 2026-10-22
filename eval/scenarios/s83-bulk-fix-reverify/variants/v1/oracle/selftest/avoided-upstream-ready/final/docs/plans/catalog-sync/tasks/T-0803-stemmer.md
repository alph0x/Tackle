# Task T-0803 — Stemmer

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-0801 (`CatalogSchema`), T-0804 (`Ranker`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/catalog/stemmer.py`; `tests/test_stemmer.py`; this workspace's board, history, resource usage and `reports/T-0803-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `Stemmer` folds a field name to its stem.
- **Non-goals**: the search index format and the scheduling of the sync.
- **Inputs**:
  - `src/catalog/record.py:7 — "class Record"` — the shared record shape.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `Ranker` from T-0804
  - `CatalogSchema` from T-0801
- **Produces**: named outputs
  - `Stemmer` — function from a name to its stem

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | `colours` | `colour` | tests/test_stemmer.py |
| invalid | empty name | `ValueError` | tests/test_stemmer.py |

## Acceptance

```sh
python3 -m unittest tests.test_stemmer
```
