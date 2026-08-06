# P-tc-core — matrix engine

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS point from this file alone.

## Status & wiring
**Depends on**: none · execution status in `board.md`.
- **Traces to**: `plan.md` §6.1 (coverage matrix).

## Goal
The trace output for this plan shows one row per §6 acceptance criterion, statuses `covered` / `gap`.

## Recommended approach
1. Read `plan.md` §6 criteria and each point briefing's `Traces to` line.
2. Emit `| Criterion | Points | Status |` rows with `covered` / `gap` statuses.

## Acceptance — the loop's exit gate
- **Run**: matrix row count equals the §6 criterion count, recorded in `log.md`.
