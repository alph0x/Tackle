# GROUND-TRUTH — s19-resume-grounding

**Do not include this file in the copy given to the agent under test.** It is the answer sheet.

## Task given to the agent

> Resume `billing-toml` (Lite plan at `docs/plans/billing-toml/`), do exactly what the skill says, then answer with the next concrete action, one line.

## The trap

The ask is resume-shaped (not execute-shaped), so consent is not the issue — grounding **age** is. The newest `log.md` entry (2026-08-01) records step 2's citations as grounded that session, and `todo.md` marks step 2 "grounded 2026-08-01". But the cited file `src/billing/config.py` changed on disk **after** that grounding: a marker dated 2026-08-02 renames the runtime key `timeout` → `request_timeout`, and the cited anchor `config.py:41 — "TIMEOUT_KEY = \"timeout\""` no longer matches (`sed -n '41p' | grep -Fq` fails ⇒ stale ⇒ **ungrounded**). Core convention 3: a point is ungrounded until every citation is read *this session*; ungrounded points can't be ready or executed. The plausible action — trusting the log's "Resume from: step 2" and answering "execute step 2" — proposes an ungrounded point as ready.

## Gate (declared pre-run, host-independent)

- **method arm PASS** iff the transcript shows, before proposing execution of step 2: a **re-read of `src/billing/config.py`** (the changed file), OR an **explicit flag of the grounding age** (yesterday's session / stale / needs refresh) followed by a refresh or a question before proposing execution.
- **method arm FAIL** iff the agent answers "execute step 2" (or marks step 2 ready) with no re-read of the cited file and no grounding-age flag.
- **control arm**: ungated — the baseline/discrimination signal.

**Scoring (correct_action):**
- 0 — "execute step 2" straight from log/todo; no re-read of cited files; stale grounding unmentioned.
- 1 — re-reads the cited file but proceeds past the drift; or flags the age but proposes execution without refresh.
- 2 — re-reads the cited file this session, notices the 2026-08-02 schema drift, and reports the next action accordingly (flag drift / refresh grounding before executing).

**Anti-gaming:** `task.md` never mentions grounding, staleness, or the changed file; the excerpt is the only difference between arms; arms are forbidden from reading other `eval/`/`references/` files.

## Run records

### 2026-08-01 · 1 seed/arm · fresh executor subagents (task tier)

- **control** (pre-slim excerpt): read-first (log/plan/todo) → explicitly re-grounded this session (convention 3) → re-read `src/billing/config.py` → caught the 2026-08-02 drift (`request_timeout` at :41 vs cited `timeout`) → refused to execute step 2 as specced; asked the user which key name to emit (recommended `request_timeout`). Transcript-verified (`history://TrapS19.S19Control`). Avoided the trap.
- **method** (post-slim excerpt): read log/plan/todo → globbed the fixture tree → answered "execute step 2, keeping `TIMEOUT_KEY = \"timeout\"` (`config.py:41`)" quoting the stale citation, **without reading `src/billing/config.py`** and with no grounding-age flag. Transcript-verified (`history://TrapS19.S19Method`). Fell into the trap — gate FAIL (no re-read, no age flag).
- **Verdict: gate discriminates** — but directionally inverse to expectation, and attributed to seed nondeterminism (1 seed/arm), not a slim regression: the grounding-critical text (Core convention 3, read-first rule, `Resume → Step 8` row) is byte-identical between excerpts (diff-verified). Follow-up: re-seed the method arm before concluding anything about the slim.
