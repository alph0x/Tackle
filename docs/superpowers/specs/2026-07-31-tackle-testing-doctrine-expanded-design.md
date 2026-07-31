# Design: Tackle testing doctrine — expanded catalog

**Date:** 2026-07-31 · **Status:** expansion of `2026-07-30-tackle-testing-doctrine-design.md` · **Driver:** user request to broaden testing guidance in Tackle, oriented to Uncle Bob's agent-speed TDD philosophy.

## Problem

The approved `2026-07-30-tackle-testing-doctrine-design.md` establishes test-first as the default stance and introduces depth tiers T0–T3 plus mutation validation. It intentionally stays compact. This expansion adds:

1. Explicit coverage of **all six test types** Uncle Bob names: unit, acceptance, property, torture, mutation, and QA.
2. **Concrete, runnable done-signal fragments** agents can copy per type.
3. Clear **heuristics for when each type fires**, so the agent does not over-test trivial points or under-test risky ones.
4. A **QA tier** distinct from acceptance: exploratory, adversarial, human-in-the-loop verification.

Tackle's testing guidance today remains thin outside this expansion path:

- `plan.tmpl.md` §6.1: "tests cover the change (test-first **if the project mandates TDD**)" — opt-in, not doctrine.
- `quality-dimensions.md`: no row about test depth or test-type selection.
- `team.tmpl.md`: the `repro` lens is the germ of mutation testing, but it is not linked to a testing doctrine.
- No rationale anywhere for *why* an agent-driven initiative should demand more test depth than a human-paced one.

## Rationale (the Bob shift)

Agent speed inverts test economics: code is cheap, verification is where value concentrates. A well-executed point spends most of its effort on test depth, not on writing the code. This must be doctrine, not a per-initiative judgment call.

## Design

### 1. New guide `references/guides/testing.md`

The core artifact. Contents:

1. **Rationale** — the Bob shift, 2–3 sentences, attributed.
2. **Default test-first flow** — for code points, red → green → refactor is the Driver's default shape; opting out requires a `D-xx`. The done-signal is written and **seen failing** before implementation; this mechanically strengthens the checker's `repro` question.
3. **Test-type catalog** — six types, each with:
   - What it is (one sentence).
   - When it fires (heuristic).
   - Runnable done-signal fragment example.
   - Agent hint: one line telling the agent what to generate.

#### T0 · Unit tests
- **What:** isolated logic tests, fast, deterministic, no external dependencies.
- **Fires:** every code point by default.
- **Done-signal fragment:** `pytest tests/unit/test_<module>.py -q` or equivalent; every public behavior has at least one count-asserted case; branch coverage ≥ threshold if the project enforces one.
- **Agent hint:** "Write the unit test for `<function>` first; mock only the immediate dependency; assert outputs and edge cases."

#### T1 · Acceptance tests
- **What:** tests at the public boundary (API endpoint, CLI command, UI flow) that express a user-visible requirement.
- **Fires:** when the point changes user/API/CLI-visible behavior.
- **Done-signal fragment:** `pytest tests/acceptance/test_<feature>.py -q` or equivalent; each acceptance criterion from the point briefing maps to one automated test.
- **Agent hint:** "Translate each acceptance criterion from the point briefing into one failing acceptance test before implementing the feature."

#### T2 · Property-based tests
- **What:** tests over invariants using generated inputs (fuzzing with assertions).
- **Fires:** on parsers, serializers, transforms, money/calculation, round-trips, stateless pure functions.
- **Done-signal fragment:** `hypothesis`/`fast-check`/equivalent runs N examples without falsifying the invariant; document the invariant in the test name.
- **Agent hint:** "Identify one invariant of `<function>` and write a property test that generates random valid inputs and asserts the invariant holds."

#### T3 · Torture / fuzz tests
- **What:** tests that feed malformed, extreme, or adversarial inputs to boundaries.
- **Fires:** on untrusted input, concurrency, state machines, parsers, network/file formats.
- **Done-signal fragment:** run a fuzz harness for a bounded number of iterations or a fixed time budget; the SUT must not crash, leak, or corrupt state.
- **Agent hint:** "Generate invalid/malformed inputs for `<boundary>` and assert graceful rejection or bounded resource use."

#### T4 · Mutation tests
- **What:** not a test to write, but a validation *of the suite*: introduce small semantic changes and confirm tests fail.
- **Fires:** on high-risk invariants (money, security, authorization, data integrity).
- **Done-signal fragment:** run mutation tool or manual `repro` lens (see `team.tmpl.md`); mutation score ≥ threshold, or every critical invariant has a test that fails when the code is deliberately broken.
- **Agent hint:** "Break `<critical function>` in one semantically meaningful way and confirm at least one test fails."

#### T5 · QA tests
- **What:** exploratory, adversarial, human-in-the-loop verification that goes beyond automated acceptance. Often: scenario walks, edge-case discovery, usability/consistency checks, and "does this feel right?" judgment.
- **Fires:** when the point touches user-facing behavior, complex workflows, or high-stakes decisions where automated acceptance is necessary but not sufficient.
- **Done-signal fragment:** a `QA.md` or checklist in the point directory, signed off by a human or a frontier-model reviewer, with findings recorded as pass / fix / risk-accepted.
- **Agent hint:** "Draft a QA checklist of at least five adversarial or edge-case scenarios for this change; the human reviewer marks each as observed pass, fixed, or accepted risk."

### 2. Hooks into existing templates (short diff, no doctrine duplication)

- `plan.tmpl.md` §6.1: change "test-first if the project mandates TDD" → **"test-first by default for code points; opting out requires a D-xx"**. Add a cross-reference to `references/guides/testing.md`.
- `quality-dimensions.md`: add a **Test depth** axis row. Touches heuristic → select tier(s), with done-signal fragments drawn from `testing.md`.
- `team.tmpl.md` §Standard lens catalog: update the `repro` lens description to explicitly reference the mutation test step from `testing.md`: "for critical invariants, deliberately break the implementation and confirm the done-signal fails."

### 3. Boundaries and non-goals

- `SKILL.md` remains unchanged: the test-first stance lives in `references/guides/testing.md`, referenced from templates. This preserves the ≤1100-word budget and the 11 core conventions.
- No per-stack tooling presets are shipped (no concrete mutation/fuzz tool configs).
- No new SDD checklist section; the catalog row in `quality-dimensions.md` covers it.
- QA tests are deliberately not fully automatable: the done-signal is a checklist/signon, not a command.

## Validation

Per project profile (behavior over text):

- **Trap eval (small):** an executor briefed with the new §6.1 writes tests before implementation; with the old clause it does not necessarily. One comparative run gates the change.
- **Fixture-test** any done-signal fragment the guide asserts as runnable.

## Execution

Dogfooded via Tackle itself, Lite gate (`/tackle-plan`), per repo convention ("features for the Tackle skill are planned and executed through Tackle itself, even Lite-sized ones"). Deviation from the brainstorming skill's writing-plans terminal step is deliberate: repo convention overrides.
