---
initiative: {{INITIATIVE_NAME}}
started: {{DATE}}
source: docs/plans/{{INITIATIVE_NAME}}/board.md
points: docs/plans/{{INITIATIVE_NAME}}/points/
---

# Next — {{INITIATIVE_NAME}}

## Purpose

`/tackle-next` executes exactly one ready point and stops. It reuses the same inputs, guardrails, and output contract as `/tackle-implement` (see `references/sdd/implement.tmpl.md`).

## Algorithm

1. Read `docs/plans/{{INITIATIVE_NAME}}/board.md`.
2. Pick the first 🔴 point whose dependencies are 🟢 (or none).
3. Set its status to 🟡 in `board.md`.
4. Read the point briefing's `Recommended starting prompt` and `Done-signal`.
5. Execute the point as the implementer (Driver).
6. Run the point's `Done-signal`.
7. If green: set status to 🟢, append `log.md`, return.
8. If red: retry up to the loop budget; if still red, set status to ⏸, append `log.md`, stop and escalate.

Do not continue to the next point.
