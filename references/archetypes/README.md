<a id="plan-archetypes"></a>
# Reference plans

A reference plan is a **proven decomposition skeleton** — the shape of an initiative that closed with its plan intact, distilled so a future intake can reuse it without re-deriving it. Reference plans are knowledge, not templates to paste blindly: intake offers them as proposals, the user decides.

## File format

One file per reference plan (legacy archetype): `references/archetypes/<name>.md`, kebab-case name. Sections, in order:

- **Name and one-line summary** — what shape of initiative this skeleton fits.
- **Task list** — the tasks as they were decomposed (titles + one-line responsibility each).
- **Edge pattern** — which dependencies wired the tasks together (the dependency-graph shape, not just a count).
- **Wave shape** — how the tasks fanned into execution waves.
- **Trap warnings** — what nearly (or did) break: budgets hit, reopened tasks, sections that drifted from the contract.
- **Provenance** — which initiative proved this skeleton, and its retro link.

## Write path — single

Only the `retro` workflow writes reference plans. Never hand-author or hand-edit a file here outside a retro; extraction is offered at initiative close when the decomposition held. Everything is batch-confirmed by the user before writing (see `guides/retro.md` §Reference plan candidates).

## Read path — intake

PLAN intake reads this directory alongside profiles (see `guides/intake-and-gate.md` §Learning-loop read). When a reference plan matches the incoming initiative's shape, PLAN offers its skeleton as a tagged proposal — `(from archetype <name>)` — never a silent default. The user may accept, adapt, or override; overrides are retro material.

Existing extracted plans are historical learning records: preserve their original names, wording, IDs and provenance. Read `Point list` as the legacy form of `Task list`; naming does not authorize rewriting those records.
