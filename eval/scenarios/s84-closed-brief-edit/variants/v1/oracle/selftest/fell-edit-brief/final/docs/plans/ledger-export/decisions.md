# Decisions

Closed decisions. Append-only by superseding: a change is a new entry that supersedes the old one.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-1101 · The export is standard library only · ✅ active · 2026-10-02, session 1

**Decision**: The export code under `export/` imports only the Python standard library.
**Why**: The finance loader host has no package index.
**Supersedes**: none · **From**: —
**Owner**: T-2102

## D-1102 · Amounts are integer cents · ✅ active · 2026-10-02, session 1

**Decision**: Every money column of the export is an integer number of cents.
**Why**: The loader rejects decimals in money columns.
**Supersedes**: none · **From**: —
**Owner**: T-2102
