# P-port-docs — docs update

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS point from this file alone.

## Status & wiring
**Depends on**: P-port-output · execution status in `board.md`.
- **Traces to**: `plan.md §6.2`.

## Goal
Update the README and the `portable --help` usage text to match the extracted modules.

## Recommended approach
1. Run `python3 main.py --help` and compare against the README.
2. Update both to describe the plain-text / JSON / table formats.

## Acceptance — the loop's exit gate
- **Run**: `grep -q "format" README.md` → pass = exit 0.
