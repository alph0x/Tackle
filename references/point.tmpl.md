# Point P-0N — {{title}}

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone. Links are for depth, not prerequisites — EXCEPT a named
> `design-contract.md` section the point implements, which IS required reading (name it in
> Context). Tackle plans this point; it does not implement it here.

## Status & wiring
**Depends on**: {{none / P-0X}} · **Runs alongside** (parallel-safe): {{P-0Y / —}} · execution status in `plan.md` §5 (single board — don't duplicate here).
- **Consumes**: {{the surface/output this point needs from upstream — e.g. "the `XPort` protocol from P-01"; "—" if none}}.
- **Produces**: {{the surface this point hands downstream — what the next loop builds on}}.
- **Touches (write scope)**: {{the files/dirs this point may modify — bounds the blast radius; lets parallel loops run in isolated worktrees without colliding, and keeps the done-signal's diff reviewable}}.

## Goal (single responsibility — one loop-completable change)
{{What "done" means — observable, testable, ONE coherent change. If stating "done" needs an "and", split the point.}}

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
Loop until green: {{the done-signal command}}.
```

## Acceptance — the loop's exit gate
<!-- One home for "how the loop knows it's done". The command is the exit check; the criteria
     are what passing means. EXHAUSTIVE + MECHANICALLY verifiable, not prose: where a finite set
     exists (error cases, states, endpoints), cover EVERY case AND assert the COUNT in the
     command (e.g. test count == N) so a lazy suite can't go green with half the cases. -->
- **Done-signal**: `{{the exact command (or a short combo of mechanical checks) — e.g. cd <pkg> && swift test --filter <Suite>}}` → pass = {{exit 0, N tests, 0 failures}}.
- [ ] Meets the **universal per-point acceptance** in `plan.md` §6.1 (don't restate it here).
- [ ] {{point-specific condition — exhaustive over its case set (assert the count), verifiable by test/grep}}.
- **If it fails →** {{likely failure → concrete fix}}. **Budget**: {{N}} attempts, then STOP — append a `log.md` note + escalate to the user (a stuck loop is a question, not another retry — Decision ownership).

## Open questions for this point
- {{Q-0x in `questions.md` — if any is user-owned and unresolved, this point is Deferred, not loop-ready}}

## Definition of Ready (the gates that can FAIL — if the rest of the briefing is filled, these are what's left to check)
<!-- Only the checks not already visible by reading the sections above. Don't re-checklist the doc. -->
- [ ] **Single responsibility**: stating "done" needs no "and" (if it does → split; see the functional-core/effectful-shell split in Step 6).
- [ ] **No open decisions inside it**: zero unresolved user-owned questions (if any → it's Deferred, not ready — Decision ownership).
- [ ] **Loop-ready**: the done-signal is a runnable command with an unambiguous pass (incl. a count assertion where a finite set exists) + budget.
- [ ] **Cold-agent-resolvable from this file alone** — the one true test of every section above.
