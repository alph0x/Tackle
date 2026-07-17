# Retro — Dime bill-splitter (draft)

Written at initiative close by mining `board.md` + `log.md`.

## Metrics

| Metric | Value |
|---|---|
| Points by status | 🔴 0 · 🟡 0 · ⏸ 0 · 🟢 3 |
| Attempts over budget | 1 (P-02: 4 attempts vs budget 3) |
| Blocked durations | none |
| Reopened points | 1 (P-01 🟢 → 🟡 → 🟢 after the P-03 regression sweep) |
| Comprehension debt | 0 |

## What worked

- Anchored citations caught a stale read before P-01 execution.
- Human review kept pace: every flip was read the same day.

## What didn't

- P-02 needed four attempts; float handling was under-scoped at planning.
- The P-03 change reopened P-01 late, at initiative close.

## Lessons

- Scope float/rounding risk explicitly in each point's Context section.
- Run the regression sweep right after each flip, not at initiative close.

## Profile candidates

- Over-budget attempts cluster on numeric/parsing points · confidence: 0.6 · evidence: 1✓/0✗ · from: dime, 2026-07-14
- Late regression sweeps reopen finished points; sweep right after each flip · confidence: 0.7 · evidence: 1✓/0✗ · from: dime, 2026-07-14
- directive: prefer half-up rounding defaults for money points · target: guides/decompose-and-lint.md · confidence: 0.5 · evidence: 1✓/0✗ · from: dime, 2026-07-14
