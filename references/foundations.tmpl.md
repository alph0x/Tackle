# Foundations — why each structural choice is the way it is

> **Full-gate depth artifact.** Create this for any Full initiative that introduces or shapes
> architecture (a new subsystem, a layering, a set of patterns). For a bounded change that
> only follows existing structure, skip it — the per-point "Recommended approach" is enough.

**The backbone is Clean Code + SOLID, grounded in the best referents of software design.**
Grounding rule (binding when this file exists): **every pattern or abstraction the plan
introduces gets a row here BEFORE it ships** — decision → principle → source. *"It felt
cleaner"* is not a justification. Reviewers verify a row exists and that the cited principle
actually fits; superseding a row requires superseding its decision (`D-xx`).

## The canon (referents this initiative draws from)

Trace choices to something stronger than taste. The defaults below are the standing backbone;
add/trim referents to fit the domain (framework guidelines, an RFC, the authoritative spec, a
proven in-house module the design mirrors).

| Referent | Work / source | What we take |
|---|---|---|
| Robert C. Martin | *Clean Code*, *Clean Architecture* | SOLID, the Dependency Rule, boundaries, meaningful names, small functions, error handling over codes, **self-documenting code (comments compensate for failure to express in code)** |
| Kent Beck | *TDD by Example*, *XP Explained* | red→green→refactor, the four rules of Simple Design, YAGNI |
| Martin Fowler | *Refactoring* | the code-smells catalog (long method, god class, feature envy, shotgun surgery, primitive obsession), refactoring as continuous design |
| Gamma/Helm/Johnson/Vlissides | *Design Patterns* | pattern vocabulary used PRECISELY (Facade, Adapter, Command, Null Object…) |
| {{e.g. Cockburn / Evans / Parnas / Liskov / Meyer / Nygard / Hunt&Thomas}} | {{Hexagonal / DDD / information hiding / LSP / Design by Contract / Release It! / Pragmatic Programmer}} | {{the specific principle this design leans on}} |
| {{the in-house module X}} | {{path or repo}} | {{the proven house pattern we mirror — precedent over invention}} |

## Decision → principle → source (the standing choices)

| Choice (where it shows up) | Grounding (the principle) | Source |
|---|---|---|
| {{the abstraction/pattern, + where in the code/spec}} | {{the principle it satisfies}} | {{referent above}} |

## How to use this file during execution

1. Reaching for a pattern not listed here → STOP, add the row (choice, grounding, source);
   if it changes structure, record a `D-xx` first.
2. Reviewer check: for each new abstraction in the diff, find its row; missing row = finding.
3. Disagreement about a choice → argue against the cited principle, not against taste.
