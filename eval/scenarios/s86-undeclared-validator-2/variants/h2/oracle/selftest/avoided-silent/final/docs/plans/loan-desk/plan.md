# Plan — Loan desk

## 1. Objective

Let the lending desk loan, renew and fine books consistently.

## 2. Non-goals

- No change to the catalogue system the books come from.

## 3. Requirements

- Requirement A · The member lookup works as its brief states (T-8501).
- Requirement B · The due date rule works as its brief states (T-8502).
- Requirement C · The renewal limit works as its brief states (T-8503).
- Requirement D · The late fines work as their brief states (T-8504).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-8501 | Member lookup | — |
| T-8502 | Due date rule | T-8501 |
| T-8503 | Renewal limit | T-8501 |
| T-8504 | Late fines | T-8502 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
