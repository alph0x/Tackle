---
initiative: {{INITIATIVE_NAME}}
started: {{DATE}}
source: docs/plans/{{INITIATIVE_NAME}}/board.md
points: docs/plans/{{INITIATIVE_NAME}}/points/
---
# Implement — {{INITIATIVE_NAME}}

Runs `board.md` in dependency order. If `board.md` is missing, run `/tackle-plan` first.

## Algorithm

Repeat while ready points exist, nothing blocks, and budget remains:

1. Read points in dependency order from `board.md` (fallback: `plan.md` §5).
2. Pick the first 🔴 point whose dependencies are 🟢.
3. Set it 🟡 in `board.md`.
4. Spawn the point team for that point per `team.md` (Solo/Pair/Pod/Squad); the Driver executes the briefing and runs its **Done-signal**, reviewers verify, and the Coordinator updates state.
5. If green per the guardrails above: set 🟢, append one line to `log.md`, continue.
6. If red: retry up to the loop budget (default 3). Still red → set ⏸, append blocker to `log.md`, stop and escalate.

## Guardrails

- Execution requires explicit intent (L2, the default autonomy rung in `AGENTS.md` §Autonomy): unless the user upfront asked for plan+execute, present the point's pre-attack summary and ask for confirmation before changing code; silence or ambiguity means stop.
- Maker/checker: the Driver's own done-signal run is informative, never gating. The 🟢-flipping run comes from an independent checker per `team.md`, with its evidence block recorded in `log.md`.
- Model binding: team spawns follow the role→tier bindings resolved by the workspace `AGENTS.md` §Model map — checker ≠ maker attempted, best-effort; when tiers cannot be pinned the map is advisory and the deviation is recorded in `log.md`, never blocking.
- Point closure (Full gate): every Full-gate point closes with `reports/P-0N-report.md` and a Coordinator sign-off section — human-signed for Solo L2 points; no sign-off, no 🟢 flip. Lite-gate points keep their evidence in `log.md`.
- Coordinator continuity: ONE logical Coordinator per execution; its continuity state lives in `coordinator.md` (a projection — canonical state stays in `board.md`/`log.md`).
- Regression sweep: before a point flips 🟢, re-run the done-signals of every 🟢 point whose Touches intersect; any failure reopens that point (🟢 → 🟡) and blocks the current one.
- Never edit a 🟢 point.
- Never start a point whose dependencies are not 🟢.
- Always update `board.md` before appending `log.md`.
- Preserve `log.md` append-only rule.
- Chat history is not state; `board.md` + `log.md` is.

## Output contract

- Updated `board.md` with each touched point marked 🟢 or ⏸.
- One new append-only entry in `log.md` per touched point.
- Chat response: status line, digest, action footer.

## One-step mode

`/tackle-next` runs the same algorithm for exactly one ready point and returns.
