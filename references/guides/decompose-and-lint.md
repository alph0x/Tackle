# Step 6 — Decompose into loop-runnable points and delivery obligations

- Skeleton board first: P-0N / What / Depends-on / Touches / done-signal.
- Then flesh out point briefings.
- Cut for parallelism using crossing artifacts, interfaces, and configuration consumers; disjoint
  `Touches` alone do not establish semantic independence. Name every produced/consumed artifact
  and relevant invalidation edge.
- One point = smallest coherent vertical slice with ONE runnable done-signal; keep the slice
  vertically complete when splitting it would hide a shared invariant.

The decomposition also assigns global delivery obligations that no single Point can prove, such
as integrated packaging, final source inventory, reproducibility, and release-scope checks. Keep
these obligations in the plan-level acceptance and give each one an owner, check, and evidence
slot. An unowned obligation blocks handoff even when every Point id is present.

## Loop archetypes (Type: discovery / Type: experiment)

**Loop-worthiness test first** — a loop point earns its cost only when ALL four questions hold; otherwise decompose as a standard point:
1. **The task repeats** (or recurs within the initiative) — a one-shot job is one good standard point.
2. **Verification is automated** — a command fails the work without a human in the room.
3. **The budget absorbs the waste** — loops retry and re-read; `Rounds:` caps it.
4. **The agent has real tools** — it can run the thing it changes and see what breaks.

When worthy, pick the archetype:
- **Discovery** (`Type: discovery`) — unknown-size search: bug sweeps, audits. Done-signal = convergence (K consecutive dry rounds, K=2 default; `Rounds:` budget default 5). The point names its dedupe key, and dedupe runs against everything seen, not just confirmed findings.
- **Experiment** (`Type: experiment`) — metric optimization. Done-signal = `Metric:` reaching `Threshold:` via keep/rollback rounds (`Rounds:` default 5). The point names its metric command, and its Touches exclude the metric/evaluator files (the evaluator is untouchable).
- **Both**: budget exhaustion ⇒ ⏸ blocked + escalation packet, never a fake pass; findings that outgrow the point become new points or seeds.

# Step 6.5 — Lint the wired plan

Mechanical first: the agent runs every row of `guides/lint-spec.md` (copy-paste commands, from the repo root), computes the **agent-computed summary** from the observed row results, and reports `lint: N/M checks passed`. Wiring, grounding, statuses, citations, log order, seals, and collisions are all decided there, not re-judged here.

Then judge — the checks no command can decide:
- Contract churn guard (contract sections changed → citing points reconciled).
- Quality dimensions derived into done-signals.
- Reversibility gate: a point whose Touches flag a production path carries a documented rollback or
  coexistence check. Require a flag default-off and no-op proof only when the product contract calls
  for a flag; no flagged path ⇒ section omitted, not left empty.
- Deferral & questions sound.
- Q-guard (active point may not depend on unresolved user-owned `Q-xx`).
- Depth artifacts coherent.

# Step 6.6 — Right-size the plan

After lint, collapse if the plan is over-decomposed:

- If a point's `Touches` are a subset of another point's and their done-signals run together, merge them.
- A one-session, one-product-file correction first checks the bounded **None** route in
  `intake-and-gate.md`; otherwise prefer **Lite** for a small coherent slice and drop Full ceremony.
- If the initiative has ≤4 points and no multi-track uncertainty, default to Lite unless the user explicitly asked for Full.

Right-size before final readiness. If a merge or collapse is made after any provisional readiness
observation, invalidate the affected coverage rows, Point cases, dependencies, fixtures, and
clause/code/config/dependency/input fingerprints. Recompile the affected contracts and run the
readiness validation again before handoff; a stale pre-merge Ready result cannot authorize RUN.

## Step 6.75 — Integrated readiness validation

After right-sizing, PLAN invokes the shared validation contract in `verify.md` in preparation mode.
Run all structural checks, then one bounded semantic counterexample review over the final coverage
matrix, Point cases, dependencies, and global obligations. The review asks which wrong
implementation would pass the stated checks and adds a fixture or observation for each gap; a
keyword or count match is never semantic proof.

Set a Point **Ready** only when all of these are true:

- every criterion has an observable, Point, target check, and evidence slot, and every Point has a
  criterion; unjustified scope is resolved or removed and is listed under scope drift only as a
  blocking finding;
- interfaces and dependency crossings are coherent, including configuration consumers;
- positive and negative validator/contract-boundary fixtures pass with checked native results
  and exits, plus exact counts only where the contract requires them;
- the relevant clause, code, configuration, dependency, and input fingerprints are recorded;
- no material contradiction or unowned global obligation remains.

Preparation records readiness evidence; it does not run source execution or claim product PASS.
Handoff contains the final Ready fingerprints and validated Point contracts. RUN alone may execute
source after explicit execution intent.

## Full execution preparation

Before Ready, choose the bounded capture and closure path in [execution checks](full-checks.md):
actual write boundary, complete input selectors, saved scripts, canonical lint observations and
one obligation index. Reuse these prepared artifacts in RUN while their dependencies remain valid;
this preparation does not claim product validation or replace the semantic readiness gate.

Current Step 6.5 structural observations satisfy the same checks in Step 6.75; verify their revisions and membership instead of executing them twice. Missing or invalidated observations must be obtained before Ready, and the semantic readiness review remains required.
