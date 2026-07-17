# Log — Dime bill-splitter

## 2026-07-06

### Did
- Gate: Full (tie-breaker: handoff expected). Scaffold and briefings done.

### Decisions
- D-01: round half-up to cents (overrides the recommended banker's rounding).

## 2026-07-09

### Did
- P-01 attempt 1: stale citation, re-grounded.
- P-01 attempt 2: done-signal passed; P-01 flipped 🟢.
- Human review: P-01 diff read, confirmed.

## 2026-07-12

### Did
- P-02 attempt 1: no-progress (edited outside Touches).
- P-02 attempt 2: done-signal failed (share remainder leak).
- P-02 attempt 3: done-signal failed (float drift).
- P-02 attempt 4: passed; P-02 flipped 🟢.
- P-03 attempt 1: argparse default shadowed the positional.
- P-03 attempt 2: done-signal failed.
- P-03 attempt 3: passed; P-03 flipped 🟢.
- Regression sweep after P-03 reopened P-01 (🟢 → 🟡); re-verified, P-01 🟢 again.

### Blockers / open questions
- None.
