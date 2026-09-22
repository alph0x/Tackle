<a id="step-6--decompose-into-loop-runnable-points-and-delivery-obligations"></a>
# Step 6 — Decompose into executable tasks and delivery obligations

- Skeleton board first: P-0N / What / Depends-on / Write scope / acceptance check.
- Then compile sufficient task briefs for the selected readiness scope.
- Cut for parallelism using crossing artifacts, interfaces, and configuration consumers; disjoint
  `Write scope` (legacy `Touches`) alone do not establish semantic independence. Name every produced/consumed artifact
  and relevant invalidation edge.
- One task = smallest coherent vertical slice with ONE runnable acceptance check; keep the slice
  vertically complete when splitting it would hide a shared invariant.

The decomposition also assigns global delivery obligations that no single Task can prove, such
as integrated packaging, final source inventory, reproducibility, and release-scope checks. Keep
these obligations in the plan-level acceptance and give each one an owner, check, and evidence
slot. An unowned obligation blocks handoff even when every Task id is present.

<a id="loop-archetypes-type-discovery--type-experiment"></a>
## Loop reference plans (Type: discovery / Type: experiment)

**Loop-worthiness test first** — a loop task earns its cost only when ALL four questions hold; otherwise decompose as a standard task:
1. **The task repeats** (or recurs within the initiative) — a one-shot job is one good standard task.
2. **Verification is automated** — a command fails the work without a human in the room.
3. **The budget absorbs the waste** — loops retry and re-read; `Rounds:` caps it.
4. **The agent has real tools** — it can run the thing it changes and see what breaks.

When worthy, pick the reference plan:
- **Discovery** (`Type: discovery`) — unknown-size search: bug sweeps, audits. Acceptance check = convergence (K consecutive dry rounds, K=2 default; `Rounds:` budget default 5). The task names its dedupe key, and dedupe runs against everything seen, not just confirmed findings.
- **Experiment** (`Type: experiment`) — metric optimization. Acceptance check = `Metric:` reaching `Threshold:` via keep/rollback rounds (`Rounds:` default 5). The task names its metric command, and its Write scope exclude the metric/evaluator files (the evaluator is untouchable).
- **Both**: budget exhaustion ⇒ ⏸ blocked + escalation packet, never a fake pass; findings that outgrow the task become new tasks or seeds.

# Step 6.5 — Lint the wired plan

Mechanical first: the agent runs every row of `guides/lint-spec.md` (copy-paste commands, from the repo root), computes the **agent-computed summary** from the observed row results, and reports `lint: N/M checks passed`. Wiring, grounding, statuses, citations, log order, seals, and collisions are all decided there, not re-judged here.

Then judge — the checks no command can decide:
- Contract churn guard (contract sections changed → citing tasks reconciled).
- Quality dimensions derived into acceptance checks.
- Reversibility gate: a task whose Write scope flag a production path carries a documented rollback or
  coexistence check. Require a flag default-off and no-op proof only when the product contract calls
  for a flag; no flagged path ⇒ section omitted, not left empty.
- Deferral & questions sound.
- Q-guard (an active task may not depend on an unresolved material product decision or required
  missing information in `Q-xx`; optional questions and delegated technical choices do not block it).
- Depth artifacts coherent.

# Step 6.6 — Right-size the plan

After lint, collapse if the plan is over-decomposed:

- If a task's `Write scope` (legacy `Touches`) are a subset of another task's and their acceptance checks run together, merge them.
- Re-apply the **risk precedence** from `intake-and-gate.md` before right-sizing: a public API,
  multi-module change, multi-session/team work, or expected handoff stays **Full** even when
  Tasks are merged into a small count. Only an actually removed trigger permits re-sizing.
- If no Full trigger applies, a one-session, one-product-file correction first checks the bounded
  **None** route; otherwise prefer **Lite** for a small coherent slice and drop Full ceremony.
- If the initiative has ≤4 Tasks and no multi-track uncertainty, default to Lite only after the
  risk check and unless the user explicitly asked for Full.

Right-size before final readiness. If a merge or collapse is made after any provisional readiness
observation, invalidate the affected coverage rows, Task cases, dependencies, fixtures, and
clause/code/config/dependency/input fingerprints. Recompile the affected contracts and run the
readiness validation again before handoff; a stale pre-merge Ready result cannot authorize RUN.

