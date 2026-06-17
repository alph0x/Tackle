# Step 3 — Location & gitignore

Create `docs/plans/<initiative>/`. Ask the user if the plans directory should be gitignored. If yes, add `docs/plans/` to `.gitignore`.

# Step 4 — Scaffold the core

Copy templates from `references/` and fill `{{PLACEHOLDERS}}`. Delete unused sections. Never leave empty slots you won't fill.

## Depth artifacts

Create only when their trigger fires:
- `foundations.md` — grounding table (decision → principle → source).
- `design-contract.md` — authoritative public surface points implement.
- `execution-strategy.md` — waves + quality gate + deferral.
- `team.md` — execution team roles and protocol.
- `board.md` — canonical status board for execution.
- `reference-docs/` — read-only external snapshots.
