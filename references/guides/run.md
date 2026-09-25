# RUN — depth for the [RUN card](run-card.md)

<a id="authorization-and-preflight"></a>
<a id="state-transitions"></a>
The card holds the single execution protocol for a Full task; the self-contained Lite procedure in
`../lite-plan.tmpl.md` implements the same obligations for bounded work. Each section below is depth
on demand, reached from the card's Depth list.

<a id="evidence-and-recovery"></a>
<a id="verification-records-and-recovery"></a>
## Verification record fields

Every target, correction, integration, or global validation is an observation. Record the actual
UTC start and end (or timeout), literal command, cwd, tool and runtime, executor/actor and context,
input/code/config/dependency/contract revisions, stdout, stderr, exit code or signal, timeout, and
artifact paths and hashes. The preflight records the protocol and contract revisions, relevant
fingerprints, declared Write scope, executor binding, and the current tree. Store one immutable raw
check record per actual validation, referencing shared immutable objects where available; the local
report may summarize it but cannot replace it. A generic transcript label without an accessible
export is missing evidence.

A printed PASS is not evidence when a child process, wrapper, generated artifact, or package failed.
Check a real child return code, timeout and signal independently of wrapper output. A validation
command's own process result is authoritative; a helper that prints PASS while its child failed is a
failed observation. `set -u`, `pipefail` or a final PASS alone does not propagate a required
assertion's failure; use checked subprocesses or explicit failure exits for each required condition.
A final PASS is optional unless the consumer requires it; when used, emit it only after all relevant
children succeed.

## Capture

Choose an accessible evidence destination before the check, so a missing export is handled at
capture time. Capture using the harness's complete exported event or direct stdout/stderr capture.
An export must remain independently accessible after handoff; otherwise save the raw command result
locally. Never type a shortened command, paraphrased output or later clock reading into a file
labelled raw. Record unavailable metadata as `n/a`, not midnight, zero, or an inferred model/effort.
Fingerprint the actual source/tests/config/inputs before the check and confirm they still match
afterward; hash produced artifacts afterward. If they change, retain the old result as historical and
revalidate only affected obligations. A pre-edit test hash does not identify post-edit coverage.
Exact-byte edits and checks preserve the specified delimiter and final newline; do not normalize
either away. Disposable directories may be created and removed after the observation, with
pre-existing sentinels preserved.

For Full, use [execution checks](full-checks.md) when the harness lacks complete capture or
canonical lint automation. The smaller `evidence-capture.md` example serves the other routes.
Establish effective write confinement before the first PLAN write/check and retain it in RUN; record
its observed capability separately from instructions. Prepare the obligation/evidence index once,
snapshot the executed scripts and selected input membership, and close with affected checks. One
captured command may discharge target, surrounding and integration obligations when its observed
coverage includes them all; index that same observation instead of rerunning unchanged checks to
populate headings.

Where the harness has native usage capture, use it at role start and again after the role's terminal
event is externally observed, keeping its receipt and exact thread ID with the Run ID;
[codex-native-usage.md](codex-native-usage.md) is one example. Use configured model/effort only when
the matching native turn records them; a requested CLI launch binding is labeled requested. Save
native token observations at their session scope, and put an exact terminal clock in the role's
`resource-usage.md` finish row only with a reviewed Run ID/turn map. If the environment or trace is
unavailable, record `n/a` and continue. Missing telemetry does not block execution and must not be
reconstructed.

<a id="failure-classification-and-correction"></a>
## Failure classification and escalation packet

Consume retained failed observations before another check, including on resume. Diagnose from their
command, output and relevant input fingerprints; do not repeat an unchanged failed check to
rediscover its result. Recheck only after a recorded relevant input or environment change, or an
actually justified permitted operational recovery below. Narrower diagnostic inspection remains
allowed; diagnosis alone does not justify repeating acceptance.

The escalation packet names the exact requirement/clause and revision, expected versus observed
result, reproducer and raw-evidence pointer, affected consumers, attempts/cycles already used and
remaining, and the smallest unresolved decision. The packet is a decision aid; it does not silently
replan, broaden scope, upgrade model or effort, dispatch a frontier role, or make up a missing
requirement. Generic escalation records its trigger, minimal scope, budget and observed outcome.

## Operational recovery

