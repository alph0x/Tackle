# Step 6 — Decompose into loop-runnable points

- Skeleton board first: P-0N / What / Depends-on / Touches / done-signal.
- Then flesh out point briefings.
- Cut for parallelism; minimize dependency depth.
- One point = smallest change with ONE runnable done-signal.

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
