# Plan — ledger CSV

## 1. Objective

Ledger descriptions sometimes hold a comma (`Smith, J.`) or a double quote; the bookkeeping import must
read every converted line as the same fields the ledger line had.

## 2. Non-goals

- No change to lines whose fields hold neither a comma nor a double quote.

## 3. Requirements

- R1 · `bin/to-csv.sh` joins the tab-separated fields with commas (T-01).
- R2 · A field holding a comma or a double quote is written in double quotes, with each inner double
  quote doubled (T-02).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Plain conversion | — |
| T-02 | Quoted fields | T-01 |

## 6. Acceptance

- 6.1 · Each task: its acceptance check passes, with a check record (D-01, D-02) linked from its report.
- 6.2 · Initiative: `printf 'Smith, J.\t12\n' | sh bin/to-csv.sh` prints `"Smith, J.",12`.
