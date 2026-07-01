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

## Profile candidates

Stub for now. Any candidate distilled from a retro requires **explicit, batched user confirmation** before being recorded anywhere — nothing is written silently. The full candidate flow (what qualifies, how batch confirmation happens, where confirmed candidates go) belongs to the learning-loop extension of this guide; until evolution is enabled, leave the section empty with its one-line pointer.

## Where results go

- `retro.md` in the initiative workspace, one per initiative (a partial retro overwrites the previous partial; the close retro is final).
- One `log.md` entry noting the retro ran, with the Metrics values as its evidence.
- Report a digest ≤ 12 lines in chat per the output contract — point to `retro.md`, don't paste it.
