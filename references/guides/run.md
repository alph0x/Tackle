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
replace workspace/Point artifacts, not authorization, scope, preservation or truthful validation.
For Lite, use `../lite-plan.tmpl.md` and its plan/log/usage/decisions. Do not continue through the Full preflight artifacts below unless the task upgrades.

The authority order is user, current contract/specification, protected acceptance and tests, then
current implementation. A contract or specification contradiction is surfaced and blocks the
affected scope. This guide never silently changes the procedure that authorized a Point already in
progress. A changed contract, dependency output, configuration, input, or relevant source
fingerprint invalidates only the dependent checks; re-ground and revalidate them before continuing.

## Authorization and preflight

Run begins only after explicit execution intent. The Coordinator records the intent and reads the
current `board.md`, `log.md`, relevant `decisions.md`, Point briefing, PLAN handoff, current
contract, dependency outputs, and environment. The preflight records the protocol and contract
revisions, relevant fingerprints, declared Touches, executor binding, and the current tree. It
checks that the Point is Ready, its dependencies have their required outputs, the environment can
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

The Point state is distinct from evidence grades and from the board's current execution status.
`Ready` means PLAN's preparation and integrated readiness checks passed with its handoff and
fingerprints; it does not mean source execution passed. The normal Point path is:

```text
Ready → preflight → implementing → target validation →
  correction (only after a failed implementation check) →
  affected integration validation → Point complete
                                      ↘ blocked
```

Preflight failure, an unavailable required capability, a contract/validator/environment defect,
budget exhaustion, or an unresolved contradiction blocks the affected scope with evidence. An
optional, user-authorized descope is `skipped`; it is not completion of a mandatory acceptance.
Point `complete` requires its target, surrounding, affected integration, and required review
evidence. Initiative `complete` additionally requires global acceptance of the merged deliverable,
final outputs, packaging and reproducibility where applicable. All Points passing is insufficient
to close an initiative.

When a release names an initiative in scope, that initiative remains subject to this global
acceptance obligation until the evidence passes. A board with no in-progress rows, or a board
whose Points are all complete, cannot infer release acceptance; the release sweep consumes the
named workspace's existing global-acceptance evidence rather than creating a second status source.

At serialization or unit boundaries, global checks include applicable valid adversarial inputs
from the declared domain and the actual consumer parser/round trip. Nominal sample output alone
does not prove preservation of arbitrary allowed strings or numeric values.
Before implementation, record required supported producer/consumer targets and available validation environments in the contract. Record the actual producer and consumer runtimes and the supported range being claimed. A pass on
one runtime does not establish compatibility with another. An unverified required target blocks
the Point or global obligation that owns it; an outstanding mandatory global obligation prevents
initiative completion. Optional targets remain unverified without blocking the authorized narrower
scope. Independent unaffected work may proceed. A cross-runtime discrepancy keeps both
observations and their environments visible.

The executor writes only in the Point's Touches. After implementation it runs the target check and
the checks for the affected surrounding behavior. After merge it runs the Point's affected
integration checks on the merged tree, including semantic consumers outside the file-level Touches
intersection when the interface, configuration, output, or dependency relationship reaches them.
Before initiative closure, global acceptance covers the integrated flows and initiative obligations
against the final deliverable.

For release work, the Coordinator records the explicit workspace scope before running the sweep;
unknown scope blocks the tag pending clarification. The release-gating set is the deduplicated union
of active and selected workspaces: selection never exempts another active workspace from its
mandatory lint and done-signal gates. Selected workspaces also require current global acceptance
regardless of board status. Historical closed and parked workspaces that are neither active nor
selected remain non-gating; warn-severity lint rows retain their severity.

## Evidence and recovery

Every target, correction, integration, or global validation is an observation. Record the actual
UTC start and end (or timeout), literal command, cwd, tool and runtime, executor/actor and context,
input/code/config/dependency/contract revisions, stdout, stderr, exit code or signal, timeout, and
artifact paths and hashes. Store one immutable raw evidence file per validation; the local report
may summarize it but cannot replace it. A printed PASS is not evidence when a child process,
wrapper, generated artifact, or package failed. Check a real child return code, timeout and signal
independently of wrapper output. A validation command's own process result is authoritative; a
helper that prints PASS while its child failed is a failed observation.

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
checks to populate headings. A final PASS is optional unless the consumer requires it; when used,
emit it only after all relevant children succeed. Full/Lite append actual start/terminal usage
events; missing telemetry does not block execution and must not be reconstructed.

