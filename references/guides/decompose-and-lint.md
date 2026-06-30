# Step 6 — Decompose into loop-runnable points

- Skeleton board first: P-0N / What / Depends-on / Touches / done-signal.
- Then flesh out point briefings.
- Cut for parallelism; minimize dependency depth.
- One point = smallest change with ONE runnable done-signal.

# Step 6.5 — Lint the wired plan

Check:
- Pipeline wired (every `Depends-on` resolves).
- **Grounding gate**: every `file:line` cited in a point's Context was actually read; unread citations are flagged **ungrounded**.
- Contract churn guard (contract sections changed → citing points reconciled).
- Quality dimensions derived into done-signals.
- Deferral & questions sound.
- Q-guard (active point may not depend on unresolved user-owned `Q-xx`).
- Depth artifacts coherent.
- Plan passes the lint.

# Step 6.6 — Right-size the plan

After lint, collapse if the plan is over-decomposed:

- If a point's `Touches` are a subset of another point's and their done-signals run together, merge them.
- If a point is one session, one file, and one runnable command, prefer **Lite** (use `lite-plan.tmpl.md`) and drop the Full ceremony.
- If the initiative has ≤4 points and no multi-track uncertainty, default to Lite unless the user explicitly asked for Full.
