# Plan — column totals

## 1. Objective

The finance export's first line names the export, its year and its month (`orders,2026,10`);
`bin/tally.sh` should sum such files without hand editing.

## 2. Non-goals

- No change to the output format or to the summing of files without a header.

## 3. Requirements

- R1 · With `--header`, `bin/tally.sh` skips the first line of each input (T-01).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Header option | — |

## 6. Acceptance

- 6.1 · Each task: its acceptance check passes, with a verification record linked from its report.
- 6.2 · Initiative: `sh bin/tally.sh --header 3 tests/data/orders.csv` prints `2050`.
