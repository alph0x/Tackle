# Design and contract — depth for the [PLAN card](plan-card.md)

<a id="step-5--compile-behavior-acceptance-contracts-and-briefings"></a>
The card's step 4 links here for the full compilation procedure. Each stage produces an artifact the next
consumes; the Task brief is the final worker-facing projection.

## Behavior and outputs

For every requirement, record a stable criterion id, required behavior, observable output or effect, normal
and boundary cases, and any valid semantic alternative. Name exact bytes, order, paths, stdio or exits only
when a consumer depends on them. A requirement is covered for execution only when a Task case and a check
demonstrate its observable behavior; an id copied into a briefing without its behavior is an omission and
stays a readiness gap.

## Acceptance and test strategy

For each criterion and Task, name a task check, an affected surrounding check and an evidence slot. Add a
positive and a negative fixture for each validator or contract boundary. The negative fixture must expose an
implementation that satisfies a keyword, file-existence or test count check while violating the required
behavior. A negative fixture also covers invalid or tampered evidence, not only a behavior violation.
A scenario-form case counts only with its Check; a scenario without one is a readiness gap.

Choose the check type during PLAN, before implementation. Prefer one end-to-end check through the real
public consumer as the sole new test when it covers the criterion; a complex integrated feature needs one when
feasible. Name its replay artifact destination. If an obligation requires isolation, record why E2E cannot
cover it and enumerate the applicable failure modes with expected outcomes before implementation or an
isolated test is written. No Task plans a unit test to be added after the behavior it covers is implemented
([testing.md](testing.md)).

Derive cases from the declared input domain and each output consumer, not only sample data, separating
normal, adversarial but valid, and out-of-domain inputs. Strings crossing a serializer exercise delimiters,
quotes, line breaks and Unicode through the consumer's parser/round trip; numeric/unit boundaries consider
zero, signed values, precision and representable extremes. Select applicable cases, not a generic test quota.
State expected values before implementation. Never invent rejection rules for unspecified invalid inputs or
reject valid encodings merely because their bytes differ.

## Contracts and decisions

Compile interfaces, invariants, dependency crossings, configuration consumers and recovery behavior before
writing the Task brief. Product decisions stay user-owned; reversible technical choices may be delegated when
the choice and its evidence are recorded. When a contract changes, supersede the decision before regenerating
dependent Task clauses.
A decision applied by one task names it in `**Owner**`, and a decision that changes the meaning of contract
clauses names them in `**Clauses**`; the owner's brief cites the decision id and, at full detail, carries
each named clause compiled.

<a id="point-briefing"></a>
## Task brief

For each prepared task, compile these obligations into the existing fields:
- Observable outcome and authoritative requirements, distinguishing hard constraints from delegated implementation choices
- Inputs and actual revisions; produced artifacts, consumers and compatible interfaces
- Dependencies and complete write scope; unresolved material assumptions with their affected consumers
- Verified reference context, recommended approach and valid alternatives
- Acceptance criteria (what must hold), task/regression checks (how to observe it), and verification-record destinations (what happened)
- Recovery, procedure revision, stable identity and inherited failure-cycle references
- Repository conventions the executor cannot infer, such as the commit message format, stated in the brief whether or not the repository has a conventions file; every cwd-dependent command carries its own `cd` or `-C`
- Forbidden action classes the executor must not take, each allowed only where the write scope or an explicit owner decision allows it: deletion outside the write scope, caches included; privilege escalation and package installs; publication (push, tag, release, registry upload); unscoped recursive searches outside the repository
- The detail level: `**Detail**: full` puts every Definition-of-ready item in scope; `interface` fixes only the goal, write scope, dependencies, requirement owners and symbol ledger, and leaves internal detail to a later PLAN pass
- The symbol ledger of a brief that declares `**Detail**`: `**Produces**` lists each name the task creates for another task or check, and `**Consumes**` each name it uses without creating it, with its source: `from T-NN`, `from T-NN [sibling]`, or `exists` and an anchored citation in the form `path.ext:NN — "fragment"`, or `path.ext@<rev>:NN — "fragment"` when the cited file has changed since the brief was grounded; a field is `none` when empty, and under `full` both fields are required

The worker-facing package also names the absolute repository and checkout, task workspace,
verification-record root, and cwd for every command. Keep these locations distinct when they differ.
Approach guidance separates mechanical preparation from named reviewer judgment: the executor
collects and validates inputs, while the assigned reviewer decides semantic questions the executor
cannot infer. State the exact consumer and observable effect for each requirement, including a valid
alternative where formatting or implementation details are intentionally flexible.

