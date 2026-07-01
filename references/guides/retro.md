# Retro — initiative retrospective (/tackle-retro)

Triggered by `/tackle-retro [initiative]` or a natural phrase like "retro" / "how did it go". Runs at initiative close — every point 🟢 or the initiative abandoned — or on demand mid-flight as a **partial retro** (say so in the artifact title).

**Principle: detection before judgment.** Mine `board.md` + `log.md` by grep/count first; use judgment only to distill the counts into lessons. Read-only over `board.md`, `log.md`, `decisions.md`; the only writes are `docs/plans/<initiative>/retro.md` (instantiated from `references/retro.tmpl.md`) and one `log.md` entry.

## Metrics — mined, not remembered

Every metric carries a copy-paste recipe; the recipes live in the template's Metrics table. What each one measures:

- **Points by status** — count the status-emoji rows in `board.md`.
- **Attempts over budget** — count `attempt N:` journal lines per point in `log.md` against the attempt budget declared in the workspace `AGENTS.md`.
- **Blocked durations** — dates between the log entry that marks a point ⏸ and the entry that unblocks it.
- **Reopened points** — `🟢 → 🟡` transitions in `log.md` (regression-sweep reopenings included).
- **Comprehension debt** — points that flipped 🟢 with no human review recorded in the log: mechanically done, humanly unread. High comprehension debt is a warning even when the board is all green.

**Lite plans** (no `board.md`): the retro still runs — board-derived metrics report `n/a`; log-derived ones stand.

## What worked / what didn't / lessons

Distill from the metrics plus the Decisions and Blockers sections of the log. One line each. A lesson must be actionable by a future plan ("gate X earlier", "the attempt budget was too low for points shaped like Y"), not a platitude.

## Profile candidates (learning loop)

The learning loop is the only mechanism that lets Tackle adapt to a user or project. It is opt-in, per scope, and never silent.

### Opt-in (asked once per scope)

At the first learning opportunity, ask per scope:

- **Both scopes** if neither `~/.tackle/user-profile.md` nor `.tackle/profile.md` exists.
- **Project only** if the user profile already exists and is enabled.

A "no" writes the disabled stub (`Evolution: disabled (YYYY-MM-DD)`) in the relevant profile file and is never re-asked. The user can flip it later by enabling evolution or deleting the file.

### Distilling candidates

Mine the following sources during retro:

- `decisions.md` deltas vs recommended defaults (recurring overrides).
- `log.md` attempt-journal lines that exceed the budget or show no-progress.
- Reopened points (`🟢 → 🟡`) in `log.md`.
- Escalation packets from `log.md`.
- `/tackle-verify` findings that recurred across points.

Present candidates as a batch. Each candidate must include:

- A hypothesis or directive entry.
- The supporting evidence count.
- A proposed confidence (0.0–1.0).

### Confirming and writing

Everything is batch-confirmed by the user before writing. Never append to a profile without an explicit "yes".

For each confirmed candidate:

- Update counters from intake tally lines: `profile proposals: N accepted, M overridden (<which>)`.
- Accept ⇒ increment ✓; override ⇒ increment ✗.
- If ✗ ≥ 3 with confidence < 0.3, set `status: retired` (kept, never deleted).
- If a project hypothesis is confirmed in ≥ 2 repos, propose promoting it to the user profile (ask again).

### Directives

Recurring failure evidence may propose a `directive:` entry (C-20). A directive targets a named template or guide section and is applied on top of the resolution stack at instantiation time. Project directives outrank user directives. A directive whose target section no longer exists is flagged **stale** for re-confirm-or-retire.

### Opt-out anytime

The user can stop evolution at any moment, per scope, with any phrasing. Two modes:

- **Pause**: flip the header to `Evolution: disabled (YYYY-MM-DD)`. Counters are kept; re-enabling resumes them.
- **Purge**: delete the profile file entirely. The next learning opportunity may re-ask for opt-in.

Both take effect immediately.

## Where results go

- `retro.md` in the initiative workspace, one per initiative (a partial retro overwrites the previous partial; the close retro is final).
- One `log.md` entry noting the retro ran, with the Metrics values as its evidence.
- Report a digest ≤ 12 lines in chat per the output contract — point to `retro.md`, don't paste it.
