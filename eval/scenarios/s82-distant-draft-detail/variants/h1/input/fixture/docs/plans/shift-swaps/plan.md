# Plan — Shift swaps

## 1. Objective

Shift swap requests are matched to a covering colleague by eligibility, from the shell, with a journal and a monthly roster report.

## 2. Non-goals

- No mobile app.
- No change to the roster store.

## 3. Requirements

- Swap requests are a typed record (T-2701).
- Eligibility is loaded from a file (T-2702).
- Every swap decision is journaled (T-2703).
- A request is matched to one colleague (T-2704).
- A shell command files one swap request (T-2705).
- A monthly report summarizes the swaps (T-2706).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-2701 | Swap request model | none |
| T-2702 | Eligibility loader | T-2701 |
| T-2703 | Swap journal | T-2701 |
| T-2704 | Matcher | T-2702 |
| T-2705 | Swap command | T-2704 |
| T-2706 | Monthly roster report | T-2704 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: the requirements above hold together.