The first validation is recorded separately and is not a correction cycle. One shared persistent
pool permits at most three failed correction-validation cycles for a Point across the executor,
reviewer, checker, interruptions, resumptions, and sessions. A successful correction resets no
counter. Two identical no-progress observations stop immediately, even if fewer than three cycles
were spent. Never invent a narrower cap, reset the count under a new actor, or count a repeated
observation as a new distinct cycle. There is one initiative-wide unowned-integration pool of two
cycles shared by all unowned integration faults. A dependency artifact failure is first recorded as
a preflight/dependency cause; if it is an unowned integration fault, its cycle consumes this same
pool. When attribution identifies an owner, transfer the cycles already spent exactly once to that
owner's Point; the initiative pool and Point counter both retain the spent count, which survives
resume.

Before repeating an interrupted side effect, inspect the tree, process results, and raw evidence to
determine whether it occurred. If occurrence is incomplete or unknown, record `observe-incomplete`
and preserve the history before choosing a safe continuation. Do not duplicate an irreversible
action merely because a session ended without a terminal message. Lifecycle rows and attempts
serialize and resume from the workspace; missing end data stays `n/a`.

## Failure classification and correction

Classify a failed observation before correcting it: implementation, missing or ambiguous
requirement, incomplete output, required edge case, dependency/integration, contradictory spec,
validator, environment, capability, or undetermined. Only an implementation fault may be corrected
within the shared implementation budget. A contract, requirement, validator, environment,
capability, dependency, or undetermined cause stops affected work and emits a small packet with the
exact requirement/clause and revision, expected versus observed result, reproducer and raw-evidence
pointer, affected consumers, attempts/cycles already used and remaining, and the smallest
unresolved decision. The packet is a decision aid; it does not silently replan, broaden scope,
upgrade model or effort, dispatch a frontier role, or make up a missing requirement.

Each failed implementation correction appends an attempt-journal entry before another attempt and
re-reads the earlier entries. The entry names the observed failure, correction, validation command,
result, and cycle count. A correction that changes a contract or acceptance requires the authorized
superseding decision first, then re-grounding and revalidation. Generic escalation records its
trigger, minimal scope, budget and observed outcome.

## Independence and evidence grades

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

## Integration, global acceptance, and close

After a Point's target and surrounding checks pass, integrate its scoped change and recheck the
merged tree. Reuse evidence only while every relevant source, contract, configuration, dependency,
input, runtime, and protocol revision matches. Selective invalidation preserves unaffected history
and invalidates the changed consumers and crossing artifacts. The integration check must include
semantic consumers that a Touches-only intersection cannot see.

Global acceptance then checks the final integrated flows, every required global obligation, final
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
Only all required Point obligations permit Point complete; only all required global obligations
permit initiative complete. Board, report and final response must express that same scope and
outcome. Role completion is separate: a reviewer may successfully report a blocked product,
but a blocked implementation is not successful product completion. Unknown telemetry and
optional coverage remain non-gating.

On complete, the Coordinator records the final report, raw evidence pointers, immutable revisions,
attempt and rework counts, and the board status. On blocked, it records the same evidence and the
failure packet; blocked, skipped, completed, and unverifiable outcomes remain distinct. `board.md`
is the canonical current state, `log.md` is append-only history, `coordinator.md` is a projection,
and `usage.md` receives its normal lifecycle rows. A closure report or local Run report is evidence,
not permission to erase prior history. Initiative closure waits for global acceptance and its
review/sign-off obligations. Once they pass, write the closure records, check only fields and
obligations affected by those writes, and respond. Do not restart whole-plan lint, guide traversal
or housekeeping after product acceptance without a relevant change, new failure, or explicit
release/audit request. Reuse unchanged PLAN readiness checks; this does not skip initial PLAN lint,
required product/review checks, or the separately requested release sweep.

## Run record

The local report contains, in order: authorization and preflight; implementation and target
observation; surrounding and integration observations; correction journal and any failure packet;
global acceptance; independent semantic review when required; final status and unresolved risk.
Each observation points to its immutable raw file. Raw files are append-never/overwrite-never
artifacts named with a unique Run, Point, validation ordinal, and observed timestamp. Record
unknown telemetry as `n/a`; do not infer duration, tokens, cost, actor, independence, or success.
