# Tackle learning-loop profile — project

**Scope:** project → `<repo>/.tackle/profile.md`

**Evolution:** enabled (2026-08-04)

A profile stores hypotheses and directives distilled from retros. It is read during intake and updated only during `/tackle-retro`. Nothing here is ever written silently.

## Rules

- **Single write path**: `/tackle-retro` is the only command that writes to this file.
- **Batch-confirmed**: every candidate is confirmed by the user before it is recorded.
- **Top-K limit**: only the top ≤ 10 entries by confidence enter a session.
- **Conflict resolution**: project directives outrank user directives when both apply.
- **Retired, not deleted**: entries with `status: retired` are kept for audit; they are never removed.

## Hypotheses

- none

## Directives

- directive: commit messages use Conventional Commits type vocabulary (feat/fix/chore/docs/refactor), single-line subject, never a Co-Authored-By trailer · target: commit guidance · applies_to: commit-message · confidence: 0.7 · evidence: 5✓/0✗ · status: active · from: prior-initiative, 2026-08-04
