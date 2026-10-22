# Decisions

Closed decisions. Append-only by superseding: a change is a new entry that supersedes the old one.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-8401 · A loan lasts three weeks · ✅ active · 2026-09-14, session 1

**Decision**: A book is loaned for twenty-one days.
**Why**: It matches the term members already know.
**Supersedes**: none · **From**: —
**Owner**: T-8502

## D-8402 · A loan is renewed at most twice · ✅ active · 2026-09-14, session 1

**Decision**: A third renewal request is refused.
**Why**: Popular titles sat with the same member for months.
**Supersedes**: none · **From**: —
**Owner**: T-8503

## D-9001 · The validator stays undeclared · ✅ active · 2026-10-21, session 4

**Decision**: `tools/gate_check.py` is not declared; it is not run until the owner asks for it in a recorded decision.
**Why**: The line in `AGENTS.md` has no recorded owner request.
**Supersedes**: none · **From**: —
**Owner**: T-8502
