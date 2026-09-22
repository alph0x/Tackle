# Design contract — {{TITLE}} (authoritative surface)

Use this depth artifact when several Tasks must agree on an API, serialization shape, state
machine, error taxonomy, or protocol. It is a shared contract, not a second plan. A Task
briefing remains self-contained and inlines the clauses it implements.

**This file defines observable behavior.** It specifies required semantics, exact bytes or
ordering only where consumers depend on them, valid alternatives where they do not, and the
failure behavior for invalid transitions or unknown inputs. A Task cannot silently diverge:
record a superseding decision, update this contract, then regenerate affected compiled Task
clauses in the same change. Seal each stable section with `<!-- SEALED: D-xx -->`; a later
change uses `<!-- SEALED: D-yy supersedes D-xx -->` and keeps the earlier decision traceable.

## Purpose and scope

{{The user-visible or integration outcome, boundaries, non-goals, and requirement ids.}}

## Interface

{{Public types, functions, entry/exit points, inputs, outputs, and allowed semantic forms.}}

## States and transitions

{{Every state and legal transition. Invalid transitions have an explicit ignored, recoverable,
or typed terminal result; undefined behavior is not a contract.}}

## Errors and recovery

{{Typed error cases, diagnostic content, retry/abort behavior, and handling for unknown or
unmapped inputs. Preserve original codes where mapping is unavailable.}}

## Invariants and quality constraints

{{Structural properties expressed as observable checks: data preservation, effect boundaries,
complexity or dependency limits when material, integration fit, and relevant quality axes. Do
not impose layers, formatting, dependencies, or design patterns without a consumer need.}}

## Cases and valid alternatives

| Case | Given | Required observation | Invalid observation |
|---|---|---|---|
| {{normal}} | {{...}} | {{...}} | {{...}} |
| {{boundary}} | {{...}} | {{...}} | {{...}} |

If whitespace, key order, implementation shape, or equivalent algorithms are irrelevant, say so
explicitly. If bytes, order, paths, stdio, or exits are required, state them exactly.

<a id="point-map-and-compiler-procedure"></a>
## Task map and compiler procedure

| Contract clause | Task(s) | Produced/consumed artifact | Regression check |
|---|---|---|---|
| {{clause id}} | {{P-0N}} | {{artifact}} | {{check}} |

The compiler copies selected clauses with their id, revision, and hash into each Task. It
checks coverage in both directions: every requirement reaches a Task and every Task has a
traceable requirement. When this contract changes, supersede the decision first, regenerate
dependent Task clauses, re-ground their inputs, and rerun affected checks. Never edit a
compiled copy to make it agree by itself.
