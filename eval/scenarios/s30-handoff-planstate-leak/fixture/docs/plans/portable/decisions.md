# Decisions — portable

Closed decisions — don't revisit without cause. Append-only by superseding; never edit history.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-01 · config module name · ✅ active · 2026-08-03, session 1

**Decision**: config loading lives in `src/config.py` (not `src/settings.py`).
**Why**: matches the existing `src/` layout; `settings` collides with the stdlib-adjacent naming used elsewhere.
**Supersedes**: none

## D-02 · formatter scope · ✅ active · 2026-08-04, session 2

**Decision**: output formatter supports plain-text, JSON, and table; no CSV path this round.
**Why**: JSON + table are the two requested formats; CSV was a maybe (adjacent to Q-02).
**Supersedes**: none
