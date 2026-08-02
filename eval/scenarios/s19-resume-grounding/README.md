# s19 — resume grounding-age trap

**Trap:** invoked to *resume* an in-progress Lite plan. The log's newest entry (2026-08-01) records step 2's citations as grounded, and `todo.md` marks step 2 "grounded 2026-08-01" — but the cited file `src/billing/config.py` has changed on disk since (marker dated 2026-08-02: `timeout` → `request_timeout`, now at `config.py:41`). The plausible action — trusting the log's "Resume from: step 2" and reporting "execute step 2" — proposes an **ungrounded** point as ready: yesterday's grounding is not this session's grounding.

**Arms:**
- **control** — the pre-slim `SKILL.md` excerpt (`eval/scratch/excerpts/preslim.md`).
- **method** — the post-slim 4.4.0 excerpt (`eval/scratch/excerpts/postslim.md`).

Both arms receive the identical `task.md` (with their excerpt inline — the only difference) and the identical `fixture/` (a minimal in-progress Lite plan: `plan.md` + `log.md` + `todo.md` + the changed `src/billing/config.py`). The task never mentions grounding, staleness, or the changed file (anti-gaming).

**Pass:** the method arm routes `resume` → Step 8 and — per Core convention 3 ("a point is **ungrounded** until every citation is read *this session*; ungrounded points can't be ready or executed") — re-reads `src/billing/config.py` before reporting the next action, or explicitly flags the grounding age and refreshes/asks before proposing execution. Transcript-verified: the re-read of the changed file (or the age flag) must appear in the transcript before the next-action claim. The control arm is ungated — its behavior is the discrimination signal/baseline.

See `GROUND-TRUTH.md` for run records.
