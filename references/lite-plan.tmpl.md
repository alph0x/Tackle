# Lite — complete PLAN → RUN path

After intake selects Lite, use this page as the procedure and briefing template. It contains the
required PLAN, RUN and closure steps; do not traverse the Full guide map or copy Full templates.
Read another guide only for an actual missing capability, such as capturing unavailable tool exports.
The core conventions in SKILL.md still apply. A durable receipt for this bounded task is Lite;
multi-team/session coordination, uncertain integration or a shared public contract upgrades to Full.

## Procedure

1. **Prepare.** Read the named spec, source and tests, relevant repository instructions and existing
   Lite plan/log/usage/decisions. Honor user > contract > protected tests > implementation. Confirm
   purpose, non-goals and scope; resolve user-owned ambiguity before the affected work. Reuse an
   authorized gitignore decision; otherwise ask once about docs/plans/ and apply it to docs/seeds/.
   Observe the repository root and create plan.md, log.md and usage.md under
   `docs/plans/<initiative>/`, plus decisions/questions files when entries exist.
   Resolve every write destination from that root, including patch tools and additive tests;
   confirm it stays inside the authorized Touches or workspace before writing.
   Use the minimal bodies below directly; log.tmpl.md and usage.tmpl.md are not prerequisites.
2. **Make ready.** Fill the plan body with verified file:line grounding, allowed writes, stable
   requirements, cases and runnable checks (or a named review rubric). Specify inputs, outputs,
   errors and invariants; exact bytes/order/paths/exits only when required. Map each requirement to
   a case/check. Derive valid adversarial cases from the domain, separately from invalid inputs:
   serializers round-trip delimiters, quotes, CR/LF and Unicode through the consumer. Expected
   results come from the contract, never from the implementation. Record intended supported
   producer/consumer runtimes and available validation environments before editing; no declared
   range means observed coverage only. Unavailable required coverage stays unverified/blocked.
3. **Run when authorized.** Explicit PLAN+RUN consent suffices; a PLAN-only request stops Ready.
   Verify current inputs/dependencies/environment and protected fingerprints before editing.
   Change only declared source and authorized artifacts. Test-first is the default for non-trivial
   executable work; existing red tests suffice. Add coverage
   in new files when original tests are byte-protected. Preserve unrelated edits.
   Apply self-documenting code: Clean Code + SOLID; no explanatory inline comments. Doc-comments
   belong on public surfaces only; put the why in commits/docs. Review smells, redundancy, SOLID
   and naming; an internal explanatory comment is a finding to fix by clarifying the code. A changed
   contract needs a prior superseding decision; changed inputs invalidate only dependent checks.
4. **Validate once per revision.** Use direct test commands or a checked script containing the
   complete compound validation. Capture exact argv/script, cwd, observed runtime, input hashes
   before/after, output, child exit/timeout/signal and produced hashes. Before running the check,
   choose an accessible durable export destination or adapt the [capture recipe](guides/evidence-capture.md).
   Choose either capture mechanism; delivering raw evidence is required. Generated
   receipts are evidence indexes: link them instead of retyping commands, output, clocks or hashes.
   One check may cover target, surrounding, affected integration and final deliverable obligations
   if its actual coverage does. Global acceptance still checks applicable packaging/rebuild and
   consumers. Validators use disposable copies and never repair real outputs. Required review
   stays required; self-observation is not independent review. Unavailable isolation is unavailable
   evidence. An output PASS cannot override failure, and counts need no extra regex wrapper.
5. **Recover or close.** First validation is not a correction cycle. Across actors/resumptions,
   allow at most three failed implementation correction-validation cycles; stop after two identical
   no-progress observations. Journal each failed correction before another. Contract, validator,
   environment or unknown causes stop the affected slice with expected/observed, reproducer,
   evidence and remaining budget; never silently replan or upgrade model. Preserve failed and stale
   observations. Before declaring complete, open each required evidence reference, confirm its
   actual result and final input/artifact revisions, and match it to the requirement it proves.
   A generic tool-transcript label without an accessible export is missing evidence. Failed,
   stale or missing required evidence, review or runtime coverage blocks the affected obligation
   and prevents overall completion. Optional coverage and unknown telemetry do not. Set plan state,
   closure log and final response from that decision: complete only when every required obligation
   passes; otherwise this evaluated closure is blocked, with completed portions and the missing check
   named. An interrupted run remains observe-incomplete until its outcome is observed. Record the role
   outcome separately in usage; do not describe a blocked implementation as successful completion.
   Make one closure write and respond. After closure,
   don't start template lint, receipt recopying or housekeeping without a new change or failure.

## plan.md body

# {{Title}}

- Purpose / requirements: {{observable result and stable ids}}
- Scope / non-goals / preserved files: {{allowed writes and exclusions}}
- Grounding / current inputs: {{verified file:line facts and fingerprints}}
- Contract: {{consumes, produces, errors, invariants and allowed semantic alternatives}}
- Compatibility: {{required supported targets; observed available producer/consumer environments}}
- Cases → checks: {{normal, valid adversarial and applicable invalid cases mapped to requirements}}
- Approach: {{small implementation sequence; material alternative/tradeoff if relevant}}
- Validation: {{literal commands or checked script, cwd, target/surrounding/integration/global coverage,
  required review and evidence destination}}
- Recovery: {{shared cycle count, remaining budget, relevant stop condition}}
- Reversal: {{documented revert; rollback/parity only for an applicable shipped path}}
- State: {{Ready / running / blocked / complete and next action}}

For discovery include Rounds and stop after the declared consecutive rounds converge against all
prior findings. For experiments include Metric, Threshold and Rounds, plus an attempt journal of
proposal/result/keep-or-rollback. Exhaustion blocks, not automatic acceptance. Omit inapplicable
fields rather than creating empty sections. Questions and decisions use their own files when needed.

## log.md body

# Log

Append one short kickoff entry with observed date/session, scope, decisions and next action.
Append one closure entry with outcome, changed surfaces, requirement-to-receipt links, unresolved
coverage and next action. This is a summary index, never reconstructed raw evidence. Historical
entries remain byte-preserved; corrections are append-only. No Full report/board/Point files.

## usage.md body

# Usage

Schema: tackle-observability/2

| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Append start before substantive role work and one finish at role close, or observe-incomplete
when an interruption is observed. Exactly one start and at most one terminal event are valid:
start(running) → finish(success|failed|blocked|aborted) or observe-incomplete(incomplete).
Use a stable unique Run ID and the same Point/Role. New ledgers
contain this v2 table only; preserve existing legacy rows without duplicating them. Unknown fields
are n/a, never guessed. Tier is the observed model binding (fast/standard/frontier), not Lite/Full;
an unavailable binding is n/a. Attempts counts failed implementation correction-validation cycles
shared across actors/resumptions: initial validation, dispatches and repeated tests do not count.
Rework uses a separately defined observed rework counter, otherwise n/a; neither counter resets
on resume. Zero requires observed absence, not missing history.
Verification/Source link the existing receipt and outcome; don't transcribe its metadata here.
**A validation end is not a role end.** An executor cannot observe its own future process termination:
use At=n/a for that unobserved finish and name this limitation in Source. Only an external observer
with the actual terminal event may supply its timestamp; never borrow the latest test clock.
No exact telemetry, collector or model metadata is required to close a product point. Ledger
recording remains informative. A successful test does not by itself establish product completion.
