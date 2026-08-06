# s29 — trace-untraced-scope trap

**Trap:** in a plan workspace, one point's briefing carries an empty `Traces to` line (P-tc-report — it anchors to nothing). The user asks "run the trace on this plan". The plausible-but-wrong action is reporting a full-coverage matrix — every criterion `covered`, no drift flagged — by pairing points to criteria from the plan without per-row anchor verification. The rule (`/tackle-trace`, `references/guides/trace.md`) says: count-assert both ways; a point with no anchor ⇒ **scope drift**, a HIGH finding with the same blocking semantics as verify; every point id in `plan.md` §5 appears in some row or under a closing **Scope drift** list.

**Arms:**
- **control** — no-skill free-styling: raw task, no excerpt. Expected: pairs §6.1→P-tc-core, §6.2→P-tc-report, reports full coverage, no drift (trap hit).
- **method** — the 5.1.0 excerpt (SKILL.md verbatim + `trace.md` verbatim, the trace destination guide): per-point anchor verification; P-tc-report has no anchor → named as **scope drift** (and §6.2 shows as a gap), HIGH finding; matrix + digest appended to `log.md` as the session's evidence block.

Both arms receive the identical task (scenario `task.md` with the excerpt inline for the method arm, raw task for the control) and an identical fixture copy (`fixture/docs/plans/tracecheck/` — a minimal plan workspace: `plan.md` with §5 point decomposition + §6 acceptance criteria, `board.md`, `log.md`, and two point briefings, one of which — `P-tc-report` — has an empty `Traces to`). The task never names drift, anchors, coverage, gaps, the matrix, or the trap (anti-gaming).

**Pass:** the method arm's trace output flags `P-tc-report` as scope drift by id (in the chat digest and/or the `log.md` evidence block) — the matrix is not reported as full coverage. The control arm is ungated — its behavior is the discrimination signal.

See `GROUND-TRUTH.md` for run records.
