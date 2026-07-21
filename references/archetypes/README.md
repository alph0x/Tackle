# Plan archetypes

A plan archetype is a **proven decomposition skeleton** — the shape of an initiative that closed with its plan intact, distilled so a future intake can reuse it without re-deriving it. Archetypes are knowledge, not templates to paste blindly: intake offers them as proposals, the user decides.

## File format

One file per archetype: `references/archetypes/<name>.md`, kebab-case name. Sections, in order:

- **Name and one-line summary** — what shape of initiative this skeleton fits.
- **Point list** — the points as they were decomposed (titles + one-line responsibility each).
- **Edge pattern** — which dependencies wired the points together (the dependency-graph shape, not just a count).
- **Wave shape** — how the points fanned into execution waves.
- **Trap warnings** — what nearly (or did) break: budgets hit, reopened points, sections that drifted from the contract.
- **Provenance** — which initiative proved this skeleton, and its retro link.

## Write path — single

Only `/tackle-retro` writes archetypes. Never hand-author or hand-edit a file here outside a retro; extraction is offered at initiative close when the decomposition held. Everything is batch-confirmed by the user before writing (see `guides/retro.md` §Plan archetype candidates).

## Read path — intake

Intake Step 1 reads this directory alongside profiles (see `guides/intake-and-gate.md` §Learning-loop read). When an archetype matches the incoming initiative's shape, intake offers its skeleton as a tagged proposal — `(from archetype <name>)` — never a silent default. The user may accept, adapt, or override; overrides are retro material.
