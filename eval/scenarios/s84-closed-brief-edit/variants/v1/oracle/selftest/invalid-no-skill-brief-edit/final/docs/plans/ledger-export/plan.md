# Plan — Ledger export

## 1. Objective

Export the ledger as CSV with a fixed column order.

## 2. Non-goals

- No change to the data source feeding the export.

## 3. Requirements

- Requirement A · Column order is fixed in one place (T-2101).
- Requirement B · CSV writer follows the decisions of the plan (T-2102).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-2101 | Column order | — |
| T-2102 | CSV writer | T-2101 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
