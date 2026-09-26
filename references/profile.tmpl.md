# Tackle learning-loop profile — {{SCOPE}}

**Scope:** {{user → `~/.tackle/user-profile.md` · project → `<repo>/.tackle/profile.md`}}

**Evolution:** {{enabled (YYYY-MM-DD) / disabled (YYYY-MM-DD)}}

A profile stores hypotheses and directives distilled from retros. It is read during intake and updated only during the `retro` workflow. Nothing here is ever written silently.

## Rules

- **Single write path**: the `retro` workflow is the only action that writes to this file.
- **Batch-confirmed**: every candidate is confirmed by the user before it is recorded.
- **Top-K limit**: only the top ≤ 10 entries by confidence enter a session.
- **Conflict resolution**: project directives outrank user directives when both apply.
- **Retired, not deleted**: entries with `status: retired` are kept for audit; they are never removed.
- **Opt-out anytime**: a "pause" flips the Evolution header but keeps counters; a "purge" deletes the file.

## Hypotheses

`-` entries describe what the profile has learned about decisions, defaults, or failure patterns.
`confidence` is computed by `guides/retro.md`'s confidence recipe (Wilson lower bound over the
entry's own `observations`), never typed by hand at write time. `id` never takes a task, decision or
question shape (`[PTDQRCM]-?[0-9]{2}`) or the workspace slug — `H01` and similar are enough. A
legacy entry with no `id` (prose `evidence: N✓/M✗`, or no confidence/evidence field at all) stays
readable; it gains a permanent `id` only the next retro that touches it assigns one.

- id: {{H-id}} · {{hypothesis text}} · confidence: {{computed}} (Wilson lower bound, z=1.96, n={{✓+✗}}) · observations: {{initiative}}:{{✓|✗|assumed}}@{{YYYY-MM-DD}}[; {{initiative}}:{{✓|✗|assumed}}@{{YYYY-MM-DD}} ...] · status: {{active|retired}}

## Directives

`directive:` entries amend a named template or guide section. Apply them to the named current section only when compatible with user instructions and the current contract. Select by applicability, version, evidence and supersession before confidence; a historical active hypothesis cannot override current rules. Incompatible entries stay preserved and unused until a confirmed retro disposition. A directive whose target section no longer exists is flagged **stale** at the next retro. A directive tagged `applies_to:` scopes to an action moment (e.g. `commit-message`, `pre-push`, `release`) instead of a template section; it binds when that action is about to happen, not at instantiation. `id`, `confidence` and `observations` follow the same computed, mechanically parseable format as Hypotheses above.

- id: {{A-id}} · directive: {{concise instruction}} · target: {{template/guide §section}} · applies_to: {{action moment — optional}} · confidence: {{computed}} (Wilson lower bound, z=1.96, n={{✓+✗}}) · observations: {{initiative}}:{{✓|✗|assumed}}@{{YYYY-MM-DD}}[; {{initiative}}:{{✓|✗|assumed}}@{{YYYY-MM-DD}} ...] · status: {{active|retired}}
