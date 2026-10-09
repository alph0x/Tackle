# Plan — remote supplement

## 1. Objective

The dispatch desk prices each remote-area parcel with the supplement of the carrier's current zone kit.

## 2. Non-goals

- No change to the shape of the charge or to the output format of `bin/supplement.sh`.

## 3. Requirements

- R1 · `bin/supplement.sh` reads the supplements from `config/zones.conf` (T-01).
- R2 · Each configured supplement is the one of the current zone kit edition (T-02).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Supplement reader | — |
| T-02 | HS supplement, zonekit 2026.4 | T-01 |

## 6. Acceptance

- 6.1 · Each task: `sh tests/run.sh` exits 0, with the command, output and exit in its report.
- 6.2 · Initiative: the configured supplements match the vendored zone kit.
