# RUN — execution and integrated acceptance

This is the Full reference for the single execution protocol; the self-contained Lite procedure
in `../lite-plan.tmpl.md` implements the same obligations for bounded work. The `run` request uses the
selected route; Full and an explicitly authorized Full Run use this
guide; `team.tmpl.md`, `AGENTS.tmpl.md`, and `coordinator.tmpl.md` bind capabilities and state
ownership and point here. PLAN prepares a handoff and may write its authorized planning artifacts.
Status, Next, and plain (unqualified) Resume inspect or select state only. Those three modes may
not execute source or mutate source, `board.md`, or `log.md`; an explicit handoff projection may
write its own projection.

The bounded None route is self-contained in `intake-and-gate.md`; its focused preflight and receipt
replace workspace/Task artifacts, not authorization, scope, preservation or truthful validation.
For Lite, use `../lite-plan.tmpl.md` and its plan/log/usage/decisions. Do not continue through the Full preflight artifacts below unless the task upgrades.

The authority order is user, current contract/specification, protected acceptance and tests, then
current implementation. A contract or specification contradiction is surfaced and blocks the
affected scope. This guide never silently changes the procedure that authorized a Task already in
progress. A changed contract, dependency output, configuration, input, or relevant source
fingerprint invalidates only the dependent checks; re-ground and revalidate them before continuing.

## Authorization and preflight

Run begins only after explicit execution intent, including an existing scoped PLAN+RUN request. Record that authorization once and apply [communication.md](communication.md) throughout; a status question does not revoke it. The coordinator verifies current task-board state, applicable decisions and blockers, the task brief, readiness records, contract, dependency outputs and environment. For a long workspace use the verified current-work view in [status.md](status.md) plus necessary source records; do not reread unrelated closed history. A missing/stale projection is rebuilt from authoritative records during authorized RUN, never trusted as permission. The preflight records the protocol and contract
revisions, relevant fingerprints, declared Write scope, executor binding, and the current tree. It
checks that the Task is Ready, its dependencies have their required outputs, the environment can
perform the declared checks, and the source is inside the declared write scope. A stale Ready
fingerprint cannot authorize execution.

Freeze the source and protected expectations at the review boundary. If existing test files are
protected, add coverage in a new file; do not silently reinterpret byte preservation as merely
preserving assertions. Otherwise an executor may add a test or
disposable fixture needed to observe behavior, but cannot remove, weaken, disable, or rewrite a
protected acceptance expectation without a prior superseding decision. Validators compare against
the declared expected behavior and valid semantic equivalents; they never derive expected values
from the candidate's output. Real outputs and inputs are read-only to validators. Disposable
directories may be created and removed after the observation, with pre-existing sentinels
preserved.

For Full, use [execution checks](full-checks.md) when the harness lacks complete capture or
canonical lint automation. Establish effective write confinement before the first PLAN write/check and retain it in RUN; record
its observed capability separately from instructions. Prepare the obligation/evidence index once,
snapshot the executed scripts and selected input membership, and close with affected checks.

## State transitions

