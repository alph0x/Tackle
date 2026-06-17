---
initiative: {{INITIATIVE_NAME}}
started: {{DATE}}
source: docs/plans/{{INITIATIVE_NAME}}/board.md
points: docs/plans/{{INITIATIVE_NAME}}/points/
---

# Implement — {{INITIATIVE_NAME}}

## How this file was produced

This execution plan is rendered from `references/sdd/implement.tmpl.md` when the user says `/tackle-implement` or `tackle-implement`. It operates on the canonical status board in `docs/plans/{{INITIATIVE_NAME}}/board.md` and the point briefings in `docs/plans/{{INITIATIVE_NAME}}/points/P-0N-*.md`. The decomposition table in `plan.md §5` is the single source of execution order; the loop only advances statuses, never reorders points.

If `board.md` is missing, suggest running `/tackle-plan` first, then produce a degraded note and stop.

## Inputs

1. `docs/plans/{{INITIATIVE_NAME}}/board.md` — canonical status board (dependency order + statuses).
2. `docs/plans/{{INITIATIVE_NAME}}/plan.md` §5 — point decomposition table (fallback order source if `board.md` is degraded).
3. The relevant `points/P-0N-*.md` briefings — each carries a recommended starting prompt and a runnable **Done-signal**.
4. `docs/plans/{{INITIATIVE_NAME}}/AGENTS.md` — loop budget and team rules.

## Execution loop algorithm

Repeat until no 🔴 or 🟡 points remain, a point blocks, or the loop budget is exhausted:

1. **List points in dependency order** from `board.md` (or `plan.md §5` as fallback).
2. **Pick the first 🔴 point** whose dependencies are 🟢 (or have no dependencies).
3. **Set its status to 🟡 in `board.md`**.
4. **Read the point briefing** (`points/P-0N-*.md`) and extract its `Recommended starting prompt` and `Done-signal`.
5. **Execute the point** as the implementer (Driver). Follow the briefing; only the Driver writes code.
6. **Run the point's `Done-signal`**.
7. **If green** (exit 0):
   - Set status to 🟢 in `board.md`.
   - Append a `log.md` entry: date, point ID, status 🟢, one-line result.
   - Continue to the next ready point.
8. **If red** (non-zero):
   - Retry up to the loop budget (default 3 attempts; obey any point-specific override).
   - If still red after retries:
     - Set status to ⏸ in `board.md`.
     - Append a `log.md` entry: date, point ID, status ⏸, blocker summary.
     - Stop the loop and escalate to the user.

## Guardrails

- Never edit a 🟢 point.
- Never start a point whose dependencies are not 🟢.
- Always update `board.md` before appending `log.md`.
- Preserve `log.md` append-only rule.
- Chat history is not state; the workspace (`board.md` + `log.md`) is the canonical state machine.

## Output contract

When the loop finishes, the workspace contains:

- Updated `board.md` with each touched point marked 🟢 or ⏸.
- One new append-only entry in `log.md` per touched point.
- Chat response: status line (`🟢 on track` / `🟡 needs your input` / `🔴 blocked`), concise digest, and the action footer.

## One-step mode

For `/tackle-next`, use the same algorithm but execute exactly one ready point and return; do not continue to the next point. See `references/sdd/next.tmpl.md` (optional one-step wrapper).
