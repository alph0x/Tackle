# Plan — Night desk booking surcharge

## 1. Objective of the night desk plan

The overnight counter adds one fixed surcharge to every booking it takes after closing time.

## 2. Non-goals of the night desk plan

- No change to the daytime booking rates or their tests in `tests/`.

## 3. Night desk requirements

- The surcharge for one late booking is the constant in `deskrates/rates.py`.

## 5. Task decomposition

| Task | What | Depends on | Night desk note |
|---|---|---|---|
| T-4501 | Night surcharge constant | — | one constant |

## 6. Night desk acceptance

- 6.1 · Each night desk task: its acceptance check exits 0.
- 6.2 · Night desk initiative: every requirement above holds.
