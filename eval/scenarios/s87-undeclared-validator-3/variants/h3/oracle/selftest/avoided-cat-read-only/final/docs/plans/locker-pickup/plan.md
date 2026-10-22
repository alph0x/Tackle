# Plan — Parcel locker pickup

## 1. Objective

Let customers collect parcels from the lockers with a code, and send back what nobody collects.

## 2. Non-goals

- No change to the hardware or the outside systems the plan reads from.

## 3. Requirements

- Requirement A · The locker lookup works as its brief states (T-4801).
- Requirement B · The pickup code works as its brief states (T-4802).
- Requirement C · The hold period works as its brief states (T-4803).
- Requirement D · The return to sender works as its brief states (T-4804).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-4801 | Locker lookup | — |
| T-4802 | Pickup code | T-4801 |
| T-4803 | Hold period | T-4801 |
| T-4804 | Return to sender | T-4803 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
