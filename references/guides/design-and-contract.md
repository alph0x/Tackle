# Step 5 — Briefing (ground in `file:line`)

For each point, write:
- Goal (single responsibility)
- Depends-on / Touches
- Context grounded in code
- Recommended approach
- Alternatives
- Done-signal (runnable command)
- Acceptance criteria

# Step 5.5 — Architecture recommendation

If Full, recommend an architecture. Record the decision as `D-xx` in `decisions.md`. Open `foundations.md` with the Clean Code + SOLID backbone.

The recommendation must cover:

- **Layers and dependency direction** — name the layers; source-code dependencies point inward, and nothing in an inner layer depends on an outer one (the dependency rule).
- **Boundary crossings** — how abstractions cross layers: interfaces are owned by the inner layer, implementations are plugged in from outside.
- **SOLID fit** — which checks apply to the chosen shape: SRP per layer and class, OCP at extension points, DIP across boundaries.
- **Foundations rows** — every structural choice gets a `foundations.md` row (decision → principle → source, per the backbone grounding rule).

# Step 5.75 — Stabilize the design contract (Full only)

Do not write point briefings until `design-contract.md` survives one full planning session unchanged. Points cite contract sections instead of inlining spec.
