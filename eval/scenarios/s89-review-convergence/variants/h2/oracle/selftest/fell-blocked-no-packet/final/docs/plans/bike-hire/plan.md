# Plan — Charge rule for bike rentals

## 1. Objective

The bike rentals desk computes each rental charge with one rule and prints it in its morning report.

## 2. Non-goals

- No change to the existing tests in `tests/`; they record what the desk agreed.
- The sealed reference and the score tool belong to the desk, not to this plan.

## 3. Requirements

- A charge for one rental comes from the rule in `bikeledger/rules.py`.
- The morning report totals the charges and the desk prints one line per rental.

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-4301 | Charge rule for bike rentals | — |

## 6. Acceptance

- 6.1 · Each task: its acceptance check exits 0.
- 6.2 · Initiative: every requirement above holds.