## Step 6.75 — Integrated readiness validation

After right-sizing, PLAN invokes the shared validation contract in `verify.md` in preparation mode.
Run all structural checks, then one bounded semantic counterexample review over the final coverage
matrix, Task cases, dependencies, and global obligations. The review asks which wrong
implementation would pass the stated checks and adds a fixture or observation for each gap; a
keyword or count match is never semantic proof.

Set a selected prepared task **Ready to run** only when all of these are true:

- every selected criterion has its required behavior, observable, task case, task check and verification-record slot, and every task has a criterion; all later criteria retain Draft owners, outcomes/interfaces and a named future check obligation; unjustified scope is resolved or removed and is listed under scope drift only as a
  blocking finding;
- interfaces and dependency crossings are coherent, including configuration consumers;
- positive and negative validator/contract-boundary fixtures pass with checked native results
  and exits, plus exact counts only where the contract requires them;
- the relevant clause, code, configuration, dependency, and input fingerprints are recorded;
- no material contradiction or unowned global obligation remains.

Preparation records readiness evidence; it does not run source execution or claim product PASS.
Handoff contains the final Ready fingerprints and validated Task contracts. RUN alone may execute
source after explicit execution intent.

## Preparation horizon

Long initiatives may use optional milestones in the existing plan/team structures. Keep the full objective, requirement map, dependencies, pending decisions and deliverable acceptance visible. Prepare current work and critical upcoming interfaces; leave distant work Draft until its inputs settle. Refinement preserves stable task IDs or explicit split/merge/supersession lineage and spent correction cycles. A milestone is not another universal checkpoint. Small work keeps its existing simple path. Readiness records explicitly name the selected tasks; “ready” never describes deferred work. Prior scoped PLAN+RUN permission continues when the next milestone becomes ready.

Resolve uncertain capabilities or interfaces with one bounded, authorized probe when its result changes implementation; compile that fact into the consumer. Routine edits do not need a research task.

## Full execution preparation

Before Ready, choose the bounded capture and closure path in [execution checks](full-checks.md):
actual write boundary, complete input selectors, saved scripts, canonical lint observations and
one obligation index. Reuse these prepared artifacts in RUN while their dependencies remain valid;
this preparation does not claim product validation or replace the semantic readiness gate.

Current Step 6.5 structural observations satisfy the same checks in Step 6.75; verify their revisions and membership instead of executing them twice. Missing or invalidated observations must be obtained before Ready, and the semantic readiness review remains required.

## Optional task consistency recipe

For a nontrivial graph, an existing planner may save this standard-library recipe locally and
pass its compiled task data. It checks identities, full scope ownership, selected readiness and
producer/consumer compatibility. It does not infer product requirements, evaluate semantic
correctness, execute tasks or replace reference verification. `available` contains observed
producer artifacts, not planned promises; each entry has its observed interface and revision.
The caller records fingerprints of the actual named inputs before using the result. `contract`,
`source`, `configuration`, `dependencies` and `runtime` are nonempty textual hashes/revisions or
explicit not-applicable reasons. `selectors` is a nonempty list/map describing selector membership;
an explicitly optional selector may have an empty match list. Empty top-level metadata is missing. No installed tool or additional file is required for small work.

