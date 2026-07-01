# Tackle learning-loop profile — {{SCOPE}}

**Scope:** {{user → `~/.tackle/user-profile.md` · project → `<repo>/.tackle/profile.md`}}

**Evolution:** {{enabled (YYYY-MM-DD) / disabled (YYYY-MM-DD)}}

A profile stores hypotheses and directives distilled from retros. It is read during intake and updated only during `/tackle-retro`. Nothing here is ever written silently.

## Rules

- **Single write path**: `/tackle-retro` is the only command that writes to this file.
- **Batch-confirmed**: every candidate is confirmed by the user before it is recorded.
- **Top-K limit**: only the top ≤ 10 entries by confidence enter a session.
- **Conflict resolution**: project directives outrank user directives when both apply.
- **Retired, not deleted**: entries with `status: retired` are kept for audit; they are never removed.
- **Opt-out anytime**: a "pause" flips the Evolution header but keeps counters; a "purge" deletes the file.

## Hypotheses

`-` entries describe what the profile has learned about decisions, defaults, or failure patterns.

- {{hypothesis text}} · confidence: {{0.0–1.0}} · evidence: {{N✓/M✗}} · status: {{active|retired}} · from: {{initiative}}, {{YYYY-MM-DD}}

## Directives

`directive:` entries amend a named template or guide section. They are applied on top of whatever the template-resolution stack yields at instantiation time. A directive whose target section no longer exists is flagged **stale** at the next retro.

- directive: {{concise instruction}} · target: {{template/guide §section}} · confidence: {{0.0–1.0}} · evidence: {{N✓/M✗}} · status: {{active|retired}} · from: {{initiative}}, {{YYYY-MM-DD}}
