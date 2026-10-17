# Design contract — {{TITLE}} (authoritative surface)

Use this depth artifact when several Tasks must agree on an API, serialization shape, state
machine, error taxonomy or protocol: a shared contract, not a second plan. A Task
briefing stays self-contained and inlines the clauses it implements.

**This file defines observable behavior:** required semantics, exact bytes or
ordering only where consumers depend on them, valid alternatives where they do not, and
failure behavior for invalid transitions or unknown inputs. A Task cannot silently diverge:
record a superseding decision, update this contract, then regenerate affected compiled Task
clauses in the same change. Seal each stable section with `<!-- SEALED: D-xx -->`; a later
change uses `<!-- SEALED: D-yy supersedes D-xx -->` and keeps the earlier decision traceable.
Each clause keeps a stable id in its heading (`## C02 · Interface`); a compiled clause runs from
that heading through the line before the next `## ` heading or `<a id=` line.

## C01 · Purpose and scope

{{User-visible or integration outcome, boundaries, non-goals, requirement ids.}}

## C02 · Interface

{{Public types, functions, entry/exit points, inputs, outputs, allowed semantic forms.}}

## C03 · States and transitions

{{Every state and legal transition. An invalid transition has an explicit ignored, recoverable
or typed terminal result; undefined behavior is not a contract.}}

## C04 · Errors and recovery

{{Typed error cases, diagnostic content, retry/abort behavior, handling of unknown or
unmapped inputs. Preserve original codes where mapping is unavailable.}}

## C05 · Invariants and quality constraints

{{Structural properties as observable checks: data preservation, effect boundaries,
material complexity or dependency limits, integration fit, relevant quality axes. Impose
no layers, formatting, dependencies or design patterns without a consumer need.}}

## C06 · Cases and valid alternatives

| Case | Given | Required observation | Invalid observation |
|---|---|---|---|
| {{normal}} | {{...}} | {{...}} | {{...}} |
| {{boundary}} | {{...}} | {{...}} | {{...}} |

Say explicitly when whitespace, key order, implementation shape or equivalent algorithms are
irrelevant; state required bytes, order, paths, stdio or exits exactly.

<a id="point-map-and-compiler-procedure"></a>
## Task map and compiler procedure

| Contract clause | Task(s) | Produced/consumed artifact | Regression check |
|---|---|---|---|
| {{clause id}} | {{T-0N}} | {{artifact}} | {{check}} |

The compiler copies selected clauses with their id, revision and hash into each Task and
checks coverage both ways: every requirement reaches a Task, every Task has a
traceable requirement. When this contract changes, supersede the decision first, regenerate
dependent Task clauses, re-ground their inputs and rerun affected checks. Never edit a
compiled copy to make it agree by itself.
