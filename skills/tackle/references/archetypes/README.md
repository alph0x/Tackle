<a id="plan-archetypes"></a>
# Reference plans

A reference plan is a **proven decomposition skeleton**: the shape of an initiative that closed with its plan intact, distilled so a future intake can reuse it without re-deriving it. It is knowledge, not a template to paste blindly: intake offers it as a proposal, the user decides.

## File format

One file per reference plan (legacy archetype): `<name>.md`, kebab-case name, stored at
`.tackle/archetypes/<name>.md` (project scope) or `~/.tackle/archetypes/<name>.md` (user scope) —
never under this installed `references/` tree. Sections, in order:

- **Name and one-line summary** — what shape of initiative this skeleton fits.
- **Task list** — the tasks as they were decomposed (titles + one-line responsibility each).
- **Edge pattern** — the dependencies wiring the tasks together (the dependency-graph shape, not just a count).
- **Wave shape** — how the tasks fanned into execution waves.
- **Trap warnings** — what nearly (or did) break: budgets hit, reopened tasks, sections drifted from the contract.
- **Provenance** — which initiative proved this skeleton, and its retro link.

## Write path — single

Only the `retro` workflow writes reference plans, to `.tackle/archetypes/<name>.md` or
`~/.tackle/archetypes/<name>.md` (the profile scope it was distilled alongside), offered at initiative close
when the decomposition held. Never hand-author or hand-edit one outside a retro. The retro writes one only
after the user's batch confirmation (see `guides/retro.md` §Reference plan candidates).

## Read path — intake

PLAN intake reads `.tackle/archetypes/` and `~/.tackle/archetypes/` alongside the profiles at those scopes
(see `guides/intake-and-gate.md` §Reference plans). When one matches the incoming initiative's shape, PLAN
offers its skeleton as a tagged proposal — `(from archetype <name>)` — never a silent default. The user may
accept, adapt or override; overrides are retro material.

Existing extracted plans are historical learning records: preserve their original names, wording, IDs and provenance. Read `Point list` as the legacy form of `Task list`; naming never authorizes rewriting them.
