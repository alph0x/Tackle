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
5. Spawn the point team for that point per `team.md` (Solo/Pair/Pod/Squad); the Driver executes the briefing and runs its **Done-signal**, reviewers verify, and the Coordinator updates state.
6. If green: set status to 🟢, append `log.md`, return.
7. If red: retry up to the loop budget; if still red, set status to ⏸, append `log.md`, stop and escalate.

## Guardrails

- Confirmation (L2): unless the user upfront asked for plan+execute, present the pre-attack summary and ask before changing code; silence or ambiguity means stop.
- Maker/checker: the Driver's done-signal run is informative, never gating; an independent checker's run flips 🟢, with its evidence block recorded in `log.md`.
- Model binding: team spawns follow the role→tier bindings resolved by the workspace `AGENTS.md` §Model map — checker ≠ maker attempted, best-effort; when tiers cannot be pinned the map is advisory.
- Point closure (Full gate): the point closes with `reports/P-0N-report.md` and a Coordinator sign-off — human-signed for Solo L2 points; no sign-off, no 🟢 flip.
- Coordinator continuity: ONE logical Coordinator per execution; its continuity state lives in `coordinator.md`.
- Regression sweep: before 🟢, re-run done-signals of every 🟢 point with intersecting Touches; any failure reopens that point (🟢 → 🟡) and blocks this one.

Do not continue to the next point.
