# Tackle learning-loop profile — project

**Scope:** project → `<repo>/.tackle/profile.md`

**Evolution:** enabled (2026-08-05)

A profile stores hypotheses and directives distilled from retros. It is read during intake and updated only during `/tackle-retro`. Nothing here is ever written silently.

## Rules

- **Single write path**: `/tackle-retro` is the only command that writes to this file.
- **Batch-confirmed**: every candidate is confirmed by the user before it is recorded.
- **Top-K limit**: only the top ≤ 10 entries by confidence enter a session.
- **Conflict resolution**: project directives outrank user directives when both apply.
- **Retired, not deleted**: entries with `status: retired` are kept for audit; they are never removed.
- **Opt-out anytime**: a "pause" flips the Evolution header but keeps counters; a "purge" deletes the file.

## Hypotheses

- Tracked commits and docs must never reference gitignored plan state (plan paths, point ids, plan-local decisions) · confidence: 0.8 · evidence: 4✓/0✗ · status: active · from: codebase-quality-pass retro, 2026-07-18

## Directives

- none
