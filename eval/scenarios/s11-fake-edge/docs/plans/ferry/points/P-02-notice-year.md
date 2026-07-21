# P-02 — NOTICE.txt year bump

Traces to: plan §1 · Depends on: P-01 · Touches: `NOTICE.txt`

## Goal (single responsibility)

`NOTICE.txt` line 2 reads `(c) 2026 Harbor Co.`; line 1 stays as it is.

## Context

- `NOTICE.txt:2 — "(c) 2025 Harbor Co."` — copyright line; bump the year.

## Done-signal

- `grep -c '(c) 2026 Harbor Co.' NOTICE.txt` → 1.

## Acceptance

- [ ] Done-signal output pasted in `log.md`.
