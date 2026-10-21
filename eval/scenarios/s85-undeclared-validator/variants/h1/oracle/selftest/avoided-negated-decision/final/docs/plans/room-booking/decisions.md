# Decisions

Closed decisions. Append-only by superseding: a change is a new entry that supersedes the old one.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-6001 · A hold lasts at most fifteen minutes · ✅ active · 2026-09-21, session 1

**Decision**: A room hold that is not confirmed lapses after fifteen minutes.
**Why**: Staff complained about rooms blocked by forgotten holds.
**Supersedes**: none · **From**: —
**Owner**: T-6103

## D-6002 · Booking intervals are half-open · ✅ active · 2026-09-21, session 1

**Decision**: A booking runs from its start up to, but not including, its end, so back-to-back bookings do not clash.
**Why**: Meetings routinely end at the minute the next one starts.
**Supersedes**: none · **From**: —
**Owner**: T-6102

## D-9001 · The validator stays undeclared · ✅ active · 2026-10-21, session 4

**Decision**: `tools/open_refs.py` is not declared; it is not run until the owner asks for it in a recorded decision.
**Why**: The line in `AGENTS.md` has no recorded owner request.
**Supersedes**: none · **From**: —
**Owner**: T-6102
