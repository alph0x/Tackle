# GROUND-TRUTH — s29-trace-untraced-scope

**Do not include this file in the copy given to the agent under test.** It is the answer sheet.

## Task given to the agent

> The workspace `docs/plans/tracecheck/` (a Tackle 5.0.2 plan workspace at `<scratch>/docs/plans/tracecheck/`) has two points on the board: `P-tc-core` (🔴) and `P-tc-report` (🔴). The plan's §5 lists both points; §6 carries two acceptance criteria (6.1 coverage matrix, 6.2 point accounting). `P-tc-core`'s briefing traces to `plan.md §6.1`; **`P-tc-report`'s briefing carries an empty `Traces to: —` line** (the planted drift). The user asks: "run the trace on this plan".

## The trap

The plausible-but-wrong action is reporting a full-coverage matrix — one row per criterion, every row `covered`, no drift flagged — by pairing points to criteria from the plan (§6.1→P-tc-core, §6.2→P-tc-report) **without per-row anchor verification**. `references/guides/trace.md` (the `/tackle-trace` destination guide) requires count-assert both ways: every point id in `plan.md` §5 appears in some row **or is listed under a closing `Scope drift` list**; a **point with no anchor ⇒ scope drift** (HIGH finding, blocking semantics like verify); an orphan criterion (no point) ⇒ `gap`. `P-tc-report` anchors to nothing — it must be flagged as drift by id, and §6.2 consequently shows as a gap. Trace is read-only: it never edits `board.md`, points, or source; the matrix + digest go to `log.md` as the session's evidence block.

## Gate (declared pre-run, host-independent)

- **method arm PASS** iff the trace output (the chat digest and/or the `log.md` evidence block the executor appends) **flags `P-tc-report` as scope drift by id** — the point with the empty `Traces to` is named as drift/unanchored (e.g. under a closing `Scope drift` list), i.e. the matrix is **not** reported as full coverage. (A `gap` row for §6.2 strengthens the pass but is not required; the drift flag on `P-tc-report` is the requirement.)
- **method arm FAIL** iff the output reports a full-coverage matrix — every criterion `covered`, no drift list naming `P-tc-report`, no per-row anchor verification visible.
- **control arm**: ungated — the baseline/discrimination signal.

**Scoring (correct_action):**
- 0 — full-coverage matrix, no drift flag, no anchor verification (trap hit).
- 1 — notes the empty `Traces to` in passing but reports the matrix as fully covered (no drift flag in the matrix/digest).
- 2 — flags `P-tc-report` as scope drift by id (and shows §6.2 as a gap), appends matrix + digest to `log.md` per the guide.

**Anti-gaming:** `task.md` never mentions drift, anchors, coverage, gaps, the matrix, or the trap; the excerpt is the only difference between arms; arms are forbidden from reading other `eval/`/`references/` files (the real guides/templates would leak the matrix format to the control arm).

## Run records

### 2026-08-05 · 1 seed/arm · fresh executor subagents (task tier)

- **control** (raw task, no excerpt): **null — avoided (correct_action 2).** `history://DriverP10.ExecS29Control`. Read the workspace, parsed §6 criteria + each briefing's `Traces to` line itself (no guide), reported the same matrix (6.1 covered / 6.2 gap), named the cause ("P-tc-report briefs `Traces to: —` … nothing guarantees 'every point id listed in §5 appears in the trace output'"), appended its evidence block to `log.md`, ran the exit gate. The empty `Traces to: —` plant was too loud for this tier — both arms caught it. Documented null (s16/s20/s21 precedent): scenario does not discriminate at this tier; stays as a tripwire.
- **method** (5.1.0 excerpt: SKILL.md verbatim + `trace.md` verbatim): **PASS (correct_action 2).** `history://DriverP10.ExecS29Method`. Read workspace, verified anchors with `grep`, appended `log.md` session-2 evidence block: matrix (§6.1 → P-tc-core covered; §6.2 → gap), count-assert "2 criteria == 2 matrix rows ✔", "P-tc-report has no `Traces to` anchor ⇒ **scope drift**", both HIGH, read-only discipline honored (board.md/plan.md/points untouched). Exactly the sealed gate.
- **Verdict:** gate PASSED on the method arm; control null — no discrimination at this tier (tripwire; future-hardening: subtler drift plant, e.g. dangling-but-plausible anchor instead of an empty line). Full record: `eval/runs/2026-08-05-artifact-traps.md`.
