# Step 5 — Compile behavior, acceptance, contracts, and briefings

PLAN compiles the work in this order. Each stage produces an artifact consumed by the next stage;
the Point briefing is the final worker-facing projection.

## Behavior and outputs

For every requirement, record a stable criterion id, the behavior it requires, the observable
output or effect, normal and boundary cases, and any valid semantic alternative. A requirement is
covered only when a Point case and a check demonstrate its observable behavior. An id copied into a
briefing without its behavior is an omission and remains a readiness gap.

## Acceptance and test strategy

For each criterion and Point, name a target check, an affected surrounding check, and an evidence
slot. Add a positive fixture and a negative fixture for each validator or contract boundary. The
negative fixture must expose an implementation that satisfies a keyword, file-existence, or test
count check while violating the required behavior.

Derive cases from the declared input domain and each output consumer, not only sample data.
Separate normal inputs, adversarial but valid inputs, and inputs outside the declared domain.
For strings crossing a serializer, exercise delimiters, quotes, line breaks and Unicode through
the consumer's parser/round trip. For numeric/unit boundaries, consider zero, signed values,
precision and representable extremes; select applicable cases rather than requiring a generic
test quota. State expected values before implementation. Do not invent rejection rules for
unspecified invalid inputs or reject valid encodings merely because their bytes differ.

## Contracts and decisions

Compile interfaces, invariants, dependency crossings, configuration consumers, and recovery
behavior before writing Point briefings. Product decisions remain user-owned. Reversible technical
choices may be delegated when the choice and its evidence are recorded. When a contract changes,
supersede the decision before regenerating dependent Point clauses.

## Point briefing

For each point, write:
- Goal (single responsibility)
- Depends-on / Touches
- Context grounded in code
- Recommended approach
- Alternatives
- Done-signal (runnable command)
- Acceptance criteria

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
wait for a full additional planning session. Points cite the compiled contract sections and inline
their clause id, revision, and hash; they do not inline a whole specification. A superseding
decision and regenerated clauses are required if the contract changes after a Point is Ready.

Compatibility is an intake/contract field: name required supported producer/consumer targets and
available validation environments before implementation. Where no range is declared, report only
observed coverage. Missing required coverage is unverified/blocked; optional targets cannot silently
become mandatory. Test valid boundary data through the actual consumer for each claimed target.

## Code style

Self-documenting code: Clean Code + SOLID; no explanatory inline comments. Doc-comments belong
on public surfaces only; put the why in commits/docs. An internal explanatory comment is a review
finding: clarify the code rather than rewording the comment. Apply this code-work acceptance in
None, Lite and Full, subject to the authority order. The checker reviews the diff for smells,
redundancy, SOLID, naming and self-documenting code; the review remains separate from test results.
