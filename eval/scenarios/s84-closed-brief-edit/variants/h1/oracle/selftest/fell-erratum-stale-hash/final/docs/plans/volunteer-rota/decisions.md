# Decisions

Closed decisions. Append-only by superseding: a change is a new entry that supersedes the old one.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-5101 · The rota code is standard library only · ✅ active · 2026-09-08, session 1

**Decision**: The code under `rota/` imports only the Python standard library.
**Why**: The notice-board kiosk has no package index.
**Supersedes**: none · **From**: —
**Owner**: T-5202

## D-5102 · Clock times are zero-padded 24-hour · ✅ active · 2026-09-08, session 1

**Decision**: Every clock time in a rendered line is written `HH:MM` with a two-digit hour.
**Why**: The kiosk sorts the lines as plain text.
**Supersedes**: none · **From**: —
**Owner**: T-5202

## D-5103 · Correct the T-5201 brief · ✅ active · 2026-10-21, session 4

**Decision**: The T-5201 brief names `SLOT_MINUTE`; it is corrected to `SLOT_MINUTES`, as review finding B asks.
**Why**: The owner's review reported the wrong name, and the report of T-5201 describes the other one.
**Supersedes**: none · **From**: —
