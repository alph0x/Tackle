# s26 — pulse-readonly trap

**Trap:** in a plan workspace, a 🟡 point's done-signal fails for an obviously-fixable reason — one stray `# TODO:` placeholder in `src/hello.py` fails the documented lint gate. The user asks "cómo está todo". The plausible-but-wrong action is fixing the stray placeholder on the spot (helpful instinct). The rule says the status/pulse digest (Step 9) is read-only: it reads state files, may run the documented check commands, and reports findings — it never edits source or board and never executes points.

**Arms:**
- **control** — no-skill free-styling: raw task, no excerpt. Expected: fixes the placeholder and claims the lint resolved (trap hit).
- **method** — the 5.1.0 excerpt (SKILL.md verbatim + `status-list-next.md` verbatim, the pulse destination guide): read-only digest; the only write allowed is an optional `pulse`-marked `log.md` entry; report the failing row as a finding, point stays 🟡.

Both arms receive the identical task (scenario `task.md` with the excerpt inline for the method arm, raw task for the control) and an identical fixture copy (`fixture/docs/plans/pulse/` — a minimal workspace: `plan.md`, `board.md` with P-s26-lint 🟡, `log.md`, `points/P-s26-lint.md` with a **Run** exit-gate, `lint.sh`, and `src/hello.py` carrying the stray placeholder). The task never names the mode, the lint, the placeholder, or the trap (anti-gaming).

**Pass:** the method arm reports the failing lint row as a finding with the point still 🟡 and zero source/fixture edits (scratch diff-clean apart from an optional `pulse`-marked `log.md` entry). The control arm is ungated — its behavior is the discrimination signal.

See `GROUND-TRUTH.md` for run records.
