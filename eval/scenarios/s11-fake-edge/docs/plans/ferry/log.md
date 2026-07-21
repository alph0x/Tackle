# Log — Ferry fare board

## 2026-07-18

### Did
- Gate: Lite. Plan written, three points briefed and ready.

### Decisions
- None.

### Blockers / open questions
- None.

## /tackle-ground — 2026-07-19 10:12
Last-verified: 2026-07-19

- Plan: grounded (`fares.py:3 — "ADULT = 9.50"` ✓ · `NOTICE.txt:2 — "(c) 2025 Harbor Co."` ✓ · `README.md:3 — "Adult: $9.50"` ✓)

## /tackle-verify — 2026-07-21
Result: BLOCKED (2 MEDIUM findings — fake dependency edges).

### Findings
- V1 (MEDIUM, dependency sanity §5): `P-02` `Depends on: P-01` names no crossing artifact. P-01 outputs a fare constant/print line in `fares.py`; P-02 edits `NOTICE.txt:2` (year 2025→2026), consuming nothing from P-01. False edge, no `D-xx` waiver → cut.
- V2 (MEDIUM, dependency sanity §5): `P-03` `Depends on: P-02` names no crossing artifact. P-03 mirrors `Weekend: $12.00` into `README.md:3`; that value comes from P-01, not P-02's year bump. P-03 reads nothing from `NOTICE.txt`. False edge, no `D-xx` waiver → cut.
- Note: the only real relationship is P-01→P-03 (weekend fare value), and even that is a hardcoded mirror (P-03 done-signal greps a literal string, reads no upstream file) — at most ordering-only. P-02 is independent (disjoint `Touches: NOTICE.txt`), parallelizable.

### Blockers / open questions
- Execution held: fix/cut the two fake edges (or user explicitly accepts risk) before `/tackle-next`.
