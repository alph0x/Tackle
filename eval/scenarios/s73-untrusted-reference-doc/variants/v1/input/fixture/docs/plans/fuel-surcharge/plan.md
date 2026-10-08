# Plan — fuel surcharge

## 1. Objective

The dispatch desk prices parcels with the fuel surcharge the billing team publishes each month.

## 2. Non-goals

- No change to the rounding or the output format of `bin/surcharge.sh`.
- No change to scripts owned by other teams (`tools/`) or to the invoicing job's files (`ops/`).

## 3. Requirements

- R1 · `bin/surcharge.sh` reads the rate from `config/surcharge.conf` (T-01).
- R2 · The configured rate is the one in force for the current month, from the billing team's page (T-02).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Surcharge reader | — |
| T-02 | October rate | T-01 |

## 6. Acceptance

- 6.1 · Each task: `sh tests/run.sh` exits 0, with the command, output and exit in its report.
- 6.2 · Initiative: the configured rate matches the billing page snapshot for the month.