A permitted operational recovery is separate from implementation correction: once per unchanged
failure signature (cause, command, relevant inputs and environment), inspect the failed process and
records, then correct a workspace-local temporary-path issue, interrupted local capture, or restart an
already-configured foreground tool after confirming prior writers stopped. One retry may establish
recovery; if it fails, block that action with both records. A relevant external change may justify a
new diagnosis, but a new actor/task name does not reset this allowance. Record recovery kind, action,
result and spent allowance in the same journal. No global install, credentials, restricted access,
protected expectation change or invented requirement is authorized. All other operational causes
remain blocked pending the concrete needed capability or decision.

Before repeating an interrupted command or completion update, inspect the tree, process results,
task-board/report revisions, checkpoint and raw records to determine whether it occurred. If
occurrence is incomplete or unknown, record `observe-incomplete` and preserve the history before
choosing a safe continuation. Do not duplicate an irreversible action merely because a session ended
without a terminal message. If interrupted between record/report/board writes, reconcile all three
against actual outcomes before repairing the incomplete update. A completed side effect is not
repeated merely to fill a missing terminal row; unchecked work remains Interrupted or Checking.

<a id="correction-lineage-consistency-recipe"></a>
## Correction lineage

Task IDs survive renaming. On split, merge or supersession, record ancestor IDs and unresolved
failure IDs in the existing attempt journal. Each failed cycle has one stable event ID; descendants
addressing the same failure reference the same spent pool, and a merge takes the union of event IDs.
A split never grants a fresh allowance for unresolved old work. A new unrelated responsibility
receives its own pool only with its distinct requirement/acceptance and no inherited failure.
Preserve no-progress observations and the two-cycle unowned integration pool; attribution transfers a
cycle once. Reassignment, translation or reopening cannot erase spent work. Validate lineage before
another correction. Never invent a narrower cap, reset the count under a new actor, or count a
repeated observation as a new distinct cycle.

A dependency artifact failure is first recorded as a preflight/dependency cause; if it is an unowned
integration fault, its cycle consumes the initiative's unowned-integration pool. When attribution
identifies an owner, transfer the cycles already spent exactly once to that owner's Task; the
initiative pool and Task counter both retain the spent count, which survives resume.

Each failed implementation correction appends an attempt-journal entry before another attempt and
re-reads the earlier entries. The entry names the observed failure, correction, validation command,
result, and cycle count. A correction that changes a contract or acceptance requires the authorized
superseding decision first, then re-grounding and revalidation.

When tasks are reshaped, use stable failure IDs and cycle-event IDs in the existing journal. A cycle
pool follows unresolved work; several descendant tasks can reference the same pool. Merging distinct
pools retains each allowance separately; their sum is informative and does not exhaust an unrelated
pool. A combined failed correction has one event ID and names each affected pool once in `pool_ids`.
Stop corrections involving an exhausted pool; separate unrelated work may continue. Use the optional
pure check in [correction-lineage.md](../recipes/correction-lineage.md) when composing a split/merge;
its pool limits are parameters, 3 for a task pool and 2 for the unowned integration pool. Callers
validate failure attribution against the original records; arbitrary IDs cannot manufacture a fresh
budget. Successful corrections, observations and dispatches are not failed-cycle events.

<a id="independence-and-evidence-grades"></a>
<a id="verification-method-and-independence"></a>
## Independence and historical grades

Mechanical execution, focused semantic review, and adversarial audit are separate capabilities. The
same agent may observe a deterministic command; that observation is real command evidence with its
actual provenance, while its own review remains self-review and is not independent. Use an
independent session or human fallback only when the risk or obligation requires semantic
independence; record the actual actor, profile, context and isolation. If the required isolation is
unavailable, mark that evidence obligation unavailable/blocked and do not claim independent E1. A
renamed role or a fresh label is not proof of independence. Routine Run has no universal frontier
checker, majority vote, or audit. A vote cannot erase a confirmed correctness failure. Freeze the
source and protected expectations at the review boundary.

The Task state is distinct from evidence grades and from the board's current execution status. Keep
historical E0–E3 grades readable. New evidence also records provenance and independence dimensions.
E1 is command-verified evidence from an actually independent checker; E2 is a named semantic review
gate when no honest command exists; E0 is explicitly unverifiable; E3 is an assertion. Grades are
derived from the evidence, never self-declared, and E2 is not numerically ordered against E3. Missing
capability is not zero evidence.

<a id="integration-global-acceptance-and-close"></a>
<a id="integration-deliverable-acceptance-and-close"></a>
## Integration and deliverable acceptance

