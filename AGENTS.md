# AGENTS — Tackle repo

Contract for any agent working in this repository (the Tackle skill itself), in any session — planning or not.

## Learning intake (session start, always)

Persisted learning from past retros MUST be considered before proposing defaults or starting work:

1. `.tackle/profile.md` — project learning-loop hypotheses (read if present; apply active entries, tagged `(from your profile)` when they shape a proposal).
2. `~/.tackle/user-profile.md` — user-level hypotheses (same rule).
3. `docs/seeds/*.md` — parked initiatives and the pending-skill-fixes intake list (offer applicable items when planning or when the user asks what is pending).

Write paths are exclusive: profiles are written ONLY by `/tackle-retro` (batch-confirmed); seeds are created/updated deliberately, never as a side effect. Never write either silently.

## Repo conventions

- The skill source is `SKILL.md` + `references/`; the entry file has a ≤1100-word budget and 11 core conventions (incl. authority order) — preserve both when editing.
- `docs/plans/` is gitignored (local workspaces); `docs/seeds/` is tracked.
- Any change that deletes normative content from `SKILL.md` or a guide requires the D-13 gate: rule-inventory diff + one behavioral eval run before release (see `references/guides/lint-spec.md` §Release sweep).
- Releases follow `references/CHANGELOG.md` discipline: granular commits, tag, GitHub release with the changelog entry as notes.
