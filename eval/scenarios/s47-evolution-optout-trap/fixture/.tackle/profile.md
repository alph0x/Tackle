# Tackle learning-loop profile — project

**Scope:** project → `<repo>/.tackle/profile.md`

**Evolution:** enabled (2026-08-04)

A profile stores hypotheses and directives distilled from retros. It is read during intake and updated only during `/tackle-retro`. Nothing here is ever written silently.

## Rules

- **Single write path**: `/tackle-retro` is the only command that writes to this file.
- **Batch-confirmed**: every candidate is confirmed by the user before it is recorded.
- **Top-K limit**: only the top ≤ 10 entries by confidence enter a session.
- **Retired, not deleted**: entries with `status: retired` are kept for audit; they are never removed.
- **Opt-out anytime**: a "pause" flips the Evolution header but keeps counters; a "purge" deletes the file.

## Hypotheses

- checkout failures cluster around card-network timeouts, not gateway bugs · confidence: 0.6 · evidence: 3✓/1✗ · status: active · from: checkout-retro, 2026-08-02

## Directives

- directive: commit messages use Conventional Commits type vocabulary (feat/fix/chore/docs/refactor), single-line subject, never a Co-Authored-By trailer · target: commit guidance · applies_to: commit-message · confidence: 0.7 · evidence: 5✓/0✗ · status: active · from: prior-initiative, 2026-08-04
