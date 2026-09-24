# P-port-config — config extraction

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS point from this file alone.

## Status & wiring
**Depends on**: none · execution status in `board.md`.
- **Traces to**: `plan.md §6.1`.

## Goal
Move config loading out of `src/main.py` into `src/config.py`.

## Recommended approach
1. Extract the config block (`src/main.py:12-30`).
2. Run `python3 -m py_compile src/config.py src/main.py`.

## Acceptance — the loop's exit gate
- **Run**: `python3 -m py_compile src/config.py src/main.py` → pass = exit 0.
