# Plan — Garden water

## 1. Objective

Turn the standpipe logger's daily lines into cubic metres drawn per billing week.

## 2. Non-goals

- No change to the plot billing rates or to the logger itself.
- No change to `tests/`; the treasurer signed off its cases.

## 3. Requirements

- R01 · A logger line becomes its day and its reading (T-3201).
- R02 · Usage between two readings survives one counter wrap (T-3202).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-3201 | Logger line reader | — |
| T-3202 | Weekly usage | T-3201 |
| T-3203 | Repair usage after the logger change | T-3202 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
