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
5. If green: set 🟢, append one line to `log.md`, continue.
6. If red: retry up to the loop budget (default 3). Still red → set ⏸, append blocker to `log.md`, stop and escalate.

## Guardrails

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
