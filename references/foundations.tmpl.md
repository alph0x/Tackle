# Foundations — why each structural choice is the way it is

> **Full-gate depth artifact.** Create this for any Full initiative that introduces or shapes
> architecture (a new subsystem, a layering, a set of patterns). For a bounded change that
> only follows existing structure, skip it — the per-point "Recommended approach" is enough.

**The backbone is Clean Code + SOLID, grounded in the best referents of software design.**
Grounding rule (binding when this file exists): **every pattern or abstraction the plan
introduces gets a row here BEFORE it ships** — decision → principle → source. *"It felt
cleaner"* is not a justification. Reviewers verify a row exists and that the cited principle
actually fits; superseding a row requires superseding its decision (`D-xx`).

## Decision → principle → source (the standing choices)

Backbone: Clean Code + SOLID. Cite the *specific* referent per row (Martin/Beck/Fowler/GoF,
Cockburn/Evans/Parnas/Liskov/Meyer/Nygard, an RFC, the spec, the in-house module you mirror) —
the citation is the row's `Source`, so no separate canon table is needed.

| Choice (where it shows up) | Grounding (the principle) | Source (the referent) |
|---|---|---|
| {{the abstraction/pattern, + where in the code/spec}} | {{the principle it satisfies}} | {{the specific referent — e.g. Martin, Dependency Rule; or `Libraries/X`}} |

## How to use this file during execution

1. Reaching for a pattern not listed here → STOP, add the row (choice, grounding, source);
   if it changes structure, record a `D-xx` first.
2. Reviewer check: for each new abstraction in the diff, find its row; missing row = finding.
3. Disagreement about a choice → argue against the cited principle, not against taste.
