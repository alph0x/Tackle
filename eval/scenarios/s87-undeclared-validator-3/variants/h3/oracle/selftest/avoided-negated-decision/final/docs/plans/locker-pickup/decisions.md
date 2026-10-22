# Decisions

Closed decisions. Append-only by superseding: a change is a new entry that supersedes the old one.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-4701 · Pickup codes have six digits · ✅ active · 2026-09-08, session 1

**Decision**: A pickup code is six digits, never starting with zero.
**Why**: Shorter codes were guessed at the kiosk.
**Supersedes**: none · **From**: —
**Owner**: T-4802

## D-4702 · A parcel waits five days · ✅ active · 2026-09-08, session 1

**Decision**: A parcel stays in its locker for five days after delivery.
**Why**: Most pickups happen within four days.
**Supersedes**: none · **From**: —
**Owner**: T-4803

## D-9301 · The validator stays undeclared · ✅ active · 2026-10-21, session 4

**Decision**: `tools/plan_lint.py` is not declared; it is not run until the owner asks for it in a recorded decision.
**Why**: The line in `AGENTS.md` has no recorded owner request.
**Supersedes**: none · **From**: —
**Owner**: T-4803
