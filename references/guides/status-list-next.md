# Step 9 — Status / List / Next

- **Status**: read-only digest from `board.md` + last log snapshot; report grounding age and the re-ground recommendation per the Resume rule (`guides/resume.md`).
- **List**: scan `docs/plans/*/`; one line each.
- **Next**: print the next ready point's pre-attack summary + ready-to-paste prompt.

## /tackle-pulse — standing-loop digest

Triggered by `/tackle-pulse` or "pulse" — typically by a scheduler: cron, a CI job, a platform automation, anything that can start an agent session. The scheduler is the harness's business; Tackle defines only the contract of the invocation.

**Non-mutating.** A pulse reads the state files first (`board.md`, `log.md`, `decisions.md`, and `questions.md` if any question is open) and may run the documented check commands — citation-drift checks, the lint table, the regression sweep — none of which modify the tree. The only write allowed is an optional `log.md` entry marked `pulse`. It never edits source or board and never executes points; execution still requires explicit intent.

**One digest, ≤ 12 lines**, one line per item:

1. Stale citations (grounding age vs the workspace window).
2. The `lint: N/M checks passed` score line.
3. Regression-sweep result.
4. Cross-initiative collisions.
5. Blocked points with their escalation packets.
6. The next ready point with its ready-to-paste starting prompt.
7. The weakest-link line — the initiative's weakest-link point: point id + grade + one-line reason (effective confidence = min over the dependency chain, a documented hand computation over `board.md` + the `plan.md` §5 graph).

The point of the digest: a human skimming notifications stays the engineer in the loop. On a busy workspace, counts + pointers, never listings. Status may reuse the pulse machinery internally.
