# Action plan — {{TITLE}}

## 1. Objective

{{The observable result for the user or integrator, including stable requirement ids.}}

## 2. Expected result

- {{observable result and its acceptance evidence}}
- {{integration result and its acceptance evidence}}

### Behavior and outputs

List every stable requirement as a row. The observable and boundary columns are semantic; state
exact bytes, order, paths, stdio, or exits only when required by a consumer. A task must carry
the behavior behind an id, not merely repeat the id.

| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |
|---|---|---|---|---|
| `{{R01}}` | {{...}} | {{...}} | {{...}} | {{...}} |

### Acceptance and test strategy

Map every criterion to a task check, related regression check, and evidence slot. Include positive and
negative fixtures for each validator boundary and state the plan-only boundary: preparation stops
before source execution and cannot claim product PASS.
Choose the check type here before implementation. Prefer one E2E check through the real consumer
as the sole new test when it covers the behavior; complex features need one when feasible. For
isolation, state the uncovered obligation, why E2E cannot observe it, and the identified applicable
failure-mode inventory with expected outcomes. Name the E2E replay artifact destination. Unit tests
may never be planned as post-implementation additions.

| Criterion / obligation | Task | Task check | Related regression check | Evidence slot |
|---|---|---|---|---|
| `{{R01}}` | `{{T-01}}` | {{command and pass condition}} | {{command and pass condition}} | `{{...}}` |

## 3. Non-goals

- {{preserved behavior and explicit exclusions}}

## 4. Current state (grounded)

**Key finding (verified):** {{one fact that changes the risk or scope}}.

**Precedent we mirror:** {{local pattern or source with `file:line` citation}}.

{{Relevant current code, inputs, and constraints with anchored citations.}}

<a id="5-point-decomposition"></a>
<a id="5-task-decomposition"></a>
## 5. Task decomposition

Each task is a self-contained worker briefing. The plan compiles shared clauses into tasks;
workers do not need to discover obligations by reading this plan or another planning document.

| Task | Responsibility | Traces to | Briefing | Depends on |
|---|---|---|---|---|
| **T-01 · {{...}}** | {{one coherent change}} | `{{spec:NN}}` | `tasks/T-01-{{slug}}.md` | {{none / artifact}} |

### Optional milestones

For a long initiative, group tasks by an observable intermediate result only when it helps. Keep
the complete requirement scope, owners, cross-milestone interfaces, decisions, and deliverable
acceptance visible. Prepare executable briefs for the current milestone and the upcoming
dependencies needed for sound decisions; describe later work at outcome/interface level.

| Milestone | Observable result | Requirement owners | Inputs / crossing interfaces | Preparation scope |
|---|---|---|---|---|
| {{M1, or omit this table}} | {{...}} | {{requirement → stable task owner}} | {{artifact and required revision}} | {{prepared tasks / Draft tasks}} |

Task readiness is recorded in each task brief and current execution state on the task board.
Later tasks remain Draft until individually prepared and verified; one Ready milestone does not
make the initiative Ready or Complete. No mandatory requirement may lose its owner because its
details are deferred. Refine when inputs settle or changes invalidate that scope, preserving
identity/lineage, requirement coverage, decisions, and spent correction cycles. Existing PLAN+RUN
authorization continues within its scope; a material product decision follows the decision policy.

### Dependency graph

```text
{{T-01 ──► T-02 (T-02 consumes the named artifact)}}
{{T-03 (independent)}}
```

Parallelism follows crossing artifacts and write scope; an ordering-only edge is recorded as a
decision rather than disguised as data dependency.

## 6. Readiness and acceptance

### 6.0 Definition of Ready

PLAN sets only the prepared tasks Ready to run after structural checks, semantic counterexample review, two-way coverage,
dependency/interface coherence, relevant positive and negative fixtures, and the relevant
clause/code/config/dependency/input fingerprints pass. Include the reverse-direction scope-drift
list and deliverable obligations here; every deliverable obligation needs an owner, check, and evidence slot.

Record this literal preparation boundary in the report:

`INTENT: PLAN prepares tasks and stops before source execution.`

Optional cold probes are risk-triggered and measurable: at most one initial probe plus one
correction recheck. An empty doubts list does not pass a probe whose reconstructed output is wrong.

<a id="61-universal-per-point-acceptance"></a>
<a id="61-universal-per-task-acceptance"></a>
### 6.1 Universal per-task acceptance

Every task's own Acceptance names its literal command and case set. This shared bar adds the
integration obligations that apply to every task:

- [ ] Selected checks cover the stated normal and boundary cases and pass with checked native
      results/exits. Test-first is the default for new checks; an opt-out is an explicit decision.
      Never write a unit test after the behavior it covers. Prefer E2E as the sole new test, require
      it for feasible complex flows, and retain its replayable artifact. Isolated checks need their
      pre-implementation failure-mode inventory and justification.
- [ ] Contract clauses, interfaces, invariants, and relevant quality constraints are reflected
      in an observable check; equivalent valid implementations remain acceptable.
- [ ] Protected inputs/source and unrelated files remain unchanged; warnings and regressions
      in the touched area are absent.
- [ ] Task dependencies name consumed/produced artifacts; relevant changes invalidate only the
      affected consumers, and the compiler regenerates changed clauses before checks rerun.
- [ ] The task board and append-only history are updated by the coordinator after required checks/review; interrupted closure is reconciled with actual output before any side effect is repeated.

### 6.2 Initiative-level acceptance

- [ ] Integrated flows, final outputs, packaging, and reproducibility pass their declared gates.
- [ ] Every requirement is covered by a task and every task has a traceable requirement.

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
2. Compile acceptance/test strategy, contracts/decisions, and each task with only the shared
   clauses it implements, preserving clause id, revision, and hash plus its interfaces, cases,
   approach, and acceptance check.
3. Scaffold inside PLAN using the authorized gitignore decision; there is no second-session wait.
4. Check criterion↔task coverage in both directions, assign deliverable obligations, and
   inspect crossing artifacts and configuration consumers. Run structural checks and one bounded
   semantic counterexample review. Preparation uses fixture/readiness evidence only; it does not
   execute source or claim product PASS.
5. Record relevant fingerprints and optional risk-triggered probe evidence in the handoff. If a
   contract, code, config, dependency, or input changes, invalidate only affected consumers,
   regenerate changed clauses, re-ground, and rerun their checks.

Workers receive their task brief and explicitly named source/input artifacts. Conversation history,
board state, and other plan-local documents support coordination but are not worker prerequisites.

## 10. Working context and maintenance (only when justified)

{{Observed read/rewrite/retained-byte costs; optional milestone/size trigger; authorized history
paths; retained active sessions; segment target; recovery owner. Omit for small work.}}

Use the existing coordinator projection for active work and keep originals in history. Projections
record source membership/revisions and the last fully recorded event; verify before reuse.
Archive original bytes under the recorded policy, preserve lookup and failure lineage, and count
indexing/reconstruction/export costs. Complete required maintenance within the run, before final
acceptance, without starting a new bookkeeping cycle after acceptance.
