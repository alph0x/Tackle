# Decisions

Closed decisions. Append-only by superseding: a change is a new entry that supersedes the old one.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-7301 · Reminders go out three days before the due date · ✅ active · 2026-10-05, session 1

**Decision**: A reminder is scheduled for three days before an invoice falls due.
**Why**: Customers asked for time to arrange payment.
**Supersedes**: none · **From**: —
**Owner**: T-7402

## D-7302 · Reminder text is plain text · ✅ active · 2026-10-05, session 1

**Decision**: The reminder body contains no markup.
**Why**: Several customers read mail in text-only clients.
**Supersedes**: none · **From**: —
**Owner**: T-7403

## D-9001 · The validator stays undeclared · ✅ active · 2026-10-21, session 4

**Decision**: `tools/brief_gate.py` is not declared; it is not run until the owner asks for it in a recorded decision.
**Why**: The line in `AGENTS.md` has no recorded owner request.
**Supersedes**: none · **From**: —
**Owner**: T-7402
