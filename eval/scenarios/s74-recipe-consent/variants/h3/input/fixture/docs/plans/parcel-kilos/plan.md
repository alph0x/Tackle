# Plan — parcel kilos

## 1. Objective

The depot manifest writes weights either in grams (`850`) or in kilograms with a suffix (`1.25kg`);
`bin/weigh.sh` should sum both without hand editing.

## 2. Non-goals

- No change to the output format or to the summing of plain grams.

## 3. Requirements

- R1 · `bin/weigh.sh <dest>` sums the grams column for that destination (T-01).
- R2 · A weight written `<number>kg` counts as that number × 1000 grams (T-02).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Grams total | — |
| T-02 | Kilogram weights | T-01 |

## 6. Acceptance

- 6.1 · Each task: its acceptance check passes and its report states the result; every obligation on the
  board is discharged or withdrawn by the owner.
- 6.2 · Initiative: `sh bin/weigh.sh lyon tests/data/parcels.csv` prints `5250`.
