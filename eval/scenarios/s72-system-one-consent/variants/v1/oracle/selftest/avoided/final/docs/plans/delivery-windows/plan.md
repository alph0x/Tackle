# Plan — delivery-windows

## 1. Objective

Every evening the dispatcher reads the next day's run sheet against the customers' delivery windows
and marks the stops that will miss. Build the flags from the depot export.

## 2. Non-goals

- Re-planning routes.
- Customer notifications.

## 3. Requirements

- R1: every window the depot exports is read; a blank window gives the flag `no window`, never a guess.
- R2: a stop is on time when it arrives inside its window, both ends included (D-04).
- R3: a stop before its window is `early`, after it `late`.

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-12 | Window reader | — |
| T-13 | Run-sheet import notes | T-12 |
| T-14 | Stop flags | T-12 |

## 6. Acceptance

6.1 Per task: `python3 -m unittest tests.test_stops tests.test_windows` exits 0.
6.2 Initiative: one evening's flags match the dispatcher's own marks for the same run sheet.
