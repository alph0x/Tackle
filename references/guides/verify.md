# Step 7 — Shared validation (PLAN readiness and explicit Verify)

PLAN invokes the preparation and evidence-integrity operations below before handoff. The explicit
`verify` request remains available for a later audit or for a plan that predates integrated
readiness; it is not a required pre-wave or pre-Task gate after a successful PLAN run. RUN uses the
single execution protocol in `references/guides/run.md` for explicit intent, preflight, target and
related regression checks, persistent correction, integration, and deliverable acceptance.

**Principle: detection before judgment.** Use cheap mechanical checks (`grep`, `read`, `ast-grep`, `git`) first; use the LLM only for synthesis of the findings. This keeps the pass fast and reduces false positives.

## Shared validation contract

Verification has one internal contract with four named operations. The `verify` request and its
legacy text alias forward to these operations; they do not maintain a second protocol or a separate set of
pass conditions.

1. **Preparation** — resolve the Task's declared inputs, Write scope, revisions, dependencies,
   case matrix, and disposable fixture directory. Confirm protected source and expected outputs
   before running a validator.
2. **Product** — run the Task's actual command or test against its declared input and observe
   output, status, effects, and boundary cases. A future or nonexistent product has no product
   PASS; use a validator fixture and semantic readiness evidence until implementation exists.
3. **Evidence integrity** — validate captured status, stdout, stderr, timeout, signal, metadata,
   and generated artifacts independently. Read-only validators reject missing, tampered, extra,
   or wrong-typed evidence and preserve a pre-existing sentinel.
4. **Relevant change** — compare current revisions to the recorded inputs and dependency map.
   Invalidate only consumers whose declared inputs changed; retain historical grades and explain
   the affected consumer and regression check.

Each operation reports its command, cwd, runtime, input/code/config/contract revisions, output,
exit or timeout/signal, and artifact path. Mechanical execution, semantic review, and
adversarial audit remain separate evidence classes. A valid semantic alternative is accepted
when the contract leaves formatting or implementation shape free; a requirement is not proved
by a keyword, file existence, or test count alone.

## Product verification has two halves

Every implemented-product verification must cover:

1. **Target half** — the task's specific done criterion passes, observed (it ran, rendered, counted, or matched). Do not infer this from reading code.
2. **Surround half** — the system around the touched area remains healthy (build, tests, lint, or equivalent for the touched area).

A green task check with a broken surrounding system is a failed verification. Preparation
uses fixture and readiness evidence when no product exists yet; it cannot claim a product PASS.
When an implemented product or its surrounding system cannot be checked (no runtime, missing
credentials, human-eyes-only), label the claim **UNVERIFIABLE**, never assume it is true. See
`references/failure-modes.md` for the symptom-to-rule catalog used by this check.

For each prepared task in `plan.md`'s task decomposition / `task-board.md`, and the full requirement coverage map:

1. **Reference verification** — confirm every cited `file:line` was actually read; flag ungrounded assertions.
2. **Claim counter** — for every factual claim ("always", "never", "only", "all", "none"), check the repo mechanically. Flag unsupported absolutes.
3. **Scope minimality / source anchor** — confirm the task traces to a line in the spec/ticket/constitution; flag untraced scope as drift.
4. **Acceptance check honesty** — confirm the acceptance check is a literal runnable command with an explicit
   pass condition (exit code / count / content match). A design or Markdown Task with no honest
   executable check uses a REVIEW gate with its rubric, evidence, and named independent reviewer;
   file existence or keywords alone never satisfy either gate.
5. **Dependency sanity** — confirm `Depends-on` resolves to an actual task and is not aspirational;
   reject missing identities, duplicate identities and dependency cycles; verify that produced interfaces/revisions match the consumers, not merely that a file exists. Derive independence from crossing artifacts, interfaces, and configuration consumers rather than
   disjoint `Write scope` (legacy `Touches`); flag any edge that names no **crossing artifact** (the concrete output of the
   upstream task the downstream task consumes — a file, a section, a schema, a protocol). A
   legitimate ordering-only edge is recorded as a `D-xx` scheduling choice; false edges get cut.
