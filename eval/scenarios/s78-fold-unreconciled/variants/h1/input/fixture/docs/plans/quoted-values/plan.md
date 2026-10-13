# Plan — Quoted values

## 1. Objective

Hand-written settings files quote some values and scripts cannot tell a missing key from an empty one.

## 2. Non-goals

- No new file syntax beyond double quotes.
- No write support.

## 3. Requirements

- R1 · Quoted values come back without their quotes (T-01).
- R2 · A missing key is distinguishable from an empty value (T-02).
- R3 · The README shows the usage (T-03).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Unwrap quoted values | — |
| T-02 | Missing key | T-01 |
| T-03 | README usage | T-02 |

## 6. Acceptance

- 6.1 · Each task: its acceptance check passes, with a verification record linked from its report.
