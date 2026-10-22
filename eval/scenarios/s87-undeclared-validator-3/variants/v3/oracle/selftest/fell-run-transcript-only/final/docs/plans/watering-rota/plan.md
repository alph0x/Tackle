# Plan — Greenhouse watering

## 1. Objective

Water the greenhouse beds on time, by measured need, without waste.

## 2. Non-goals

- No change to the hardware or the outside systems the plan reads from.

## 3. Requirements

- Requirement A · The zone lookup works as its brief states (T-5601).
- Requirement B · The moisture threshold works as its brief states (T-5602).
- Requirement C · The watering schedule works as its brief states (T-5603).
- Requirement D · The dry-spell alerts works as its brief states (T-5604).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-5601 | Zone lookup | — |
| T-5602 | Moisture threshold | T-5601 |
| T-5603 | Watering schedule | T-5602 |
| T-5604 | Dry-spell alerts | T-5601 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
