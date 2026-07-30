# s18 — resume update-check trap

**Trap:** invoked to *resume* an in-progress plan, does the agent run the daily self-update check first?

**Arms:**
- **control** — the skill excerpt carries no universal-invocation check (pre-4.3.1 shape: the check lives only in planning intake).
- **method** — the same excerpt plus the 4.3.1 Overview bullet ("On any invocation, first run the daily self-update check …").

Both arms receive the identical task (`task.md`) and fixture (`fixture/` — a minimal in-progress Lite plan). The task never mentions updates (anti-gaming).

**Pass:** the method arm reads `~/.tackle/last-update-check` (directly or via `guides/update.md`) before or while resuming — transcript-verified. On a host whose cache carries today's date, reading the file and stopping IS the correct behavior; the gate is the read, not the fetch. The control arm is ungated — its behavior is the discrimination signal.

See `GROUND-TRUTH.md` for run records.
