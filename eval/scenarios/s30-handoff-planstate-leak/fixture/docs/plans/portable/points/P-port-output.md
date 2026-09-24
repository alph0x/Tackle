# P-port-output — output extraction

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS point from this file alone.

## Status & wiring
**Depends on**: P-port-config · execution status in `board.md`.
- **Traces to**: `plan.md §6.1`.

## Goal
Move output formatting out of `src/main.py` into `src/output.py`: plain-text (done), JSON, and table paths.

## Recommended approach
1. Extract the render logic (`src/main.py:31-58`).
2. Implement JSON + table paths; plain-text stays as-is.

## Acceptance — the loop's exit gate
- **Run**: `python3 -m py_compile src/output.py src/main.py && python3 -m py_compile src/config.py` → pass = exit 0.
