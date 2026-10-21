# Task T-0802 — Row reader

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-0801 (`CatalogSchema`), T-0803 (`Stemmer`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/catalog/reader.py`; `tests/test_reader.py`; this workspace's board, history, resource usage and `reports/T-0802-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `RowReader` yields the rows of a catalog file as `Record` values.
- **Non-goals**: the search index format and the scheduling of the sync.
- **Inputs**:
  - `src/catalog/record.py:7 — "class Record"` — the shared record shape.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `Stemmer` from T-0803
  - `CatalogSchema` from T-0801
- **Produces**: named outputs
  - `RowReader` — iterator over the rows of a file

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | file with 2 rows | 2 records | tests/test_reader.py |
| invalid | file with a bad header | `ValueError` | tests/test_reader.py |

## Acceptance

```sh
python3 -m unittest tests.test_reader
```
