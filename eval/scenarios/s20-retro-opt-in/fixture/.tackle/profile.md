# Tackle learning-loop profile — project

**Scope:** project → `<repo>/.tackle/profile.md`

**Evolution:** enabled (2026-05-14)

A profile stores hypotheses and directives distilled from retros. It is read during intake and updated only during `/tackle-retro`. Nothing here is ever written silently.

## Rules

- **Single write path**: `/tackle-retro` is the only command that writes to this file.
- **Batch-confirmed**: every candidate is confirmed by the user before it is recorded.
- **Top-K limit**: only the top ≤ 10 entries by confidence enter a session.
- **Conflict resolution**: project directives outrank user directives when both apply.
- **Retired, not deleted**: entries with `status: retired` are kept for audit; they are never removed.
- **Opt-out anytime**: a "pause" flips the Evolution header but keeps counters; a "purge" deletes the file.

## Hypotheses

- Migrations need a rollback script before the flip · confidence: 0.8 · evidence: 2✓/0✗ · status: active · from: alpha-migration, 2026-07-30
- Payment refactors break silently unless the checkout smoke test runs first · confidence: 0.7 · evidence: 1✓/1✗ · status: active · from: alpha-migration, 2026-07-30

## Directives

- directive: keep the legacy route until the flip; never deprecate mid-wave · target: design-and-contract §contract · confidence: 0.6 · evidence: 1✓/1✗ · status: active · from: alpha-migration, 2026-07-30
