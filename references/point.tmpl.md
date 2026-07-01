# Point P-0N — {{title}}

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone. Links are for depth, not prerequisites — EXCEPT a named
> `design-contract.md` section the point implements, which IS required reading (name it in
> Context). Tackle plans this point; it does not implement it here.

## Status & wiring
**Depends on**: {{none / P-0X — and what it needs from it, e.g. "P-01 (its `XPort` protocol)"}} · execution status in `board.md` (single board — don't duplicate here). Parallelism is read off the graph + Touches, not re-listed here.
- **Traces to**: {{spec/ticket line this point implements — e.g. `spec.md:NN` or `ticket-123` acceptance #2}}.
- **Touches (write scope)**: {{the files/dirs this point may modify — bounds the blast radius; disjoint Touches ⇒ parallel-safe (isolated worktrees), and keeps the done-signal's diff reviewable. Explicitly flag any touched path that ships to production — a flagged path requires the Rollout / reversibility section below}}.
- **Autonomy override**: {{inherit (workspace level in AGENTS.md §Autonomy) / L1 / L2 / L3 — L3 requires the AGENTS.md §Autonomy conditions; production-path points cap at L2}}.

## Goal (single responsibility — one loop-completable change)
{{What "done" means — observable, testable, ONE coherent change. If stating "done" needs an "and", split the point.}}

## Context (grounded)
- {{Why this point exists; what part of the system it touches.}}
- `{{path/File.ext:NN}} — "{{literal fragment}}"` — {{relevant current code/behavior}}.
  <!-- Anchored citation: fragment = verbatim substring of line NN, ≤ 60 chars, unique on that line, no double quotes (pick another fragment if unavoidable); a range `NN-MM` anchors to NN. -->
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

## Rollout / reversibility (only if Touches include a production path)
- {{revert procedure · flag default-off · no-op-when-off proof; delete this section if no touched path ships to production}}

## Acceptance — the loop's exit gate
<!-- One home for "how the loop knows it's done". The command must be a literal runnable command (or a short pipe/combo) with an explicit pass condition. EXHAUSTIVE + MECHANICALLY verifiable: where a finite set exists, assert the COUNT. No prose gates, no `test -f`, no "document exists". -->
<!-- Seal at ready: when the point is marked ready, seal this heading by appending the marker
     `SEALED: D-xx` as an HTML comment on the heading line (D-xx = the decision that marked it ready).
     Editing anything in a sealed section afterwards requires a superseding `D-yy` recorded in
     `decisions.md` FIRST; the marker then becomes `SEALED: D-yy supersedes D-xx`. -->
- **Done-signal**: `{{the exact command (or a short combo of mechanical checks) — e.g. cd <pkg> && swift test --filter <Suite>}}` → pass = {{exit 0, N tests, 0 failures}}.
- The 🟢-flipping run of this command is the **checker's**, not the Driver's (maker/checker).
  <!-- Judgment/investigation point (research, copy/UX, design spike) with no honest command? Make this a REVIEW-gate instead: "exit = artifact + rubric, reviewed" (e.g. `decisions.md` D-xx chosen with the matrix filled). Never a fake `test -f` green. -->
- [ ] Meets the **universal per-point acceptance** in `plan.md` §6.1 (don't restate it here).
- [ ] {{quality-dimension checks this point's **Touches** fire — Security / Performance / Concurrency / Correctness / … per the catalog (`references/guides/quality-dimensions.md`) — each **folded into the done-signal above** as a runnable fragment using this repo's tooling (e.g. "authz test in the suite asserts unauthenticated/cross-tenant → 401/403"), or a **review-gated** criterion only if no honest command exists. Omit axes that don't fire; don't restate the §6.1 universal ones}}.
- [ ] {{point-specific condition — exhaustive over its case set (assert the count), verifiable by test/grep}}.
- **If it fails →** {{likely failure → concrete fix}}. Self-correct up to the workspace iteration budget (`AGENTS.md`), then STOP + escalate (set a per-point budget here only if it differs).

## Open questions for this point
- {{Q-0x in `questions.md` — if any is user-owned and unresolved, this point is Deferred, not loop-ready}}

## Definition of Ready (the gates that can FAIL — if the rest of the briefing is filled, these are what's left to check)
<!-- Only the checks not already visible by reading the sections above. Don't re-checklist the doc. -->
- [ ] **Grounded**: every Context citation passes the drift check recorded by the newest ground entry in `log.md` (`sed -n 'NNp' file | grep -Fq "fragment"` → exit 0) — not "read in this session"; any stale citation makes the point **ungrounded** and not ready.
- [ ] **Anchored**: it traces to a line in the spec, ticket, or `constitution.md`; untraced scope is flagged as drift.
- [ ] **Single responsibility**: stating "done" needs no "and" (if it does → split; see the functional-core/effectful-shell split in Step 6).
- [ ] **No open decisions inside it**: zero unresolved user-owned questions (if any → it's Deferred, not ready — Decision ownership).
- [ ] **Loop-ready**: the Acceptance done-signal is a literal runnable command with an explicit pass condition (exit code / count / grep match); count-asserted where a finite set exists.
- [ ] **Cold-agent-resolvable from this file alone** — the one true test of every section above.
