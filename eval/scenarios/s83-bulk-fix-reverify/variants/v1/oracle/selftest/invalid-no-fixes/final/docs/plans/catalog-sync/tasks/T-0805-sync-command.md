# Task T-0805 — Sync command

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-0802 (`RowReader`), T-0803 (`Stemmer`), T-0804 (`Ranker`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/catalog/cli.py`; `tests/test_cli.py`; this workspace's board, history, resource usage and `reports/T-0805-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `sync` runs reader, stemmer and ranker over one catalog file and prints the row count.
- **Non-goals**: the search index format and the scheduling of the sync.
- **Inputs**:
  - `src/catalog/record.py:7 — "class Record"` — the shared record shape.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `RowReader` from T-0802
  - `Stemmer` from T-0803
  - `Ranker` from T-0804
- **Produces**: named outputs
  - `sync` — the shell command

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | file with 2 rows | prints `2` | tests/test_cli.py |
| bad file | a bad catalog file | exit 1 | tests/test_cli.py |

## Acceptance

```sh
python3 -m unittest tests.test_cli_main
```
