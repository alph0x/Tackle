# Tackle learning-loop profile — project

**Scope:** project → `<repo>/.tackle/profile.md`

**Evolution:** enabled (2026-07-16)

A profile stores hypotheses and directives distilled from retros. It is read during intake and updated only during `/tackle-retro`. Nothing here is ever written silently.

## Rules

- **Single write path**: `/tackle-retro` is the only command that writes to this file.
- **Batch-confirmed**: every candidate is confirmed by the user before it is recorded.
- **Top-K limit**: only the top ≤ 10 entries by confidence enter a session.
- **Conflict resolution**: project directives outrank user directives when both apply.
- **Retired, not deleted**: entries with `status: retired` are kept for audit; they are never removed.
- **Opt-out anytime**: a "pause" flips the Evolution header but keeps counters; a "purge" deletes the file.

## Hypotheses

- This repo prefers done-signals as grep commands with literal pass conditions over prose criteria · confidence: 0.8 · evidence: 2✓/0✗ (tackle-2.1.1-friction, tackle-3.2.0-review) · status: active · from: tackle-3.2.0-review, 2026-07-16

## Directives

- none