```python
import hashlib
import json
import re


def task_fields(text):
    aliases = {'Touches': 'Write scope', 'Done-signal': 'Acceptance check',
               'Run': 'Acceptance check', 'Target check': 'Task check',
               'Surround check': 'Related regression check'}
    fields = {}
    for line in text.splitlines():
        match = re.fullmatch(r'\s*(?:-\s*)?\*\*([^*:]+)(?:\*\*\s*:|:\*\*)\s*(.*?)\s*', line)
        if not match:
            continue
        key = aliases.get(match[1], match[1])
        if key in fields and fields[key] != match[2]:
            raise ValueError('conflicting field aliases: ' + key)
        fields[key] = match[2]
    return fields


def prepare_tasks(requirements, tasks, selected, available, fingerprints, delivery):
    identities = [task['id'] for task in tasks]
    if len(set(identities)) != len(identities) or not identities:
        raise ValueError('duplicate or empty task identities')
    if any(not re.fullmatch(r'P-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*', identity) for identity in identities):
        raise ValueError('invalid stable task identity')
    by_id = dict(zip(identities, tasks))
    if len(requirements) != len(set(requirements)) or not requirements:
        raise ValueError('duplicate or missing requirements')
    if not selected or len(selected) != len(set(selected)) or set(selected) - by_id.keys():
        raise ValueError('invalid readiness scope')
    owners = {requirement: [] for requirement in requirements}
    for task in tasks:
        if not task.get('requirements') or not task.get('outcome'):
            raise ValueError('task lacks required outcome or scope')
        for requirement in task['requirements']:
            if requirement not in owners:
                raise ValueError('unjustified task scope')
            owners[requirement].append(task['id'])
        for dependency in task.get('consumes', []):
            producer = by_id.get(dependency['task'])
            if producer is None:
                raise ValueError('missing dependency identity')
            output = producer.get('produces', {}).get(dependency['artifact'])
            expected = {'interface': dependency['interface'], 'revision': dependency['revision']}
            if output != expected:
                raise ValueError('incompatible declared producer/consumer')
    if any(not names for names in owners.values()):
        raise ValueError('unowned requirement')
    if not delivery or any(not row.get(k) for row in delivery for k in ('owner', 'check', 'record')):
        raise ValueError('unowned deliverable obligation')
    visiting, visited = set(), set()
    def visit(identity):
        if identity in visiting:
            raise ValueError('cyclic dependency')
        if identity in visited:
            return
        visiting.add(identity)
        for dependency in by_id[identity].get('consumes', []):
            visit(dependency['task'])
        visiting.remove(identity)
        visited.add(identity)
    for identity in identities:
        visit(identity)
    required_inputs = {'contract', 'source', 'configuration', 'dependencies', 'selectors', 'runtime'}
    if not required_inputs.issubset(fingerprints):
        raise ValueError('missing relevant fingerprint')
    for key in required_inputs - {'selectors'}:
        if not isinstance(fingerprints[key], str) or not fingerprints[key].strip():
            raise ValueError('missing relevant fingerprint: ' + key)
    if not isinstance(fingerprints['selectors'], (dict, list)) or not fingerprints['selectors']:
        raise ValueError('missing selector membership fingerprint')
    states, findings = {}, {}
    for identity, task in by_id.items():
        states[identity] = 'Draft'
        if identity not in selected:
            if not task.get('milestone') or not task.get('future_check'):
                raise ValueError('deferred scope lacks milestone/check owner')
            continue
        gaps = []
        for key in ('write_scope', 'inputs', 'acceptance_check', 'regression_check', 'record'):
            if not task.get(key):
                gaps.append('missing ' + key)
        for requirement in task['requirements']:
            cases = [case for case in task.get('cases', []) if case.get('requirement') == requirement]
            if not cases or any(k not in case for case in cases for k in ('input', 'expected', 'check')) or any(not case['check'] for case in cases):
                gaps.append('missing observable case: ' + requirement)
        if task.get('pending_product_decisions'):
            gaps.append('material decision unresolved')
        if task.get('semantic_review') != 'passed' or task.get('boundary_fixtures') != 'passed':
            gaps.append('readiness observations unavailable')
        for dependency in task.get('consumes', []):
            key = dependency['task'] + '/' + dependency['artifact']
            expected = {'interface': dependency['interface'], 'revision': dependency['revision']}
            if available.get(key) != expected:
                gaps.append('missing or stale dependency output: ' + key)
        findings[identity] = gaps
        if not gaps:
            states[identity] = 'Ready to run'
    revision = hashlib.sha256(json.dumps(
        [requirements, tasks, selected, available, fingerprints, delivery],
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'states': states, 'findings': findings, 'owners': owners,
            'revision': revision, 'execution_authorized': False, 'product_pass': False}
```

The recipe's structural pass is one preparation observation. `semantic_review` and
`boundary_fixtures` name results whose actual accessible records the coordinator must inspect;
a caller setting those strings does not establish either result. An omitted behavior hidden
behind a requirement ID still fails the required semantic counterexample review.
