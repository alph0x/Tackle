# Design contract — {{TITLE}} (authoritative surface)

> **Full-gate depth artifact (optional).** Create this only when the initiative defines a
> public surface that several points must agree on — an API, a wire/serialization format, a
> state machine, an error taxonomy, a protocol between components. If the work has no shared
> contract, skip it and let each point's briefing stand alone.

**This file is normative. Points implement it; they do not redefine it.** A point's briefing
*sketches* approach; this contract *defines* the surface. If a point needs to deviate,
**supersede the spec FIRST** (edit this file + record a `D-xx`), then write the divergent code.
That keeps every point agreeing on one source instead of drifting apart.

When the contract stabilizes, each named section heading gains the seal marker
`<!-- SEALED: D-xx -->` (D-xx = the sealing decision) on the heading line. The supersede-first
flow then also updates the marker — `<!-- SEALED: D-yy supersedes D-xx -->` — so every
deviation leaves a grep-able trail.

Map each section to the points that implement it so coverage is auditable.

## Signatures / API surface
{{The exact public types, functions, entry/exit points. One entry, one exit where possible.}}

## States & transitions
{{If there's a lifecycle/state machine: every state, every legal transition. Invalid
transitions are defined (ignored/typed-error), never undefined behavior.}}

## Error model
{{The typed error space — every case, recoverable vs terminal, and how unknown/unmapped
inputs are handled (preserve the original code; unmapped ≠ terminal crash).}}

## Invariants / policies (structural, verifiable)
{{The properties that must always hold — phrased so they can be tested, not just asserted in
prose. e.g. "recoverable vs terminal is structural: recoverable failures appear as state with
retry/abort; anything thrown from result() is terminal." "Core compiles with zero
dependencies." Promote each load-bearing invariant into `plan.md` §6.1 (or a point's done-signal) so it's an actual pass/fail check, not prose.}}

## Spec → point map
| Spec section | Implemented by |
|---|---|
| {{§ signatures}} | {{P-0x}} |
