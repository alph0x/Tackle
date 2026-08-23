# Plan — demo

## Objective

Record one usage ledger row for a completed run and close the single open point.

## Point decomposition

| Point | What | Depends on |
|---|---|---|
| P-01 | Record this run's usage and close | none |

## Point P-01 — Record this run's usage and close

**Goal**: append the run's usage row to `usage.md` and flip the board to 🟢.

**Recommended approach**:
1. Appends one row to `usage.md` per the ledger table.
2. Records the close evidence in `log.md`.
3. Flips `board.md` P-01 to 🟢.

**Done-signal**: `grep -q '| P-01 ' usage.md && grep -q '🟢' board.md && echo closed` → prints `closed`.