New visible states and exact legacy mappings are defined in [terminology.md](../terminology.md#states-and-observations). Draft is unprepared/deferred; Ready to run is prepared, In progress implements, Checking verifies, Complete satisfies mandatory task checks. Blocked, Interrupted, Skipped and Unverifiable are distinct. The historical internal transition names below remain readable; relabeling never certifies success.

The Task state is distinct from evidence grades and from the board's current execution status.
`Ready` means PLAN's preparation and integrated readiness checks passed with its handoff and
fingerprints; it does not mean source execution passed. The normal Task path is:

```text
Ready → preflight → implementing → target validation →
  correction (only after a failed implementation check) →
  affected integration validation → Point complete
                                      ↘ blocked
```

Preflight failure, an unavailable required capability, a contract/validator/environment defect,
budget exhaustion, or an unresolved contradiction blocks the affected scope with evidence. An
optional, user-authorized descope is `skipped`; it is not completion of a mandatory acceptance.
Task `complete` requires its target, surrounding, affected integration, and required review
evidence. Initiative `complete` additionally requires deliverable acceptance of the merged deliverable,
final outputs, packaging and reproducibility where applicable. All tasks passing is insufficient
to close an initiative.

When a release names an initiative in scope, that initiative remains subject to this global
acceptance obligation until the evidence passes. A board with no in-progress rows, or a board
whose Tasks are all complete, cannot infer release acceptance; the release sweep consumes the
named workspace's existing global-acceptance evidence rather than creating a second status source.

At serialization or unit boundaries, global checks include applicable valid adversarial inputs
from the declared domain and the actual consumer parser/round trip. Nominal sample output alone
does not prove preservation of arbitrary allowed strings or numeric values.
Before implementation, record required supported producer/consumer targets and available validation environments in the contract. Record the actual producer and consumer runtimes and the supported range being claimed. A pass on
one runtime does not establish compatibility with another. An unverified required target blocks
the Task or global obligation that owns it; an outstanding mandatory global obligation prevents
initiative completion. Optional targets remain unverified without blocking the authorized narrower
scope. Independent unaffected work may proceed. A cross-runtime discrepancy keeps both
observations and their environments visible.

The executor writes only in the Task's Write scope. After implementation it runs the task check and
the checks for the affected surrounding behavior. After merge it runs the Task's affected
integration checks on the merged tree, including semantic consumers outside the file-level Write scope
intersection when the interface, configuration, output, or dependency relationship reaches them.
Before initiative closure, deliverable acceptance covers the integrated flows and initiative obligations
against the final deliverable.

For release work, the Coordinator records the explicit workspace scope before running the sweep;
unknown scope blocks the tag pending clarification. The release-gating set is the deduplicated union
of active and selected workspaces: selection never exempts another active workspace from its
mandatory lint and acceptance check gates. Selected workspaces also require current deliverable acceptance
regardless of board status. Historical closed and parked workspaces that are neither active nor
selected remain non-gating; warn-severity lint rows retain their severity.

<a id="evidence-and-recovery"></a>
## Verification records and recovery

Every target, correction, integration, or global validation is an observation. Record the actual
UTC start and end (or timeout), literal command, cwd, tool and runtime, executor/actor and context,
input/code/config/dependency/contract revisions, stdout, stderr, exit code or signal, timeout, and
artifact paths and hashes. Store one immutable raw check record per actual validation, referencing shared immutable objects where available; the local report
may summarize it but cannot replace it. A printed PASS is not evidence when a child process,
wrapper, generated artifact, or package failed. Check a real child return code, timeout and signal
independently of wrapper output. A validation command's own process result is authoritative; a
helper that prints PASS while its child failed is a failed observation.
Every required assertion in a compound check must propagate failure to that process result.
`set -u`, `pipefail` or a final PASS alone does not do this; use checked subprocesses or explicit
failure exits for each required condition. Exact-byte edits and checks preserve the specified
delimiter and final newline; do not normalize either away.

Choose an accessible evidence destination before the check, so a missing export is handled at
capture time. Capture using the harness's complete exported event or direct stdout/stderr
capture. An export must remain independently accessible after handoff; otherwise save the raw
command result locally. Never type a shortened command, paraphrased output or later clock reading
into a file labelled raw. Record unavailable metadata as `n/a`, not midnight, zero, or an inferred
model/effort. Fingerprint the actual source/tests/config/inputs before the check and confirm they
still match afterward; hash produced artifacts afterward. If they change, retain the old result
as historical and revalidate only affected obligations. A pre-edit test hash does not identify
post-edit coverage. For Full, use `full-checks.md` for script-saving capture and connected
canonical lint execution. The smaller `evidence-capture.md` example serves the other routes.

One captured command may discharge target, surrounding and integration obligations when its
observed coverage includes them all; index that same observation instead of rerunning unchanged
checks to populate headings. Do not append equivalent auxiliary assertions or repeat a successful
check during closure when its inputs and required coverage are unchanged. A final PASS is optional unless the consumer requires it; when used,
emit it only after all relevant children succeed. Full/Lite append actual start/terminal usage
events; missing telemetry does not block execution and must not be reconstructed.

The first validation is recorded separately and is not a correction cycle. One shared persistent
pool permits at most three failed correction-validation cycles for a Task across the executor,
reviewer, checker, interruptions, resumptions, and sessions. A successful correction resets no
counter.

Task IDs survive renaming. On split, merge or supersession, record ancestor IDs and unresolved failure IDs in the existing attempt journal. Each failed cycle has one stable event ID; descendants addressing the same failure reference the same spent pool, and a merge takes the union of event IDs. A split never grants a fresh allowance for unresolved old work. A new unrelated responsibility receives its own pool only with its distinct requirement/acceptance and no inherited failure. Preserve no-progress observations and the two-cycle unowned integration pool; attribution transfers a cycle once. Reassignment, translation or reopening cannot erase spent work. Validate lineage before another correction. Two identical no-progress observations stop immediately, even if fewer than three cycles
were spent. Never invent a narrower cap, reset the count under a new actor, or count a repeated
observation as a new distinct cycle. There is one initiative-wide unowned-integration pool of two
cycles shared by all unowned integration faults. A dependency artifact failure is first recorded as
a preflight/dependency cause; if it is an unowned integration fault, its cycle consumes this same
pool. When attribution identifies an owner, transfer the cycles already spent exactly once to that
owner's Task; the initiative pool and Task counter both retain the spent count, which survives
resume.

Before repeating an interrupted command or completion update, inspect the tree, process results, task-board/report revisions, checkpoint and raw records to
determine whether it occurred. If occurrence is incomplete or unknown, record `observe-incomplete`
and preserve the history before choosing a safe continuation. Do not duplicate an irreversible
action merely because a session ended without a terminal message. Lifecycle rows and attempts
serialize and resume from the workspace; missing end data stays `n/a`.

## Failure classification and correction

Consume retained failed observations before another check, including on resume. Diagnose from
their command, output and relevant input fingerprints; do not repeat an unchanged failed check
to rediscover its result. Recheck only after a recorded relevant input or environment change,
or an actually justified permitted operational recovery below. Narrower diagnostic inspection
remains allowed; diagnosis alone does not justify repeating acceptance.

Classify a failed observation before correcting it: implementation, missing or ambiguous
requirement, incomplete output, required edge case, dependency/integration, contradictory spec,
validator, environment, capability, or undetermined. Only an implementation fault may be corrected
within the shared implementation budget. A contract, requirement, validator, environment,
capability, dependency, or undetermined cause stops the failed action and emits a small packet with the
exact requirement/clause and revision, expected versus observed result, reproducer and raw-evidence
pointer, affected consumers, attempts/cycles already used and remaining, and the smallest
unresolved decision. The packet is a decision aid; it does not silently replan, broaden scope,
upgrade model or effort, dispatch a frontier role, or make up a missing requirement.

A permitted operational recovery is separate from implementation correction: once per unchanged failure signature (cause, command, relevant inputs and environment), inspect the failed process and records, then correct a workspace-local temporary-path issue, interrupted local capture, or restart an already-configured foreground tool after confirming prior writers stopped. One retry may establish recovery; if it fails, block that action with both records. A relevant external change may justify a new diagnosis, but a new actor/task name does not reset this allowance. Record recovery kind, action, result and spent allowance in the same journal. No global install, credentials, restricted access, protected expectation change or invented requirement is authorized. All other operational causes remain blocked pending the concrete needed capability or decision.

Each failed implementation correction appends an attempt-journal entry before another attempt and
re-reads the earlier entries. The entry names the observed failure, correction, validation command,
result, and cycle count. A correction that changes a contract or acceptance requires the authorized
superseding decision first, then re-grounding and revalidation. Generic escalation records its
trigger, minimal scope, budget and observed outcome.

<a id="independence-and-evidence-grades"></a>
## Verification method and independence

Mechanical execution, focused semantic review, and adversarial audit are separate capabilities.
The same agent may observe a deterministic command; that observation is real command evidence with
its actual provenance, while its own review remains self-review and is not independent. Use an
independent session or human fallback only when the risk or obligation requires semantic
independence; record the actual actor, profile, context and isolation. If the required isolation is
unavailable, mark that evidence obligation unavailable/blocked and do not claim independent E1. A
renamed role or a fresh label is not proof of independence. Routine Run has no universal frontier
checker, majority vote, or audit. A vote cannot erase a confirmed correctness failure.

Keep historical E0–E3 grades readable. New evidence also records provenance and independence
dimensions. E1 is command-verified evidence from an actually independent checker; E2 is a named
semantic review gate when no honest command exists; E0 is explicitly unverifiable; E3 is an
assertion. Grades are derived from the evidence, never self-declared, and E2 is not numerically
ordered against E3. Missing capability is not zero evidence.

<a id="integration-global-acceptance-and-close"></a>
## Integration, deliverable acceptance, and close

After a Task's target and related regression checks pass, integrate its scoped change and recheck the
merged tree. Reuse evidence only while every relevant source, contract, configuration, dependency,
input, selector membership, runtime, protocol revision and relevant freshness window matches. Unknown dependencies require conservative verification. Selective invalidation preserves unaffected history
and invalidates the changed consumers and crossing artifacts. The integration check must include
semantic consumers that a Write scope-only intersection cannot see.

Deliverable acceptance then checks the final integrated flows, every required global obligation, final
artifacts, packaging, source/install boundary, reproducibility, and the complete acceptance command
where applicable. It must catch a producer/consumer unit mismatch such as cents rendered by a
producer while a consumer expects dollars, even if every local unit suite is green. Missing package
files, child failures, stale inputs, protected-test weakening, isolation gaps, and unavailable
environment capabilities remain failed or unverifiable observations.

For compound global checks, save the complete script before execution and include it in input
fingerprints; a label describing an inline assertion cannot replace its code in the handoff.

Before choosing the terminal state, the Coordinator opens every required evidence reference,
checks its actual result and relevant final revisions, and matches it to the obligation it proves.
A generic transcript label without an accessible export is missing evidence. Missing, stale or
failed required evidence/review/coverage blocks its owning scope; summaries cannot repair it.
Only all required Task obligations permit Task complete; only all required global obligations
permit initiative complete. Board, report and final response must express that same scope and
outcome. Role completion is separate: a reviewer may successfully report a blocked product,
but a blocked implementation is not successful product completion. Unknown telemetry and
optional coverage remain non-gating.

On complete, the Coordinator records the final report, raw evidence pointers, immutable revisions,
attempt and rework counts, and the board status. On blocked, it records the same evidence and the
failure packet; blocked, skipped, completed, and unverifiable outcomes remain distinct. `board.md`
is the canonical current state, `log.md` is append-only history, `coordinator.md` is a projection,
and `usage.md` receives its normal lifecycle rows. A completion update records the last fully recorded event and intended task state. If interrupted between record/report/board writes, reconcile all three against actual outcomes before repairing the incomplete update. A completed side effect is not repeated merely to fill a missing terminal row; unchecked work remains Interrupted or Checking. A projection never overrides counters, permissions or actual results.

A closure report or local Run report is evidence,
not permission to erase prior history. Initiative closure waits for deliverable acceptance and its
review/sign-off obligations. Once they pass, write the closure records, check only fields and
obligations affected by those writes, and respond. Do not restart whole-plan lint, guide traversal
or housekeeping after product acceptance without a relevant change, new failure, or explicit
release/audit request. Reuse unchanged PLAN readiness checks; this does not skip initial PLAN lint,
required product/review checks, or the separately requested release sweep.

## Run record

The local report contains, in order: authorization and preflight; implementation and target
observation; surrounding and integration observations; correction journal and any failure packet;
deliverable acceptance; independent semantic review when required; final status and unresolved risk.
Each observation links to its immutable raw record. Raw records are append-never/overwrite-never
artifacts named with a unique Run, Task, validation ordinal, and observed timestamp. Record
unknown telemetry as `n/a`; do not infer duration, tokens, cost, actor, independence, or success.

## Correction lineage consistency recipe

When tasks are reshaped, use stable failure IDs and cycle-event IDs in the existing journal.
A cycle pool follows unresolved work; several descendant tasks can reference the same pool. Merging distinct pools retains each allowance separately; their sum is informative and does not exhaust an unrelated pool. A combined failed correction has one event ID and names each affected pool once in `pool_ids`. Stop corrections involving an exhausted pool; separate unrelated work may continue.
Use this optional pure check when composing a split/merge. Callers validate failure attribution
against the original records; arbitrary IDs cannot manufacture a fresh budget. Successful
corrections, observations and dispatches are not failed-cycle events.

```python
def correction_usage(events, pool_ids):
    unique = {}
    for event in events:
        identity = event['cycle_id']
        if not identity or event.get('kind') != 'failed-correction':
            raise ValueError('invalid correction event')
        if identity in unique and unique[identity] != event:
            raise ValueError('conflicting correction history')
        unique[identity] = event
    selected = set(pool_ids)
    pools = {pool: 0 for pool in selected}
    counted = set()
    for identity, event in unique.items():
        affected = event.get('pool_ids', [event.get('pool_id')])
        if not isinstance(affected, list) or not affected or any(not isinstance(p, str) or not p for p in affected):
            raise ValueError('invalid correction pool')
        for pool in selected & set(affected):
            pools[pool] += 1
            counted.add(identity)
    return {'spent': len(counted), 'pools': pools,
            'remaining': min((max(0, 3 - n) for n in pools.values()), default=3),
            'exhausted': any(n >= 3 for n in pools.values())}


def transfer_lineage(previous, descendants, unresolved, failure_pools):
    required = set(previous) & set(unresolved)
    inherited = set().union(*(set(failures) for failures in descendants.values())) if descendants else set()
    if required != inherited or not required.issubset(failure_pools):
        raise ValueError('lost, invented or unrelated failure lineage')
    return {identity: sorted({failure_pools[failure] for failure in failures})
            for identity, failures in descendants.items()}
```
