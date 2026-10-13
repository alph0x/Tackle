# Plan — coupon expiry

## 1. Objective

Coupons carry an expiry date. A quote applies a coupon only while it is valid and states the reason when it
does not (requirement `R1`).

## 2. Non-goals

- No change to `total()`, which stays as it is for existing callers.
- No coupon storage or issuing.

## 3. Requirements

- `R1` · `quote(items, coupon, today)` returns the total and a note; an expired coupon is ignored (T-01).

## 4. Tasks

| Task | What | Depends on | Why separate |
|---|---|---|---|
| T-01 | Quote with expiry | — | — |

## 5. Acceptance

- 5.1 · Each task: its acceptance check passes and its report is linked from the board.
- 5.2 · Initiative: `python3 -m unittest discover -s tests` exits 0.
