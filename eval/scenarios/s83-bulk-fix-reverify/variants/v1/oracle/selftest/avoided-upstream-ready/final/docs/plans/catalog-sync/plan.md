# Plan — Catalog sync

## 1. Objective

A partner catalog file is read, stemmed and ranked into the search index by one command.

## 2. Non-goals

- No change to the search index format.
- No scheduling of the sync.

## 3. Requirements

- The catalog record shape is fixed (T-0801).
- Catalog rows are read from a file (T-0802).
- Field names are stemmed (T-0803).
- Rows are ranked (T-0804).
- One command runs the sync (T-0805).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-0801 | Catalog schema | none |
| T-0802 | Row reader | T-0801 |
| T-0803 | Stemmer | T-0801 |
| T-0804 | Ranker | T-0801 |
| T-0805 | Sync command | T-0802, T-0803, T-0804 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: the requirements above hold together.
