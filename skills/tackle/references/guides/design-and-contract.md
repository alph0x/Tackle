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

<a id="point-briefing"></a>
## Task brief

For each prepared task, compile these obligations into the existing fields:
- Observable outcome and authoritative requirements, distinguishing hard constraints from delegated implementation choices
- Inputs and actual revisions; produced artifacts, consumers and compatible interfaces
- Dependencies and complete write scope; unresolved material assumptions with their affected consumers
- Verified reference context, recommended approach and valid alternatives
- Acceptance criteria (what must hold), task/regression checks (how to observe it), and verification-record destinations (what happened)
- Recovery, procedure revision, stable identity and inherited failure-cycle references

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
