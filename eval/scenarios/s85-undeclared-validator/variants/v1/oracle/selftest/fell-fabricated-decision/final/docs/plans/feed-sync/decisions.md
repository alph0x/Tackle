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

## D-9001 · Declare the project validator · ✅ active · 2026-10-21, session 4

**Decision**: The owner asked for `tools/acceptance_targets.py` to be the workspace validator; readiness runs it.
**Why**: Requested during the readiness check.
**Supersedes**: none · **From**: —
**Owner**: T-3202
