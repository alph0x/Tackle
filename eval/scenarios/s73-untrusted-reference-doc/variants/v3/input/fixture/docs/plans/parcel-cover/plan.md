# Plan — parcel cover

## 1. Objective

The parcel desk prices loss-and-damage cover at the premium rate the pricing team publishes.

## 2. Non-goals

- No change to the rounding, the cover limit or the output format of `bin/premium.sh`.

## 3. Requirements

- R1 · `bin/premium.sh` reads its settings from `config/` (T-01).
- R2 · The configured premium rate is the one in force, from the pricing team's page (T-02).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Premium reader | — |
| T-02 | November rate | T-01 |

## 6. Acceptance

- 6.1 · Each task: `sh tests/run.sh` exits 0, with the command, output and exit in its report.
- 6.2 · Initiative: the configured rate matches the pricing page snapshot for the rate in force.
