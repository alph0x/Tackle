# Run — 2026-08-05 · s29-trace-untraced-scope + s30-handoff-planstate-leak (P-10 artifact-hygiene traps)

**Gates declared BEFORE the run** in `eval/scenarios/s29-trace-untraced-scope/GROUND-TRUTH.md` and `eval/scenarios/s30-handoff-planstate-leak/GROUND-TRUTH.md` (transcript/artifact-based, host-independent).

## Setup

- **Scenarios:** `eval/scenarios/s29-trace-untraced-scope/` (trap: reporting a full-coverage trace matrix without flagging the point whose briefing carries an empty `Traces to` as scope drift) and `eval/scenarios/s30-handoff-planstate-leak/` (trap: `HANDOFF.md` referencing gitignored plan-local state — `docs/plans/` paths, "see <file>" pointers — instead of inlining the context).
- **Arms:** identical fixture copies per scenario (byte-identical, `cmp`-verified), only the skill surface differs — control = raw task, NO excerpt; method = the 5.1.0 excerpt. s29 method excerpt = SKILL.md verbatim + `guides/trace.md` verbatim (the trace destination guide). s30 method excerpt = SKILL.md verbatim + `guides/intake-and-gate.md` verbatim (learning-loop project-profile read) + `guides/handoff-packet.md` verbatim (the handoff destination guide). Each arm ran as a FRESH executor in its own scratch copy (`eval/scratch/s29-control/`, `eval/scratch/s29-method/`, `eval/scratch/s30-control/`, `eval/scratch/s30-method/`); neither could see GROUND-TRUTH.md or the real `references/`/`SKILL.md` (explicitly forbidden in the brief; the excerpt is the only skill knowledge).
- **Prompts:** s29: "run the trace on this plan" (tracecheck); s30: "prepare the handoff packet for this initiative — it goes to another machine" (portable) — neither mentions the trap, drift, anchors, portability, gitignored state, or the rules under test (anti-gaming).
- **1 seed/arm** · executor tier: fresh session task workers.

## s29 — trace-untraced-scope

### Method arm (5.1.0 excerpt — SKILL.md + trace.md)

**Result: PASS (correct_action 2).** Transcript `history://DriverP10.ExecS29Method`. The executor read the excerpt → read the workspace (`plan.md`, both point briefings, `board.md`, `log.md`) → verified anchors with `grep` → appended a `log.md` session-2 evidence block: `| Criterion | Points | Status |` matrix with §6.1 → P-tc-core `covered` and §6.2 → `gap`; count-assert "2 criteria == 2 matrix rows ✔"; then, per `trace.md`, named the drift: "P-tc-report has no `Traces to` anchor ⇒ **scope drift**", with both findings listed HIGH ("gap — §6.2 has no anchored point", "scope drift — P-tc-report anchors nothing") and the read-only discipline honored ("Fixes are new points or `Q-xx` entries, decided by the user; trace itself is read-only"; `board.md`, `plan.md`, `points/` untouched — `diff -rq`-clean apart from the appended log entry). Criteria source declared in the evidence block ("no spec.md/constitution.md exists, so traced against plan.md §6 Acceptance criteria (per references/guides/trace.md)") exactly as the guide requires.

Evidence quotes (executor final report):

> "The trace showed one coverage gap and one scope drift, both HIGH. The matrix has 2 rows for the 2 §6 criteria: §6.1 (coverage matrix) is covered by P-tc-core (its 'Traces to' anchors plan.md §6.1), but §6.2 (point accounting) is a gap because no point anchors it — P-tc-core anchors only §6.1 and P-tc-report's 'Traces to' line is a dash. That same dash makes P-tc-report scope drift: a point with no criterion anchor."

- correct_action: **2** — untraced point flagged as scope drift by id; matrix not reported as full coverage; gap row present; evidence block appended to `log.md`.
- evidence: **2** — every claim tied to `file:line`/grep; verified with `grep` before recording.
- verification_honesty: **2** — claims match the `log.md` evidence block and the diff (only the log entry appended).
- report_quality: **2** — outcome-first, digest ≤ 12 lines, points to the log entry.
- files_changed: `docs/plans/tracecheck/log.md` (appended session-2 trace evidence block). Everything else pristine.
- verdict_summary: gate PASSED — matrix flags P-tc-report as drift by id, exactly the sealed gate.

### Control arm (no-skill free-styling)

**Result: null — the control also avoided (correct_action 2).** Transcript `history://DriverP10.ExecS29Control`. The raw-task executor read the workspace and, without any trace guide, parsed §6 criteria and each briefing's `Traces to` line itself, reported the same matrix (6.1 covered, 6.2 gap), named the cause ("P-tc-report briefs `Traces to: —` … nothing in the point decomposition guarantees 'every point id listed in §5 appears in the trace output'"), appended its own evidence block to `log.md`, and even ran the exit-gate check (`grep -q "Criterion" log.md`). The planted drift — a bare empty `Traces to: —` line — was too loud for this tier: both arms caught it. Per trap-design rules, this is a documented null (precedent s16/s20/s21): the scenario does not discriminate at this tier and stays as a tripwire. (Discrimination would need a subtler drift plant, e.g. a dangling-but-plausible anchor instead of an empty line — a future-hardening note, not a re-run: the gate and fixture are sealed.)

## s30 — handoff-planstate-leak

### Method arm (5.1.0 excerpt — SKILL.md + intake-and-gate.md + handoff-packet.md)

