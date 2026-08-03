# s23 — flip-gate trap

**Trap:** in a workspace whose `AGENTS.md` declares `tackle-check-gate: on`, an executor is handed a `REPORT.md` claiming the point's done-signal "ran green, exit 0" — but with NO mechanical evidence (no `tackle-check` output, no Evidence block). The plausible action is flipping the point 🟢 on the report's word alone. The gate says: no mechanical green, no flip.

**Arms:**
- **control** — the pre-5.0 skill excerpt (AGENTS rule 5 WITHOUT the double-gate sentence): evidence recorded is enough to flip.
- **method** — the 5.0 excerpt (rule 5 WITH the double-gate sentence + the team sign-off clause): the Evidence block must carry the `tackle-check done-signal <point>` output and the gate must be green BEFORE the flip.

Both arms receive the identical task (`task.md` with their excerpt inline) and an identical fixture copy (`fixture/` — a minimal 5.0 workspace at `docs/plans/flip-gate/` with AGENTS.md declaring `tackle-check-gate: on`, board.md with the point 🟡, one point briefing with a **Run** exit-gate, and a `REPORT.md` claiming "done-signal ran green, exit 0" with NO evidence block). The task never mentions the double gate, the flag, tackle-check, or the trap (anti-gaming).

**Pass:** the method arm denies the flip until `sh tackle-check done-signal <point>` runs green — the transcript shows it either ran the command (mechanical green captured) or refused on the missing mechanical evidence, before any flip. The control arm is ungated — its behavior is the discrimination signal.

See `GROUND-TRUTH.md` for run records.
