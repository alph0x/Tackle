# Point P-0N — {{title}}

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone (links below are for depth, not prerequisites). Tackle plans
> this point; it does not implement it here.

## Status
**Depends on**: {{none / P-0X}} · execution status tracked in `plan.md` §5 (single board — don't duplicate it here).

## Goal
{{What "done" means for this point — observable, testable.}}

## Context (grounded)
- {{Why this point exists; what part of the system it touches.}}
- `{{path/File.swift:NN}}` — {{relevant current code/behavior}}.
- Deeper refs: {{`reference.md` §x · `specs/...md` · diagram}}.

## Non-goals
- {{What NOT to do in this point — keep it surgical.}}

## Recommended approach
1. {{concrete step, grounded in real files}}
2. {{...}}
3. Tests: {{what to cover and where}}

## Alternatives / fallbacks
- **If {{condition / the recommended approach doesn't fit}}** → {{alternative approach + tradeoff}}.
- **If blocked by {{X}}** → {{what to do; which question in `questions.md` it maps to}}.

## Recommended starting prompt
<!-- Ready to paste into a fresh session to attack this point. Keep it grounded and bounded. -->
```text
Resolve Point {{ID}} ({{title}}) of the "{{initiative}}" plan.
Repo: {{repo path}}. Read points/{{this-file}}.md first; it is self-contained.
Do: {{the recommended approach, summarized}}.
Constraints: {{non-goals / no-regression / surgical}}.
Acceptance: {{acceptance criteria}}.
Verify with: {{tests / mock / smoke}}.
```

## Acceptance criteria
- [ ] {{observable, verifiable condition}}

## Verification
- {{targeted tests; local mock/stub if the env needs it; smoke for this point}}

## Open questions for this point
- {{Q-0x in `questions.md` — blocking or not}}

## Definition of Ready (self-check while writing — if any remains unchecked, the point is not ready to tackle)
- [ ] Goal is observable/testable.
- [ ] Context is grounded in `file:line`, verified against the repo.
- [ ] Recommended approach is concrete; alternatives/fallbacks cover the likely failure.
- [ ] Starting prompt is pasteable and bounded — works on any model.
- [ ] Acceptance + verification are stated.
- [ ] Dependencies and open questions are linked.
- [ ] A cold agent could resolve this point from this file alone.
