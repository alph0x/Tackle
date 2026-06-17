# Step 6 — Decompose into loop-runnable points

- Skeleton board first: P-0N / What / Depends-on / Touches / done-signal.
- Then flesh out point briefings.
- Cut for parallelism; minimize dependency depth.
- One point = smallest change with ONE runnable done-signal.

# Step 6.5 — Lint the wired plan

Check:
- Pipeline wired (every `Depends-on` resolves).
- Contract churn guard (contract sections changed → citing points reconciled).
- Quality dimensions derived into done-signals.
- Deferral & questions sound.
- Q-guard (active point may not depend on unresolved user-owned `Q-xx`).
- Depth artifacts coherent.
- Plan passes the lint.
