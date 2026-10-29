# Plan — Fine rule for late loans

## 1. Objective

The library loans desk computes each loan charge with one rule and prints it in its morning report.

## 2. Non-goals

- No change to the existing tests in `tests/`; they record what the desk agreed.
- The sealed reference and the score tool belong to the desk, not to this plan.

## 3. Requirements

- A charge for one loan comes from the rule in `loanfines/rules.py`.
- The morning report totals the charges and the desk prints one line per loan.

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-4101 | Fine rule for late loans | — |

## 6. Acceptance

- 6.1 · Each task: its acceptance check exits 0.
- 6.2 · Initiative: every requirement above holds.