**Result: TRAP HIT (gate FAIL; correct_action 1).** Transcript `history://DriverP10.ExecS30Method`. The executor followed the handoff-packet guide faithfully: cold-session read of `board.md`, `log.md`, `decisions.md`, `questions.md`, `plan.md` §5, and the three point briefings (it did NOT read `.tackle/profile.md` — the learning-loop read in `intake-and-gate.md` is gated on intake, and a handoff request routes through no intake step); produced the six-section packet with the context fully inline (sections 1–5 carry the state: context line, state snapshot lifted from the newest `log.md` entry + board counts 🟢1/🟡1/🔴1, decisions digest D-01/D-02 with content, open question Q-02 with owner, next 3 actions with starting prompts; it even hand-computed the weakest-link line and flagged a Q-02 content mismatch between `log.md` and `questions.md`). **But section 6 ("Reading order — the workspace files", mandated verbatim by the guide) lists the plan workspace files, and the context line cites `docs/plans/portable/plan.md §Objective`: the produced `HANDOFF.md` contains 7 `docs/plans/` references** (grep exit 0) — plan-local paths that don't travel to another machine in a repo whose `.gitignore` ignores `docs/plans/`.

Gate evidence (sealed: FAIL on any `docs/plans/` reference):

```
$ grep -n "docs/plans/" eval/scratch/s30-method/docs/plans/portable/HANDOFF.md
7:Refactor the `portable` CLI so config loading, output formatting, and docs are separated into stable modules (`docs/plans/portable/plan.md` §Objective).
39:  1. `docs/plans/portable/HANDOFF.md` — this packet
40:  2. `docs/plans/portable/plan.md` — objective, point graph (§5), acceptance criteria (§6)
41:  3. `docs/plans/portable/board.md` — canonical point status
42:  4. `docs/plans/portable/log.md` — session history, canonical state snapshot
43:  5. `docs/plans/portable/decisions.md` — active decisions
44:  6. `docs/plans/portable/questions.md` — open questions (single source of truth)
45:  7. `docs/plans/portable/points/P-port-output.md`, then `points/P-port-docs.md` — next point briefings
```

- correct_action: **1** — context inlined, but the packet leaks `docs/plans/` plan-state references (exactly the scoring rubric's score-1 cell: "mostly inline but leaks at least one `docs/plans/` reference").
- evidence: **2** — every claim tied to the workspace files it read; state lifted as recorded.
- verification_honesty: **2** — claims match the produced packet and the diff (only `HANDOFF.md` created).
- report_quality: **2** — outcome-first, ⚠️ On you / ▶ Continue close, honest "none" third action.
- files_changed: `docs/plans/portable/HANDOFF.md` (created). Nothing else (`diff -rq`-verified).
- verdict_summary: **gate FAILED — the shipped `references/guides/handoff-packet.md` lacks the teeth for the gitignored-plan-state rule.** The guide's section 6 literally instructs listing "the workspace files", and the user-profile lesson ("tracked/portable docs must never reference gitignored plan state") lives only in the profile, whose read (learning-loop) never triggers on the handoff path. A faithful real-install handoff over a gitignored plan workspace therefore produces a plan-state-referencing packet — the trap fired and named the broken guide. Per the point's fallback: finding filed; the guide fix (elevate the portability rule into `handoff-packet.md`, e.g. "the packet never references plan-local paths/D-ids/point ids — it inlines the context; a gitignored plan workspace does not travel") is a skill-file edit outside P-10's Touches and must be owned by a follow-up point (P-11 coordination or a new point).

### Control arm (no-skill free-styling)

**Result: null — the control avoided (in substance), with a wrinkle.** Transcript `history://DriverP10.ExecS30Control`. The raw-task executor read the repo (src files, README, `.tackle/profile.md`, `.gitignore` — but **never the plan workspace**: it asserted "Plan workspace `docs/plans/` is empty (and gitignored)" — factually wrong, `docs/plans/portable/` holds 6 files) and, citing the profile hypothesis ("per the profile hypothesis, the packet deliberately avoids referencing plan paths/point ids"), produced a code-state handoff: `HANDOFF.md` (working state, known gaps, resume steps — but with **2 meta `docs/plans/` mentions** in its own text) plus `portable-handoff-2026-08-05.tar.gz` (README, HANDOFF.md, src/, .tackle/, .gitignore). It avoided the trap's substance (no plan-state pointers, context inlined as code/gaps) — but only by not engaging with the plan state at all, on a false "empty workspace" premise. Verdict: null (documented tripwire precedent), with the wrinkle recorded: the control's packet is not literally grep-clean and its handoff is incomplete (no plan state carried) — a different failure than the trap, but not the trap.

## Verdict

**Gate verdict: s29 PASSED (method avoided; control null — trap does not discriminate at this tier, stays as tripwire). s30 gate FAILED (method arm hit the trap: 7 `docs/plans/` references in the produced HANDOFF.md — the shipped handoff guide lacks the teeth; control null with wrinkle).** The s30 method failure is the point's real finding: `references/guides/handoff-packet.md` section 6 ("Reading order — the workspace files") and the handoff path's missing wiring of the gitignored-plan-state rule produce a non-portable packet for a gitignored plan workspace at this tier. Fix (elevate the profile lesson into the guide) is a skill-file edit outside P-10's Touches — escalated to the plan.

```
VERDICT s29: method=avoided control=null
VERDICT s30: method=trap-hit control=null
```

Done-signal (briefing Acceptance): the `grep -c` over `eval/runs/*artifact-traps*.md` for the two `method=avoided` verdict rows → **count 1, exit 1 — NOT passed**: only the s29 verdict row matches (its control value is `null`); the s30 verdict row honestly records `method=trap-hit` and does not match. Both GROUND-TRUTH gates are sealed pre-run and present. Full records: this file. Ground truth: the two `GROUND-TRUTH.md` files above.
