# Plan — handling fee

## 1. Objective

The quoting desk prices pallet handling at the rate of the tariff edition in force.

## 2. Non-goals

- No change to the shape of the charge or to the output format of `bin/handling-fee.sh`.

## 3. Requirements

- R1 · `bin/handling-fee.sh` reads the rate from `config/fees.conf` (T-01).
- R2 · The configured rate is the one of the edition in force, from the operator's tariff (T-02).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Handling fee reader | — |
| T-02 | November tariff | T-01 |

## 6. Acceptance

- 6.1 · Each task: `sh tests/run.sh` exits 0, with the command, output and exit in its report.
- 6.2 · Initiative: the configured rate matches the transcribed tariff for the edition in force.
