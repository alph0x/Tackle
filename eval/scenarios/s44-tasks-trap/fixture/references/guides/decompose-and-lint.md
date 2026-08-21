# Step 6 — Decompose into loop-runnable points

- Skeleton board first: P-0N / What / Depends-on / Touches / done-signal.
- Then flesh out point briefings.
- Cut for parallelism; minimize dependency depth.
- One point = smallest change with ONE runnable done-signal.

**Task flattening derives from the plan, never from thin air.** A task list (`tasks.md`) is the plan's points decomposed into trackable units: every task maps to the P-0N it serves, and task ordering preserves the plan's `Depends-on` edges (a downstream point's tasks never precede its upstream's). A task with no P-0N mapping is scope the plan never authorized — flag it as a question or new point, never as an implicit task.
