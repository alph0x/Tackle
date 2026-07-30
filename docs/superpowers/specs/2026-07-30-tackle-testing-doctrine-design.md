# Design: Tackle testing doctrine (agent-speed TDD)

**Date:** 2026-07-30 · **Status:** approved (design conversation) · **Driver:** user request quoting Uncle Bob: agents write code many times faster than humans; the time saved should be spent on unit, acceptance, property, torture, mutation, and QA testing — the result is both more productive and better.

## Problem

Tackle's testing guidance today is thin:

- `plan.tmpl.md` §6.1: "tests cover the change (test-first **if the project mandates TDD**)" — test-first is opt-in, not doctrine.
- `quality-dimensions.md`: 9 axes, none about **test depth** — property, mutation, fuzz/torture, acceptance are absent as categories.
- `team.tmpl.md` `repro` question ("does the done-signal fail when the behavior is broken?") is a manual germ of mutation testing with no mechanical form.
- No rationale anywhere for *why* an agent-driven initiative should demand more test depth than a human-paced one.

## Rationale (the Bob shift)

Agent speed inverts test economics: code is cheap, verification is where value concentrates. A well-executed point spends most of its effort on test depth, not on writing the code. This must be doctrine, not a per-initiative judgment call.

## Design

### 1. New guide `references/guides/testing.md`

The core artifact. Contents:

1. **Rationale** — the Bob shift, stated in 2–3 sentences, attributed.
2. **Default test-first flow** — for code points, red → green → refactor is the Driver's default shape; opting out requires a `D-xx`. The done-signal is written and **seen failing** before implementation; this mechanically strengthens the checker's `repro` question.
3. **Depth tiers** — each tier folds into the done-signal as a runnable fragment, same convention as the other quality axes:
   - **T0 · unit** — always: tests over the case set, count-asserted.
   - **T1 · acceptance** — fires when the point changes user/API/CLI-visible behavior: test at the public boundary.
   - **T2 · property-based** — fires on parsers, serializers, transforms, money/calculation, round-trips.
   - **T3 · fuzz/torture** — fires on untrusted input, concurrency, state machines.
   - **Mutation** — not a test to write but a validation *of the suite*: fires on high-risk invariants (money, security). The cheap form already exists: break the code, watch the done-signal fail (`repro` made mechanical).

### 2. Hooks (short diff, no doctrine duplication)

- `plan.tmpl.md` §6.1: "test-first if the project mandates TDD" → **"test-first by default for code points; opting out requires a D-xx"**.
- `quality-dimensions.md`: new **Test depth** axis row — Touches heuristic → tier, with per-tier done-signal fragments.
- `testing.md` is referenced from the catalog, the same way the catalog is referenced from templates. `SKILL.md` unchanged (≤1100-word budget intact; no normative content deleted → D-13 gate not triggered).

### 3. Non-goals

- No per-stack tooling presets (no concrete mutation/fuzz tool configs shipped).
- No changes to `SKILL.md` core conventions.
- No new SDD checklist section; the catalog row covers it.

## Validation

Per project profile (behavior over text):

- **Trap eval (small):** an executor briefed with the new §6.1 writes tests before implementation; with the old clause it does not necessarily. One comparative run gates the change.
- **Fixture-test** any done-signal fragment the guide asserts as runnable.

## Execution

Dogfooded via Tackle itself, Lite gate (`/tackle-plan`), per repo convention ("features for the Tackle skill are planned and executed through Tackle itself, even Lite-sized ones"). Deviation from the brainstorming skill's writing-plans terminal step is deliberate: repo convention overrides.
