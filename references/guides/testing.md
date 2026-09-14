# Testing doctrine

Agent speed makes verification valuable: spend the saved time on evidence that exercises the
Point's observable contract — unit, acceptance, property, torture, mutation, or review as the
risk requires. Test depth is chosen from the behavior and Touches, not from a generic count.

## Default: test-first

For the bounded None route, follow `intake-and-gate.md` without expanding the task into this
template-driven loop. Existing failing tests already establish red; do not duplicate them or add
a PASS wrapper just for ceremony. A meaningful gap may receive focused additive coverage.

For code points, red → green → refactor is the Driver's default shape:

1. Write the failing test — **see it fail**.
2. Minimal implementation — see it pass.
3. Refactor with the suite green.

Opting out requires a `D-xx` recorded before implementation. "Seen failing" is the mechanical
form of the checker's `repro` question: a test never seen failing proves little about its bite.
The red-phase evidence answers `repro`; the checker does not re-break code by hand.

## Depth tiers

Tiers escalate with risk and stack (T1 never replaces T0). Each fires on a Touches heuristic and folds into the done-signal as a runnable fragment — the same convention as `quality-dimensions.md`, whose **Test depth** axis points here.

| Tier | What | Fires when (Touches heuristic) | Done-signal fragment shape |
|---|---|---|---|
| **T0 · unit** | Tests over the case set, count-asserted where the set is finite. | Every code point — always. | Suite run → green; count assertion matches the case-set size. |
| **T1 · acceptance** | Test at the public boundary: API call, CLI invocation, rendered UI. | Changes user/API/CLI-visible behavior. | Boundary test asserts the observable contract end to end. |
| **T2 · property-based** | Invariants over generated inputs: round-trip, commutativity, bounds. | Parsers, serializers, transforms, money/calculation, round-trips. | Property runner ≥ N cases, seed recorded for repro. |
| **T3 · fuzz / torture** | Adversarial input or hostile scheduling hammered under a time budget. | Untrusted input, concurrency, state machines. | Fuzz run < time budget with zero unhandled crashes; suite repeated ×N for races. |
| **Mutation** | Validates the *suite*, not the code: break the code, watch the suite fail. | High-risk invariants (money, security, data integrity). | Mutation score ≥ threshold, or manual repro: one deliberate break → done-signal fails. |

Mutation is not a test you write — it is the audit that the tests you wrote actually bite. Its cheap form already runs in every test-first point: the red phase *is* a one-mutant mutation test.

## What this changes in practice

- Serialization checks parse output with the real consumer or assert a round trip over valid
  delimiter/quote/newline/Unicode inputs. Numeric checks retain signs and precision. Choose cases
  from the declared domain, keep invalid-input policy separate, and compare with contract-derived
  expectations; a nominal file snapshot or test count alone cannot discharge this obligation.
- `plan.md` §6.1: test-first by default for code points; opt-out via `D-xx`.
- Point Acceptance names the fired tiers as done-signal fragments; tiers that don't fire are omitted, not waived.
- Checker: `repro` is answered by red-phase evidence in `log.md`, not by hand-breaking the code.

## Compatibility before implementation

Record the required supported producer/consumer versions and the environments available for
validation before editing. Choose targets from the user/spec or repository contract; don't invent
a wider support promise from the installed runtime. Each claimed target needs its own observed
check or exact externally supplied evidence. Missing required coverage blocks that obligation;
optional targets remain unverified without blocking a narrower authorized scope. Preserve both
results on a discrepancy. Cross-version serializer tests use valid domain strings and the consumer
parser, not assumptions about a library's quoting defaults. An evaluator's later run is separate
coverage and cannot retroactively justify the executor's earlier completion claim.
