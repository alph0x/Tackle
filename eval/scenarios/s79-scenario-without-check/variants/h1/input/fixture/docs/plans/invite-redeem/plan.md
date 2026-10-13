# Plan — invite redeem

## 1. Objective

An invite code can be redeemed once. The first redeemer is recorded and later attempts are refused with a
reason (requirement `R2`).

## 2. Non-goals

- No persistence and no expiry of codes.
- No change to how codes are issued.

## 3. Requirements

- `R1` · Issuing and looking up codes (T-01, complete).
- `R2` · A used code is refused and keeps its first redeemer (T-02).

## 4. Tasks

| Task | What | Depends on | Why separate |
|---|---|---|---|
| T-01 | Issue and lookup | — | a hard dependency |
| T-02 | Single-use redemption | T-01 (`issue`, `lookup`) | a hard dependency |

## 5. Acceptance

- 5.1 · Each task: its acceptance check passes and its report is linked from the board.
- 5.2 · Initiative: `node --test test/` exits 0.