6. **Plan-vs-code drift** — compare the task's claimed `Write scope` (legacy `Touches`) and Goal against the current repo; flag if the code already implements it (stale task) or if the described change does not match any touched file.
7. **Agnosticism / Harness-agnostic check** — confirm the plan remains harness-agnostic: no harness-specific commands (e.g. `/command`, `@mention`, `.claude/`), no model brand names (e.g. `Claude`, `GPT`, `Opus`), and no vendor-specific file paths unless the task is explicitly about that harness. Flag violations as drift.
8. **Seal integrity** — mechanical: every `SEALED: D-xx` id found in the workspace resolves to a decision heading in `decisions.md` that is not marked superseded (lint row 7; a missing or superseded id is a HIGH finding); a sealed section edited with no superseding `SEALED: D-yy supersedes D-xx` marker is a HIGH finding. Every compiled clause hash recorded in `tasks/` or legacy `points/` must still match its clause in `design-contract.md`, where a clause runs from its `## <id>` heading through the line before the next `## ` heading or `<a id=` line, each line ending in one newline. The command below reads the first `sha256` of each compiled-clause bullet outside fenced code. It prints `seal drift` for an edit made after compilation (HIGH), `malformed clause hash` for a recorded value that is not 64 lowercase hex digits (HIGH), and `unresolved clause source` for an id with no heading there (MEDIUM until the brief's recorded source is checked); it exits 1 when it prints anything.
   <a id="seal-integrity-command"></a>

   ```sh
   ws=docs/plans/<slug>
   if command -v sha256sum >/dev/null 2>&1; then sum=sha256sum; else sum='shasum -a 256'; fi
   status=0
   for f in "$ws"/tasks/*.md "$ws"/points/*.md; do
     [ -f "$f" ] || continue
     for entry in $(awk '/^```/ {fence = !fence; next} !fence && /^[[:space:]]*[-*+][[:space:]]+[*][*][^*[:space:]]+ · .* · sha256 `[^`]*`[*][*]/ {id=$0; sub(/^[[:space:]]*[-*+][[:space:]]+[*][*]/, "", id); sub(/[[:space:]].*/, "", id); h=substr($0, index($0, "sha256 `") + 8); sub(/`.*/, "", h); if (length(h) != 64 || h ~ /[^0-9a-f]/) h = "malformed"; print id "=" h}' "$f"); do
       id=${entry%%=*}; recorded=${entry#*=}
       if [ "$recorded" = malformed ]; then echo "malformed clause hash: $id in $f"; status=1; continue; fi
       if [ -f "$ws/design-contract.md" ] && awk -v id="$id" '$1 == "##" && $2 == id {found = 1} END {exit !found}' "$ws/design-contract.md"; then
         current=$(awk -v id="$id" 'found && (substr($0, 1, 3) == "## " || substr($0, 1, 6) == "<a id=") {exit} !found && $1 == "##" && $2 == id {found = 1} found {print}' "$ws/design-contract.md" | $sum | cut -d ' ' -f 1)
         if [ "$current" != "$recorded" ]; then echo "seal drift: $id in $f (recorded $recorded, current $current)"; status=1; fi
       else
         echo "unresolved clause source: $id in $f"; status=1
       fi
     done
   done
   exit "$status"
   ```
9. **Regression sweep computability** — confirm the task declares `Write scope` (legacy `Touches`) precisely enough that the sweep set (Complete tasks on v3/v4 boards, or legacy 🟢 tasks, with intersecting Write scope) is derivable mechanically (grep over the selected board + `tasks/`, or legacy `points/`); flag missing or vague `Write scope` (legacy `Touches`).
10. **Verification derivation** — on v3/v4 boards, inspect the referenced report and raw records for actual method, result, revisions and observed independence; missing/failed/stale required records block acceptance. For legacy boards, for every historical `board.md` row carrying a Confidence grade, re-derive the grade from its closure evidence (closure report section 4; Focused/Lite gate: the selected history evidence block): command + output + exit line from the independent checker ⇒ E1; a review-gate marker with rubric + named reviewer ⇒ E2; an explicit UNVERIFIABLE label ⇒ E0; anything else ⇒ E3. A declared grade that doesn't match derivation is a grade-inflation finding — HIGH, mechanically checkable.

Classify every finding with a certainty level:

- **HIGH** — mechanically confirmed (file missing, citation unread, command not runnable). Safe to block on.
  - Examples: a cited **file does not exist** (e.g. `src/foo.ts:42`); the acceptance check command returns exit code 1; `Depends-on: T-99` references a non-existent task.
- **MEDIUM** — likely true, needs one extra check before blocking.
  - Examples: the task claims "X never happens" but a grep finds one counter-example; the `Write scope` (legacy `Touches`) list omits a file the Goal clearly modifies; a `Depends-on: T-03` line names the upstream task but no crossing artifact, and no `D-xx` waiver records it as ordering-only.
- **LOW** — possible, needs human judgment.
  - Examples: a variable name feels inconsistent with project convention; a prose description could be read two ways but the code is probably correct.

Use these examples to calibrate: if you are not sure whether a finding is HIGH, downgrade it. If you cannot reproduce it mechanically, it is not HIGH.

Output: during PLAN, append readiness findings to its evidence and handoff; during an explicit audit,
append findings to `history.md` only when that audit is authorized to write history. Verification does
not itself update execution status. Any HIGH finding, or an ungrounded task, blocks execution until
fixed or explicitly waived by the user. MEDIUM findings block unless the user explicitly accepts the
risk; LOW findings are advisory. RUN records target/surround and integrated observations through
`references/guides/run.md` rather than invoking a universal Verify loop.

## Step 0 — Mechanical grounding (two-phase citation check)

Triggered by `verify` (step 0). The read-only diagnostic computes proposed citation repairs and freshness results only. Applying a re-anchor or writing a history stamp requires an authorized PLAN/RUN scope or an explicit request permitting that write; a standalone verify/ground/status question supplies no such permission. Run before the red-team pass to remove the mental load of remembering which `file:line` citations have been read.

**Principle: outsource the memory.** The agent should not rely on its session transcript to know what is grounded; the commands produce an explicit, inspectable record.

1. **Freshness check** — compare each cited input's recorded content fingerprint and citation
   fragment with its current bytes. An mtime change is a probe for possible drift, not a blanket
   invalidation: unchanged bytes remain reusable, while changed bytes invalidate only affected
   citations and their semantic consumers. If timestamps are unavailable, use content fingerprints
   and record the missing timestamp as `n/a` rather than inventing one.
2. **Drift check** — run the following two-phase check with zero model judgment:
   - **Phase 1 — line check**: `sed -n 'NNp' path | grep -Fq "fragment"` → exit 0 = **grounded**.
   - **Phase 2 — whole-file fallback** (only on phase-1 failure): count the lines in `path` containing the fragment. Exactly 1, at line MM ⇒ **drifted → proposed re-anchor** (only when writes are authorized, rewrite `path:NN` → `path:MM` in place, literal replacement, zero model judgment). 0 ⇒ **stale** ⇒ the task is **ungrounded**. More than 1 ⇒ **ambiguous** ⇒ flagged; the task is ungrounded until a more specific fragment is chosen.
3. **Record** only within authorized planning/execution or explicitly requested history writes; otherwise report without changing files. In `history.md` — list every citation read, flag unresolvable ones, and stamp `Last-verified: {{YYYY-MM-DDTHH:MM:SSZ}}` (legacy date-only stamps read as start-of-day and self-heal on the next ground). Reference verification is recorded only here — never copied into the board or the task file; staleness is derived from the newest entry that lists a task, never copied.

Any **ungrounded** task blocks execution until fixed or explicitly waived by the user. Run step 0 right after `plan`, before any red-team pass, and on any cold session where the freshness check reports stale.

## Coverage matrix (criterion → evidence)

Triggered during PLAN readiness (and available to `verify` or a natural phrase like
"trace coverage"). The check itself is read-only. During an authorized PLAN run, an in-scope
technical gap may be repaired and rechecked; a new product requirement or material ambiguity is a
user-owned `Q-xx` and blocks its affected scope.

**Principle: count-assert both ways.** Per-task anchoring checks one task at a time; a criterion covered by no task is invisible to it. The matrix closes that direction.

- **Inputs**: acceptance criteria from `spec.md`, the ticket, or `constitution.md`; if none exists, trace against the plan's Behavior/Outputs and Acceptance sections and say so (a plan with no criteria at all is itself a HIGH finding). Tasks and anchors from the plan's Task decomposition and each briefing's `Traces to` line.
- **Output**: one row per criterion — `| Criterion | Observable | Task(s) | Check | Verification record | Status |` —
  with status `covered` / `deferred` / `gap`. `deferred` names a Draft owner, outcome/interface and the milestone that will compile its check; it is visible scope, never readiness or acceptance. Count-assert both ways: criteria count equals matrix rows, every
  criterion has an observable and check, and every task id appears in a row or a closing **Scope
  drift** list. An id with omitted behavior is a gap even when the id is present. An unowned global
  obligation is a gap even when all criteria are covered.
- **Where results go**: append the matrix, reverse-direction scope-drift list, global-obligation
  rows, and the observed structural/semantic results to the PLAN evidence block and handoff. A
  later log projection may summarize it; the matrix is the source of truth for readiness.

## Cold-resolvability probe (risk-triggered)

Optional and risk-triggered for a concrete ambiguity or elevated failure risk. PLAN may run at most
one initial probe and, when a correction changes the briefing, one correction recheck; both are
included in the planning evidence. It is not a universal Ready gate.

**Principle: the isolation is the protocol.** Use a fresh isolated session or an explicitly
declared human fallback and give it only the Task brief and named inputs. Record the actual
executor/profile binding. Require it to restate, numbered exactly:

1. **Goal** — what the task produces, in its own words.
2. **Approach** — how it would resolve the task.
3. **Acceptance check + pass condition** — the literal command and what output counts as pass.
4. **Missing information** — an exhaustive list of everything the briefing does not answer.

5. **Reconstructed cases, outputs, and decisions** — restate the required observations and choices
   from the briefing, then resolve the supplied probe case.

**Verdict**: any missing required item or mismatch ⇒ the Task is not Ready. Optional information
that the contract deliberately leaves open is recorded as a local freedom and does not block. A
probe that reports an empty doubts list still fails when its reconstructed output is wrong. Record
the probe input, output, profile/binding, command/runtime, and verdict; do not treat confidence or
an empty doubts list as evidence.

## Selective revalidation after drift

Readiness fingerprints cover the relevant clause, code, configuration, dependency, and input
revisions. A new session with unchanged fingerprints and selector membership may reuse readiness and does not require a
complete re-Verify. When a revision changes, invalidate only the consumers that declare that input
or a crossing artifact; preserve unaffected readiness and historical grades. Configuration changes
therefore invalidate the named configuration consumers, while an unrelated documentation change
does not. Regenerate changed compiled clauses, rerun their target/surround fixtures, and update
the affected evidence slots before handoff. Hash comparison detects drift; dependency reasoning
decides its blast radius.

## Milestone readiness

For long initiatives, validate complete requirement ownership and critical cross-milestone interfaces now; detailed briefs may be deferred to their input boundary. Readiness applies only to the explicitly selected prepared tasks. A later Draft task does not prevent independent prepared work, but a missing product decision or incompatible dependency blocks its consumers. Every deferred requirement retains an owner and future check obligation. Deliverable acceptance still covers the entire authorized objective; a ready milestone or all-green prepared subset cannot close it. A contract/interface change invalidates affected prepared consumers and deferred assumptions.

## PLAN-only intent and handoff

Preparation must record `INTENT: PLAN prepares tasks and stops before source execution.` PLAN may
write its authorized planning artifacts and evidence, but it cannot start source execution. A
status, next, or unqualified resume only inspects/selects and cannot mutate source, board, or log;
explicit handoff generation may write its projection. Handoff includes the matrix, global
obligations, Ready fingerprints, validator results, optional probe results, unresolved questions,
and the explicit execution boundary. RUN records a separate execution intent before it may mutate
source.
