# Testing doctrine

Agent speed inverts test economics (Uncle Bob): an agent writes code many times faster than a human, so the time saved belongs to verification — unit, acceptance, property, torture, mutation, QA. Code is cheap; verification is where the value concentrates. A well-executed point spends most of its effort on test depth, not on writing code.

## Default: test-first

For code points, red → green → refactor is the Driver's default shape:

1. Write the failing test — **see it fail**.
2. Minimal implementation — see it pass.
3. Refactor with the suite green.

Opting out requires a `D-xx` recorded before implementation. "Seen failing" is the mechanical form of the checker's `repro` question (`team.md`): a test never seen failing proves nothing. The red-phase evidence in `log.md` answers `repro`; the checker does not re-break code by hand.

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

- `plan.md` §6.1: test-first by default for code points; opt-out via `D-xx`.
- Point Acceptance names the fired tiers as done-signal fragments; tiers that don't fire are omitted, not waived.
- Checker: `repro` is answered by red-phase evidence in `log.md`, not by hand-breaking the code.