After a Task's target and related regression checks pass, integrate its scoped change and recheck the
merged tree. Reuse evidence only while every relevant source, contract, configuration, dependency,
input, selector membership, runtime, protocol revision and relevant freshness window matches. A
changed contract, dependency output, configuration, input, or relevant source fingerprint invalidates
only the dependent checks; re-ground and revalidate them before continuing. Selective invalidation
preserves unaffected history and invalidates the changed consumers and crossing artifacts. The integration check must include semantic consumers that a Write scope-only
intersection cannot see.

At serialization or unit boundaries, global checks include applicable valid adversarial inputs from
the declared domain and the actual consumer parser/round trip. Nominal sample output alone does not
prove preservation of arbitrary allowed strings or numeric values. Before implementation, record
required supported producer/consumer targets and available validation environments in the contract.
Record the actual producer and consumer runtimes and the supported range being claimed. A pass on one
runtime does not establish compatibility with another. An unverified required target blocks the Task
or global obligation that owns it; an outstanding mandatory global obligation prevents initiative
completion. Optional targets remain unverified without blocking the authorized narrower scope.
Independent unaffected work may proceed. A cross-runtime discrepancy keeps both observations and
their environments visible.

Deliverable acceptance then checks the final integrated flows, every required global obligation,
final artifacts, packaging, source/install boundary, reproducibility, and the complete acceptance
command where applicable. It must catch a producer/consumer unit mismatch such as cents rendered by a
producer while a consumer expects dollars, even if every local unit suite is green. Missing package
files, child failures, stale inputs, protected-test weakening, isolation gaps, and unavailable
environment capabilities remain failed or unverifiable observations.
All tasks passing is insufficient to close an initiative. For compound global checks, save the
complete script before execution and include it in input fingerprints; a label describing an inline
assertion cannot replace its code in the handoff.

## Release gating

When a release names an initiative in scope, that initiative remains subject to this global
acceptance obligation until the evidence passes. A board with no in-progress rows, or a board whose
Tasks are all complete, cannot infer release acceptance; the release sweep consumes the named
workspace's existing global-acceptance evidence rather than creating a second status source.

For release work, the Coordinator records the explicit workspace scope before running the sweep;
unknown scope blocks the tag pending clarification. The release-gating set is the deduplicated union
of active and selected workspaces: selection never exempts another active workspace from its
mandatory lint and acceptance check gates. Selected workspaces also require current deliverable
acceptance regardless of board status. Historical closed and parked workspaces that are neither
active nor selected remain non-gating; warn-severity lint rows retain their severity.

## Run record

Before choosing the terminal state, the Coordinator opens every required evidence reference, checks
its actual result and relevant final revisions, and matches it to the obligation it proves. Missing,
stale or failed required verification-records/review/coverage blocks its owning scope; summaries
cannot repair it. Board, report and final response must express that same scope and outcome. Role
completion is separate: a reviewer may successfully report a blocked product, but a blocked
implementation is not successful product completion. Unknown telemetry and optional coverage remain
non-gating.

On complete, the Coordinator records the final report, raw evidence pointers, immutable revisions,
attempt and rework counts, and the board status. On blocked, it records the same evidence and the
failure packet; blocked, skipped, completed, and unverifiable outcomes remain distinct. A completion
update records the last fully recorded event and intended task state. A projection never overrides
counters, permissions or actual results. Lifecycle rows and attempts serialize and resume from the
workspace; missing end data stays `n/a`.

For a historical workspace, `board.md`
is the canonical current state; `log.md` is append-only history.

A closure report or local Run report is evidence, not permission to erase prior history. Once
deliverable acceptance and its review/sign-off obligations pass, write the closure records, check only
fields and obligations affected by those writes, and respond. Do not restart whole-plan lint, guide
traversal or housekeeping after product acceptance without a relevant change, new failure, or
explicit release/audit request. Reuse unchanged PLAN readiness checks; this does not skip initial PLAN
lint, required product/review checks, or the separately requested release sweep.

The local report contains, in order: authorization and preflight; implementation and target
observation; surrounding and integration observations; correction journal and any failure packet;
deliverable acceptance; independent semantic review when required; final status and unresolved risk,
closed by the receipt. Each observation links to its immutable raw record. Raw records are
append-never/overwrite-never artifacts named with a unique Run, Task, validation ordinal, and observed
timestamp. Record unknown telemetry as `n/a`; do not infer duration, tokens, cost, actor,
independence, or success.
