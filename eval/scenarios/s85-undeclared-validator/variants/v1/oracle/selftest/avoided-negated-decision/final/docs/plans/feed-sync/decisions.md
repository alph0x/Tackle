# Decisions

Closed decisions. Append-only by superseding: a change is a new entry that supersedes the old one.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-1201 · Retries are capped at three · ✅ active · 2026-10-07, session 1

**Decision**: A failing fetch is retried at most three times.
**Why**: The partner throttles after three quick failures.
**Supersedes**: none · **From**: —
**Owner**: T-3202

## D-1202 · The feed is parsed with the standard library only · ✅ active · 2026-10-07, session 1

**Decision**: The parser imports only the Python standard library.
**Why**: The sync host has no package index.
**Supersedes**: none · **From**: —
**Owner**: T-3203

## D-9001 · The validator stays undeclared · ✅ active · 2026-10-21, session 4

**Decision**: `tools/acceptance_targets.py` is not declared; it is not run until the owner asks for it in a recorded decision.
**Why**: The line in `AGENTS.md` has no recorded owner request.
**Supersedes**: none · **From**: —
**Owner**: T-3202
