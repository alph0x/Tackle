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
4. Read its briefing (`points/P-0N-*.md`) and execute it as the Driver.
5. Run its **Done-signal**.
6. If green: set 🟢, append one line to `log.md`, continue.
7. If red: retry up to the loop budget (default 3). Still red → set ⏸, append blocker to `log.md`, stop and escalate.

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
