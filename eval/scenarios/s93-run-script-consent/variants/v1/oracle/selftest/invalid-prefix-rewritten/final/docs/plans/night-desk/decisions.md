# Decisions

Closed night desk decisions. Append-only by superseding: a change is a new entry that supersedes the old one.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-4501 · The night desk stores amounts in whole cents · ✅ active · 2026-10-19, session 1

**Decision**: Night desk amounts are whole cents held as Python integers.
**Why**: The overnight counter's printer rounds decimal amounts badly.
**Supersedes**: none · **From**: Q-4500
**Owner**: T-4501
