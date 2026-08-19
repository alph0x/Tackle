# Step 9 — Status / List / Next

- **Status**: read-only digest from `board.md` + last log snapshot; report grounding age and the re-ground recommendation per the Resume rule (`guides/resume.md`).
- **List**: scan `docs/plans/*/`; one line each.
- **Next**: print the next ready point's pre-attack summary + ready-to-paste prompt.

## /tackle-pulse — standing-loop digest

Triggered by `/tackle-pulse` or "pulse" — typically by a scheduler: cron, a CI job, a platform automation, anything that can start an agent session. The scheduler is the harness's business; Tackle defines only the contract of the invocation.

**Non-mutating.** A pulse reads `board.md`, `decisions.md`, the newest `log.md` entry (heading `## YYYY-MM-DD` to end of file), and `questions.md` if any question is open — never the full `log.md`; full-history reads belong to retro mining, which reads the archive pair. It may run the documented check commands — citation-drift checks, the lint table, the regression sweep — none of which modify the tree. The only write allowed is an optional `log.md` entry marked `pulse`. It never edits source or board and never executes points; execution still requires explicit intent.

**One digest, ≤ 12 lines**, one line per item:

1. Stale citations (`tackle-check probe` result, plus grounding age vs the workspace window).
2. The `lint: N/M checks passed` score line.
3. Regression-sweep result.
4. Cross-initiative collisions.
5. Blocked points with their escalation packets.
6. The next ready point with its ready-to-paste starting prompt.
7. The weakest-link line — the initiative's weakest-link point: point id + grade + one-line reason (effective confidence = min over the dependency chain, a documented hand computation over `board.md` + the `plan.md` §5 graph).
8. Usage so far (optional) — tokens by phase from `usage.md` when the workspace carries one (report the `n/a`-row count too); omit the line when there is no `usage.md`.
9. `log.md` size vs its archive threshold (lint row 13); over ⇒ recommend the archive protocol — a pulse never archives.

The point of the digest: a human skimming notifications stays the engineer in the loop. On a busy workspace, counts + pointers, never listings. Status may reuse the pulse machinery internally.

## Archive (on consent)

Pulse and status are read-only — they never archive. On an explicit user ask, run the `log.tmpl.md` archive protocol: move entries older than the last 5 sessions **verbatim** from `log.md` to `log-archive.md` (append, ascending), never edit moved entries, and confirm the newest entry still carries its State snapshot. Threshold: `Log archive threshold: N` in the workspace `AGENTS.md`, default 400 lines. Close with a one-line `log.md` entry recording the archive (entries moved, line counts before/after). Lint row 6 covers the archive pair's ordering.