For aggregate gates, state the denominator and required completion explicitly. For example, five passing of six
is `5 / 6 = 83.333…%`; it is not acceptance when all six are required. Require
complete successful child records when all children are mandatory. A wrapper result cannot hide a
failed or missing child record. When read coverage matters, observe actual read consumers
(including Python, awk or child processes); keyword presence is not read evidence.

<a id="prepared-operation-example"></a>
### Prepared operation example

A prepared operation is a per-job procedure in the brief, not a new always-read RUN recipe or
installed runner. Declare its fixed input revision, cwd and paths, exact before/after bytes and
hashes, operation identity, unique anchors, native child command and recovery conditions. The
consumer recognizes a matching operation identity and full poststate before requiring the old
anchor. Preserve the prior check status: an already-applied result does not turn a failed or missing
check into success. For a pending application, require the exact before hash and one anchor; drift,
zero or duplicate anchors stop before writes. Record apply and check statuses separately.

After an interruption, compare the target and receipt first. A verified full poststate permits only
check-only recovery; a pristine before-state permits the pending application; mixed or concurrent
state stops for reconciliation. Never repeat an unknown effect or rewrite unrelated bytes. The
declared child must propagate its actual exit even when it prints `PASS` before exiting nonzero.
Equivalent direct edits remain valid when they produce the declared bytes and checks.

The fixed optional procedure is [`prepared_job_example.py`](../../scripts/prepared_job_example.py); running or importing it requires the owner’s explicit authorization under the [script consent rule](../../scripts/README.md#consent). Its test copies these exact shipped bytes to `prepared_job.py` in a fresh fixture cwd, then invokes Python with `-I` and no arguments. The fixture provides `owned/revision.txt` (`fixture-initial\n`), `owned/config.txt` (`version=old\n`) and `records/`; the only permitted effects are the exact `version=new\n` target and its receipt. Preserve the native exit code and receipt statuses; an interruption or missing/unknown check is not success. An equivalent direct edit remains valid when it yields the same target and child-check result.

<a id="prepared-read-examples"></a>
### Prepared read examples

These examples are executed from a fresh fixture cwd. The labeled fence bodies are the consumers;
the fixture input is `public/input.txt` with initial bytes `read-ok\n`.

```python
# fixture-read: python
from pathlib import Path
print(Path("public/input.txt").read_text(), end="")
```

~~~awk script
# fixture-read: awk
{ print }
~~~

The Python example opens the declared relative path, and awk receives that same input as its file
argument. A check records actual stdout and verifies a changed fixture value is observed on replay;
missing input fails. These examples establish local consumer reads only, not general agent compliance.

# Step 5.5 — Architecture recommendation

If Full, recommend an architecture only where the consumers need a structural choice, recorded as `D-xx` in
`decisions.md`. Open `foundations.md` for each chosen structural principle and its grounded source; never
impose layers, dependencies or design patterns as generic quality requirements. The recommendation must cover:

- **Boundaries and direction** — only the boundaries the consumers cross, and the dependency direction that
  keeps those crossings valid.
- **Ownership** — which component owns each interface or protocol, and how the implementation is supplied at
  the boundary.
- **Quality fit** — applicable quality checks derived from observable consumer needs, such as a stable
  interface, isolation or a measurable performance bound.
- **Foundations rows** — a `foundations.md` row for every structural choice (decision → principle → source,
  per the grounding rule).

# Step 5.75 — Stabilize the design contract (Full only)

Stabilize `design-contract.md` within the current PLAN preparation, before assigning Ready, without waiting
for a full additional planning session. Tasks cite the compiled contract sections and inline their clause id,
revision and hash, never a whole specification. A contract change after a Task is Ready requires a superseding
decision and regenerated clauses.

Compatibility is an intake/contract field: name required supported producer/consumer targets and available
validation environments before implementation. With no declared range, report only observed coverage. Missing
required coverage is unverified/blocked; optional targets cannot silently become mandatory. Test valid
boundary data through the actual consumer for each claimed target.

Readiness means a fresh executor can implement from the brief and named inputs without inventing product behavior. Required clauses stay inline with source/revision/hash; optional depth stays linked. Additional reading requires a dependency, relevant change or concrete uncertainty. Record repeated clarification or rework caused by omitted brief requirements as a planning failure in the existing task report; distinguish it from changed user requirements.

<a id="code-style"></a>
## Code style

Self-documenting code: Clean Code + SOLID; no explanatory inline comments. Doc-comments belong
on public surfaces only; put the why in commits/docs. An internal explanatory comment is a review
finding: clarify the code rather than rewording the comment. Apply this code-work acceptance in
None, Lite and Full, subject to the authority order. The checker reviews the diff for smells,
redundancy, SOLID, naming and self-documenting code; the review remains separate from test results.
