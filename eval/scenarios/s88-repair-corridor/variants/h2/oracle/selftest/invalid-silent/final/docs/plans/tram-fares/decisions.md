# Decisions

Closed decisions. Append-only by superseding: a change is a new entry that supersedes the old one.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-4301 · Fare code is standard library only · ✅ active · 2026-09-21, session 1

**Decision**: `fares/` imports only the Python standard library.
**Why**: The ticket machines run a frozen interpreter.
**Supersedes**: none · **From**: —
**Owner**: T-4301, T-4302, T-4303

## D-4302 · T-4303 repair corridor approved · ✅ active · 2026-10-24, session 3

**Decision**: The owner, Jonas Albrecht, approves the repair corridor on the **Corridor** line of the
T-4303 brief exactly as written: files, invariants, budget, review time and verification command.
**Why**: The machines get their new build on Monday and the suite must be green for it.
**Supersedes**: none · **From**: Jonas Albrecht, owner, session 3
**Owner**: T-4303
