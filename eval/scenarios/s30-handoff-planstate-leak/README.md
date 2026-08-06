# s30 — handoff-planstate-leak trap

**Trap:** an initiative's plan state lives in gitignored `docs/plans/portable/` (`.gitignore` ignores `docs/plans/`). The user asks to "prepare the handoff packet for this initiative — it goes to another machine". The plausible-but-wrong action is a `HANDOFF.md` that references plan-local state which doesn't travel — `docs/plans/portable/board.md` / `log.md` / `decisions.md` paths, plan-local D-ids without their content, "see points/…" pointers — instead of inlining the needed context. The rules: `/tackle-handoff` (`references/guides/handoff-packet.md`) produces a **portable single file** "for a session or person that has nothing else" (a read-only projection of `board.md` + `log.md`, never a pointer set); and the user-profile lesson (4✓/0✗): **tracked/portable docs must never reference gitignored plan state (plan paths, point ids, plan-local decisions)** — the packet inlines the context instead.

**Arms:**
- **control** — no-skill free-styling: raw task, no excerpt. Expected: writes a `HANDOFF.md` that points at the plan workspace ("Reading order: `docs/plans/portable/board.md`, …", "see `decisions.md`") — plan-state references that don't travel (trap hit).
- **method** — the 5.1.0 excerpt (SKILL.md verbatim + `intake-and-gate.md` verbatim — the learning-loop project-profile read — + `handoff-packet.md` verbatim, the handoff destination guide): reads the cold-session state files and the project profile (`.tackle/profile.md`, which carries the portable-docs lesson), and produces a self-contained six-section `HANDOFF.md` with the context inlined and zero `docs/plans/` references.

Both arms receive the identical task (scenario `task.md` with the excerpt inline for the method arm, raw task for the control) and an identical fixture copy (`fixture/` — a repo whose `.gitignore` ignores `docs/plans/`, with `.tackle/profile.md` carrying the portable-docs hypothesis, and `docs/plans/portable/` holding `plan.md`, `board.md` (P-port-config 🟢, P-port-output 🟡, P-port-docs 🔴), `log.md` (newest entry with Did/Decisions/Blockers/Next), `decisions.md` (D-01, D-02), `questions.md` (Q-02 open), and three point briefings). The task never names portable, self-contained, gitignored, `docs/plans/`, paths, or the trap (anti-gaming).

**Pass:** the produced `HANDOFF.md` greps clean for `docs/plans/` and carries the context inline (state snapshot, decisions, questions, next actions present in the packet — not pointers). The control arm is ungated — its behavior is the discrimination signal.

See `GROUND-TRUTH.md` for run records.
