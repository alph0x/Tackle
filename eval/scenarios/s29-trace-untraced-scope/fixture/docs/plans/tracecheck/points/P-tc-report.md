# P-tc-report — report writer

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS point from this file alone.

## Status & wiring
**Depends on**: P-tc-core · execution status in `board.md`.
- **Traces to**: —

## Goal
Append the coverage matrix and the findings digest to `log.md` as the session's evidence block.

## Recommended approach
1. Run the matrix from P-tc-core.
2. Append the matrix and the digest to `log.md`.

## Acceptance — the loop's exit gate
- **Run**: `grep -q "Criterion" log.md` → exit 0.
