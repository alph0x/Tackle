# P-01 — Plan lookup helper

Traces to: plan §1 · Depends on: none · Touches: `users.py` · Lenses: correctness, security

## Goal (single responsibility)

`python3 users.py` prints `ada -> pro`; the lookup helper resolves a customer name to a plan.

## Context

- `users.py:11 — "def get_plan(db, name):"` — the lookup helper.

## Done-signal

- `python3 users.py` exits 0 and its output contains `ada -> pro`.

## Acceptance

- [ ] Done-signal output pasted in `reports/P-01-report.md`.
