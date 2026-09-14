# Action plan — {{TITLE}}

## 1. Objective

{{The observable result for the user or integrator, including stable requirement ids.}}

## 2. Expected result

- {{observable result and its acceptance evidence}}
- {{integration result and its acceptance evidence}}

### Behavior and outputs

List every stable requirement as a row. The observable and boundary columns are semantic; state
exact bytes, order, paths, stdio, or exits only when required by a consumer. A Point must carry
the behavior behind an id, not merely repeat the id.

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `{{R01}}` | {{...}} | {{...}} | {{...}} | {{...}} |

### Acceptance and test strategy

Map every criterion to a target check, surrounding check, and evidence slot. Include positive and
negative fixtures for each validator boundary and state the plan-only boundary: preparation stops
before source execution and cannot claim product PASS.

| Criterion / obligation | Point | Target check | Surround check | Evidence slot |
|---|---|---|---|---|
| `{{R01}}` | `{{P-01}}` | {{command and pass condition}} | {{command and pass condition}} | `{{...}}` |

## 3. Non-goals

- {{preserved behavior and explicit exclusions}}

## 4. Current state (grounded)

**Key finding (verified):** {{one fact that changes the risk or scope}}.

**Precedent we mirror:** {{local pattern or source with `file:line` citation}}.

{{Relevant current code, inputs, and constraints with anchored citations.}}

## 5. Point decomposition

Each Point is a self-contained worker briefing. The plan compiles shared clauses into Points;
workers do not need to discover obligations by reading this plan or another planning document.

| Point | Responsibility | Traces to | Briefing | Depends on |
|---|---|---|---|---|
| **P-01 · {{...}}** | {{one coherent change}} | `{{spec:NN}}` | `points/P-01-{{slug}}.md` | {{none / artifact}} |

### Dependency graph

```text
{{P-01 ──► P-02 (P-02 consumes the named artifact)}}
{{P-03 (independent)}}
```

Parallelism follows crossing artifacts and Touches; an ordering-only edge is recorded as a
decision rather than disguised as data dependency.

## 6. Readiness and acceptance

### 6.0 Definition of Ready

PLAN sets Ready only after structural checks, semantic counterexample review, two-way coverage,
dependency/interface coherence, relevant positive and negative fixtures, and the relevant
clause/code/config/dependency/input fingerprints pass. Include the reverse-direction scope-drift
list and global obligations here; every global obligation needs an owner, check, and evidence slot.

Record this literal preparation boundary in the report:

`INTENT: PLAN prepares Points and stops before source execution.`

Optional cold probes are risk-triggered and measurable: at most one initial probe plus one
correction recheck. An empty doubts list does not pass a probe whose reconstructed output is wrong.

### 6.1 Universal per-point acceptance

Every Point's own Acceptance names its literal command and case set. This shared bar adds the
integration obligations that apply to every Point:

- [ ] Tests cover the stated normal and boundary cases; the suite and each Point done-signal
      pass with checked native results/exits and any contract-required counts. Test-first is the default for non-trivial code;
      an opt-out is an explicit decision.
- [ ] Contract clauses, interfaces, invariants, and relevant quality constraints are reflected
      in an observable check; equivalent valid implementations remain acceptable.
- [ ] Protected inputs/source and unrelated files remain unchanged; warnings and regressions
      in the touched area are absent.
- [ ] Point dependencies name consumed/produced artifacts; relevant changes invalidate only the
      affected consumers, and the compiler regenerates changed clauses before checks rerun.
- [ ] The board and append-only log are updated by the coordinator after the checker review.

### 6.2 Initiative-level acceptance

- [ ] Integrated flows, final outputs, packaging, and reproducibility pass their declared gates.
- [ ] Every requirement is covered by a Point and every Point has a traceable requirement.

## 7. Risks and dependencies

- {{risk, observable consequence, mitigation, and owner}}

### Rollout and reversibility (only for a shipped path)

{{Document the revert or coexistence procedure, migration/parity check, and enablement default
when a flag exists. For an unflagged Markdown or documentation change, name the bounded revert
procedure and omit invented flag or canary requirements.}}

## 8. Decisions and questions

- {{resolved `D-xx` or user-owned `Q-xx`; unresolved questions defer affected work}}

## 9. Compiler and handoff procedure

1. Resolve the anchors, behavior/output criteria, and requirement ids from the specification and
   named inputs.
2. Compile acceptance/test strategy, contracts/decisions, and each Point with only the shared
   clauses it implements, preserving clause id, revision, and hash plus its interfaces, cases,
   approach, and done-signal.
3. Scaffold inside PLAN using the authorized gitignore decision; there is no second-session wait.
4. Check criterion↔Point coverage in both directions, assign global delivery obligations, and
   inspect crossing artifacts and configuration consumers. Run structural checks and one bounded
   semantic counterexample review. Preparation uses fixture/readiness evidence only; it does not
   execute source or claim product PASS.
5. Record relevant fingerprints and optional risk-triggered probe evidence in the handoff. If a
   contract, code, config, dependency, or input changes, invalidate only affected consumers,
   regenerate changed clauses, re-ground, and rerun their checks.

Workers receive their Point and explicitly named source/input artifacts. Conversation history,
board state, and other plan-local documents support coordination but are not worker prerequisites.
