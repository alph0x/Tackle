# Plan — october tides

## 1. Objective

Berth checks use the month's lowest predicted height from the harbour office's feed.

## 2. Non-goals

- No change to the vendored feed (`vendor/`).

## 3. Requirements

- R1 · `bin/berth-check.sh` uses `LOW_WATER_CM` and `CLEARANCE_CM` from `config/tide.conf` (T-03).
- R2 · `LOW_WATER_CM` is the current month's figure from the feed (T-04).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-03 | Clearance check | — |
| T-04 | October low water | T-03 |

## 6. Acceptance

- 6.1 · Each task: `sh tests/run.sh` exits 0, with the command, output and exit in its report.
- 6.2 · Initiative: the configured low water matches the feed for the month.
