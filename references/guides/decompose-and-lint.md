# Step 6 — Decompose into loop-runnable points

- Skeleton board first: P-0N / What / Depends-on / Touches / done-signal.
- Then flesh out point briefings.
- Cut for parallelism; minimize dependency depth.
- One point = smallest change with ONE runnable done-signal.

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

Mechanical first: run every row of `guides/lint-spec.md` (copy-paste commands, from the repo root) and report its score line — `lint: N/M checks passed`. Wiring, grounding, statuses, citations, log order, seals, and collisions are all decided there, not re-judged here.

Then judge — the checks no command can decide:
- Contract churn guard (contract sections changed → citing points reconciled).
- Quality dimensions derived into done-signals.
- Reversibility gate: a point whose Touches flag a production path carries the Rollout / reversibility section (revert procedure · flag default-off · no-op-when-off proof); no flagged path ⇒ section omitted, not left empty.
- Deferral & questions sound.
- Q-guard (active point may not depend on unresolved user-owned `Q-xx`).
- Depth artifacts coherent.

# Step 6.6 — Right-size the plan

After lint, collapse if the plan is over-decomposed:

- If a point's `Touches` are a subset of another point's and their done-signals run together, merge them.
- If a point is one session, one file, and one runnable command, prefer **Lite** (use `lite-plan.tmpl.md`) and drop the Full ceremony.
- If the initiative has ≤4 points and no multi-track uncertainty, default to Lite unless the user explicitly asked for Full.
