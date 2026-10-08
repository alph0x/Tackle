# Plan — rota hours

## 1. Objective

The shift export writes durations either as minutes (`420`) or as hours and minutes (`7:30`);
`bin/hours.sh` should sum both without hand editing.

## 2. Non-goals

- No change to the output format or to the summing of plain minutes.

## 3. Requirements

- R1 · `bin/hours.sh <name>` sums the minutes column for that name (T-01).
- R2 · A duration written `H:MM` counts as `H × 60 + MM` minutes (T-02).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Minutes total | — |
| T-02 | Clock-style durations | T-01 |

## 6. Acceptance

- 6.1 · Each task: its acceptance check passes; from T-02 on with a check record (D-01) linked from its
  report.
- 6.2 · Initiative: `sh bin/hours.sh ana tests/data/week.csv` prints `1185`.
