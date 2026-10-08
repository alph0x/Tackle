# Plan — FX rate

## 1. Objective

The sales desk prices offers in dollars at the month's reference rate.

## 2. Non-goals

- No change to the rounding or the output format of `bin/quote.sh`.

## 3. Requirements

- R1 · `bin/quote.sh` reads the rate from `config/fx.conf` (T-01).
- R2 · The configured rate is the month's reference rate from ratebook (T-02).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Quote reader | — |
| T-02 | October rate | T-01 |

## 6. Acceptance

- 6.1 · Each task: `sh tests/run.sh` exits 0, with the command, output and exit in its report.
- 6.2 · Initiative: the configured rate matches ratebook's rate for the month's first business day.
