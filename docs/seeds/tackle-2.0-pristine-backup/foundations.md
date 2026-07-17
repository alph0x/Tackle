# Foundations — why each structural choice is the way it is

**Backbone: Clean Code + SOLID.**

## Decision → principle → source

| Choice (where it shows up) | Grounding (the principle) | Source (the referent) |
|---|---|---|
| Keep Tackle as a skill, not a CLI/SaaS | Single Responsibility: Tackle plans; execution is the agent's job | Tackle 1.5 `SKILL.md` §Scope |
| Add SDD phases (`constitution`, `specify`, `tasks`, `implement`, `checklist`) as optional triggers around the existing `plan` mode | Open/Closed: extend behavior without changing existing routing | spec-kit command surface (github/spec-kit README) |
| Template-resolution stack: plan-local overrides > plan-local presets > `references/sdd/` > `references/` | Dependency Inversion: high-level templates depend on abstractions, concrete files resolved at load time | spec-kit preset/extension priority table |
| Presets are template folders, not code | YAGNI: a folder of markdown files is enough customization for 2.0 | ponytail full-mode rule |
| `/tackle-init` is a trigger, not an external installer; it only creates directories inside `docs/plans/<initiative>/` | Visibility: plan decisions should be examinable, not hidden in dot-directories or outside the repo | user feedback (D-06) |
| Visible plan-local layout (`presets/`, `overrides/`, `constitution.md`) inside `docs/plans/<initiative>/` | No hidden config: every artifact the skill produces is part of the plan handoff | Tackle 1.5 workspace convention |
| Tackle 2.0 executes the plan it produces | User-driven disruption: since Tackle already produces prompts, the major-version jump is to consume them | user override (D-03a) |
| Variable execution team sizing (Solo/Pair/Pod/Squad) | Proportionality: overhead should match risk/complexity | user feedback during planning |
| Backward-compatible trigger table | Don't break existing contracts | semantic-versioning major bump convention |

## How to use this file during execution

1. Reaching for a pattern not listed here → STOP, add the row; if it changes structure, record a `D-xx` first.
2. Reviewer check: every new abstraction in the diff must map to a row.
