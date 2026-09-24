# Testing doctrine

Agent speed makes verification valuable: spend the saved time on evidence that exercises the
Task's observable contract through its real consumer. Choose test depth from behavior and Write
scope, not from a generic count.

## PLAN chooses the check before code

For each code Task, PLAN names the behavior, cases, check type, expected result, and evidence
destination before implementation. Prefer an end-to-end (E2E) check through the public boundary
as the sole new test mechanism when it can cover the contract. Complex features need an E2E
check of their integrated flow when that boundary is executable. An E2E check can discharge Task,
surrounding, and integration obligations together when its actual coverage does. Reuse sufficient
existing checks; do not create unit tests or duplicate assertions to satisfy a tier quota.

If E2E cannot exercise a required failure reliably or an executable consumer is unavailable,
PLAN records that limitation and the narrowest honest alternative. Before testing a system in
isolation, write down every identified applicable way it can fail, with its expected observable
outcome. Derive isolated cases from that inventory before writing implementation. Do not claim
exhaustiveness beyond the declared input domain and known interfaces; newly discovered failure
modes update the inventory before the corresponding implementation change.

## Test-first execution

For the bounded None route, follow `intake-and-gate.md` without expanding the task into this
template-driven loop. Existing failing tests already establish red; do not duplicate them or add
a PASS wrapper just for ceremony. A meaningful gap may receive focused additive coverage.

For new tests, red → green → refactor is the Executor's default shape:

1. Write the chosen failing test — **see it fail** at the intended boundary.
2. Minimal implementation — see it pass.
3. Refactor with the suite green.

Opting out requires a `D-xx` recorded before implementation. "Seen failing" is the mechanical
form of the verifier's `repro` question: a test never seen failing proves little about its bite.
Never write a unit test after implementing the behavior it covers. For a change to existing code,
write any needed unit regression before changing that behavior; a later discovered isolated gap
starts with its failure-mode inventory and test before the next implementation change. A general
test-first opt-out does not authorize post-implementation unit tests.
The red-phase evidence answers `repro`; the verifier does not re-break code by hand.
Consume that failed evidence and diagnose first. Repeat the failed acceptance check only after a
recorded relevant input or environment change, or justified permitted operational recovery.
Narrower diagnostic inspection remains allowed; diagnosis alone does not justify repetition.

Each required assertion must make its command fail when false. `set -u`, `pipefail` and a final
PASS do not establish this; use checked subprocesses or explicit failure exits. Preserve exact
specified bytes when editing and comparing, including the delimiter and final newline.

## Check types and depth

Select only the checks that cover a distinct contract obligation. T1 can be the sole new test;
T0 is conditional, never an automatic prerequisite. Fold each selected check into the Task's
acceptance command — the same convention as `quality-dimensions.md`, whose **Test depth** axis
links here. Historical T0–T3 labels remain readable in pinned workspaces.

| Tier | What | Fires when (Write scope heuristic) | Acceptance check fragment shape |
|---|---|---|---|
| **T1 · E2E acceptance** | Test through the real public consumer: API call, CLI invocation, rendered UI, or complete workflow. | Default for executable behavior; required for a complex integrated feature when feasible. | Boundary check asserts the observable contract and produces a replayable artifact. |
| **T0 · isolated unit** | Focused test of a behavior the E2E check cannot observe reliably. | An uncovered failure mode requires isolation; PLAN records why and inventories applicable failures first. | Failing test precedes the implementation it covers; native suite result is captured. |
| **T2 · property-based** | Invariants over generated inputs: round-trip, commutativity, bounds. | Parsers, serializers, transforms, money/calculation, round-trips when example cases cannot cover the invariant. | Prefer the real consumer; record seed and case count needed for replay. |
| **T3 · fuzz / torture** | Adversarial input or hostile scheduling under a time budget. | Untrusted input, concurrency, state machines when a bounded adversarial run addresses a distinct risk. | Prefer the real consumer; record seed, time budget, and native result. |
| **Mutation** | Validates the selected check: break behavior, watch the check fail. | High-risk invariants (money, security, data integrity). | Mutation score ≥ a declared threshold, or one deliberate break → acceptance check fails. |

Mutation is not a test you write — it audits whether the selected check bites. The observed red
phase supplies its cheap form without adding a unit-test layer.

## Replayable E2E artifact

At the end of each E2E run, retain one verifiable, repeatable artifact: the exact command or saved
checked script, accessible fixtures and input revisions, expected outputs from the contract,
observed stdout/stderr and child exit/timeout/signal, runtime and relevant environment, produced
outputs, and hashes of inputs and outputs. A complete existing raw capture plus referenced stable
fixtures can be that artifact; do not duplicate it in prose. Include a short replay instruction
from the recorded cwd. Replaying must use a disposable copy or a fresh run destination so the
original raw record, fixtures, and output hashes remain immutable; the replay compares its new
result to the recorded expected and observed result. A PASS string, screenshot, test count, or
hash without runnable inputs does not make an E2E run repeatable. The artifact's required
assertions must propagate failure to the native result, and changed inputs invalidate the
affected result.

## What this changes in practice

- Serialization checks parse output with the real consumer or assert a round trip over valid
  delimiter/quote/newline/Unicode inputs. Numeric checks retain signs and precision. Choose cases
  from the declared domain, keep invalid-input policy separate, and compare with contract-derived
  expectations; a nominal file snapshot or test count alone cannot discharge this obligation.
- `plan.md` §6.1: choose the E2E or justified alternative, test-first by default, and never write
  unit tests after their implementation.
- Task Acceptance names only the selected checks, an isolation failure-mode inventory when needed,
  and the E2E replay artifact destination. Unselected types need no waiver or test quota.
- Verifier: `repro` is answered by red-phase evidence in `history.md`, not by hand-breaking the code.

## Compatibility before implementation

Record the required supported producer/consumer versions and the environments available for
validation before editing. Choose targets from the user/spec or repository contract; don't invent
a wider support promise from the installed runtime. Each claimed target needs its own observed
check or exact externally supplied evidence. Missing required coverage blocks that obligation;
optional targets remain unverified without blocking a narrower authorized scope. Preserve both
results on a discrepancy. Cross-version serializer tests use valid domain strings and the consumer
parser, not assumptions about a library's quoting defaults. An evaluator's later run is separate
coverage and cannot retroactively justify the executor's earlier completion claim.
