# Plan — Room booking

## 1. Objective

Let staff book meeting rooms without double-booking them.

## 2. Non-goals

- No change to the calendar system the rooms are mirrored from.

## 3. Requirements

- Requirement A · The room list works as its brief states (T-6101).
- Requirement B · The overlap check works as its brief states (T-6102).
- Requirement C · Hold expiry works as its brief states (T-6103).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-6101 | Room list | — |
| T-6102 | Overlap check | T-6101 |
| T-6103 | Hold expiry | T-6101 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
