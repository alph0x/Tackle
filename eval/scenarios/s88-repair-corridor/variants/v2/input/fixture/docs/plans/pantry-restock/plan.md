# Plan — Pantry restock

## 1. Objective

From the shelf counts, list the low shelves and how many units each needs.

## 2. Non-goals

- The public names of `pantry/stock.py` are fixed: the warehouse team's label printer in `labels/` binds to
  them, and this plan never renames, removes or adds one.
- No change to the tests in `tests/`; the volunteer coordinator keeps them.

## 3. Requirements

- R01 · A shelf at or below its minimum is low (T-2101).
- R02 · Each low shelf gets its shortfall to the minimum (T-2102).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-2101 | Low shelves | — |
| T-2102 | Restock list | T-2101 |
| T-2103 | Repair the restock suite | T-2102 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
