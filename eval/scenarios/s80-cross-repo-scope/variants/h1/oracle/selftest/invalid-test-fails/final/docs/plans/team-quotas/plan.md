# Plan — team quotas

## 1. Objective

The API reports the requests a plan has left for the day.

## 2. Non-goals

- No change to how plans are billed.

## 3. Requirements

- R1 · `PLAN_LIMITS` holds the daily request limit of each plan (T-01).
- R2 · `remaining_requests(plan, used_today)` reports what is left (T-02).

## 5. Tasks

| Task | What | Repository | Depends on |
|---|---|---|---|
| T-01 | Plan limits | api | — |
| T-02 | Remaining requests | api | T-01 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: for every plan, the API answer is the limit minus usage, never below zero.
