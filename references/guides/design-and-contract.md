# Step 5 — Compile behavior, acceptance, contracts, and briefings

PLAN compiles the work in this order. Each stage produces an artifact consumed by the next stage;
the Task brief is the final worker-facing projection.

## Behavior and outputs

For every requirement, record a stable criterion id, the behavior it requires, the observable
output or effect, normal and boundary cases, and any valid semantic alternative. A requirement is
covered for execution only when a Task case and a check demonstrate its observable behavior. An id copied into a
briefing without its behavior is an omission and remains a readiness gap.

## Acceptance and test strategy

For each criterion and Task, name a task check, an affected surrounding check, and an evidence
slot. Add a positive fixture and a negative fixture for each validator or contract boundary. The
negative fixture must expose an implementation that satisfies a keyword, file-existence, or test
count check while violating the required behavior.

Choose the check type during PLAN, before implementation. Prefer one end-to-end check through the
real public consumer as the sole new test when it covers the criterion; a complex integrated
feature needs one when feasible. Name its replay artifact destination. If an obligation requires
isolation, record why E2E cannot cover it and enumerate the applicable failure modes with expected
outcomes before implementation or an isolated test is written. No Task plans a unit test to be
added after the behavior it covers is implemented. See [testing.md](testing.md).

Derive cases from the declared input domain and each output consumer, not only sample data.
Separate normal inputs, adversarial but valid inputs, and inputs outside the declared domain.
For strings crossing a serializer, exercise delimiters, quotes, line breaks and Unicode through
the consumer's parser/round trip. For numeric/unit boundaries, consider zero, signed values,
precision and representable extremes; select applicable cases rather than requiring a generic
test quota. State expected values before implementation. Do not invent rejection rules for
unspecified invalid inputs or reject valid encodings merely because their bytes differ.

## Contracts and decisions

Compile interfaces, invariants, dependency crossings, configuration consumers, and recovery
behavior before writing Task brief. Product decisions remain user-owned. Reversible technical
choices may be delegated when the choice and its evidence are recorded. When a contract changes,
supersede the decision before regenerating dependent Task clauses.

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

If Full, recommend an architecture only where the consumers need a structural choice. Record the
decision as `D-xx` in `decisions.md`. Open `foundations.md` for each chosen structural principle
and its grounded source; do not impose layers, dependencies, or design patterns as generic quality
requirements.

The recommendation must cover:

- **Boundaries and direction** — name only the boundaries the consumers cross and show the
  dependency direction that keeps those crossings valid.
- **Ownership** — state which component owns each interface or protocol and how the implementation
  is supplied at the boundary.
- **Quality fit** — derive the applicable quality checks from observable consumer needs, such as a
  stable interface, isolation, or a measurable performance bound.
- **Foundations rows** — every structural choice gets a `foundations.md` row (decision → principle
  → source, per the grounding rule).

# Step 5.75 — Stabilize the design contract (Full only)

Stabilize `design-contract.md` during the current PLAN preparation before assigning Ready. Do not
wait for a full additional planning session. Tasks cite the compiled contract sections and inline
their clause id, revision, and hash; they do not inline a whole specification. A superseding
decision and regenerated clauses are required if the contract changes after a Task is Ready.

Compatibility is an intake/contract field: name required supported producer/consumer targets and
available validation environments before implementation. Where no range is declared, report only
observed coverage. Missing required coverage is unverified/blocked; optional targets cannot silently
become mandatory. Test valid boundary data through the actual consumer for each claimed target.

Readiness means a fresh executor can implement from the brief and named inputs without inventing product behavior. Required clauses stay inline with source/revision/hash; optional depth stays linked. Additional reading requires a dependency, relevant change or concrete uncertainty. Record repeated clarification or rework caused by omitted brief requirements as a planning failure in the existing task report; distinguish it from changed user requirements.

## Code style

Self-documenting code: Clean Code + SOLID; no explanatory inline comments. Doc-comments belong
on public surfaces only; put the why in commits/docs. An internal explanatory comment is a review
finding: clarify the code rather than rewording the comment. Apply this code-work acceptance in
None, Lite and Full, subject to the authority order. The checker reviews the diff for smells,
redundancy, SOLID, naming and self-documenting code; the review remains separate from test results.
