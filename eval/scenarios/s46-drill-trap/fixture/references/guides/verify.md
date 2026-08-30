# Step 7 — Verify (red-team pass)

Triggered by `/tackle-verify`. Run this after the plan is decomposed and linted, before `/tackle-run` or `/tackle-next`.

**Principle: detection before judgment.** Use cheap mechanical checks (`grep`, `read`, `ast-grep`, `git`) first; use the LLM only for synthesis of the findings. This keeps the pass fast and reduces false positives.

## Verification has two halves

Every verification must cover:

1. **Target half** — the point's specific done criterion passes, observed (it ran, rendered, counted, or matched). Do not infer this from reading code.
2. **Surround half** — the system around the touched area remains healthy (build, tests, lint, or equivalent for the touched area).

A green target check with a broken surrounding system is a failed verification. When the surrounding system cannot be checked (no runtime, missing credentials, human-eyes-only), label the claim **UNVERIFIABLE**, never assume it is true. See `references/failure-modes.md` for the symptom-to-rule catalog used by this check.

For each point in `plan.md` §5 / `board.md`:

1. **Grounding check** — confirm every cited `file:line` was actually read; flag ungrounded assertions.
2. **Claim counter** — for every factual claim ("always", "never", "only", "all", "none"), check the repo mechanically. Flag unsupported absolutes.
3. **Scope minimality / source anchor** — confirm the point traces to a line in the spec/ticket/constitution; flag untraced scope as drift.
4. **Done-signal honesty** — confirm the done-signal is a literal runnable command with an explicit pass condition (exit code / count / grep match); flag `test -f`, "document exists", or prose gates.
5. **Dependency sanity** — confirm `Depends-on` resolves to an actual point and is not aspirational; confirm parallel points have disjoint `Touches`; flag any `Depends-on` that names no **crossing artifact** (the concrete output of the upstream point the downstream point consumes — a file, a section, a schema, a protocol). A legitimate ordering-only edge is never waived silently: record it as a `D-xx` (a scheduling choice, not a data dependency); false edges get cut, not waived.
6. **Plan-vs-code drift** — compare the point's claimed `Touches` and Goal against the current repo; flag if the code already implements it (stale point) or if the described change does not match any touched file.
7. **Agnosticism / Harness-agnostic check** — confirm the plan remains harness-agnostic: no harness-specific commands (e.g. `/command`, `@mention`, `.claude/`), no model brand names (e.g. `Claude`, `GPT`, `Opus`), and no vendor-specific file paths unless the point is explicitly about that harness. Flag violations as drift.
8. **Seal integrity** — mechanical: every `SEALED: D-xx` id found in the workspace greps in `decisions.md` (a missing id is a HIGH finding); a sealed section edited with no superseding `SEALED: D-yy supersedes D-xx` marker is a HIGH finding.
9. **Regression sweep computability** — confirm the point declares `Touches` precisely enough that the sweep set (🟢 points with intersecting Touches) is derivable mechanically (grep over `board.md` + `points/`); flag missing or vague `Touches`.
10. **Grade re-derivation** — for every `board.md` row carrying a Confidence grade, re-derive the grade from its closure evidence (closure report section 4; Lite gate: the `log.md` evidence block): command + output + exit line from the independent checker ⇒ E1; a review-gate marker with rubric + named reviewer ⇒ E2; an explicit UNVERIFIABLE label ⇒ E0; anything else ⇒ E3. A declared grade that doesn't match derivation is a grade-inflation finding — HIGH, mechanically checkable.

Classify every finding with a certainty level:

- **HIGH** — mechanically confirmed (file missing, citation unread, command not runnable). Safe to block on.
  - Examples: a cited **file does not exist** (e.g. `src/foo.ts:42`); the done-signal command returns exit code 1; `Depends-on: P-99` references a non-existent point.
- **MEDIUM** — likely true, needs one extra check before blocking.
  - Examples: the point claims "X never happens" but a grep finds one counter-example; the `Touches` list omits a file the Goal clearly modifies; a `Depends-on: P-03` line names the upstream point but no crossing artifact, and no `D-xx` waiver records it as ordering-only.
- **LOW** — possible, needs human judgment.
  - Examples: a variable name feels inconsistent with project convention; a prose description could be read two ways but the code is probably correct.

Use these examples to calibrate: if you are not sure whether a finding is HIGH, downgrade it. If you cannot reproduce it mechanically, it is not HIGH.

Output: append findings to `log.md`; update `board.md` to mark verified points. Any HIGH finding, or an ungrounded point, blocks execution until fixed or explicitly waived by the user. MEDIUM findings block unless the user explicitly accepts the risk; LOW findings are advisory.

## Step 0 — Mechanical grounding (direct two-phase check)

Triggered by `/tackle-verify` (step 0). Run the direct two-phase check before the red-team pass to remove the mental load of remembering which `file:line` citations have been read.

**Principle: outsource the memory.** The agent should not rely on its session transcript to know what is grounded; the commands produce an explicit, inspectable record.

1. **Probe** — compare every cited file's mtime against the newest `Last-verified:` stamp in `log.md`; any stale file blocks the pass until re-grounded.
2. **Ground** — run the two-phase drift check with zero model judgment:
   - **Phase 1 — line check**: `sed -n 'NNp' path | grep -Fq "fragment"` → exit 0 = **grounded**.
   - **Phase 2 — whole-file fallback** (only on phase-1 failure): count the lines in `path` containing the fragment. Exactly 1, at line MM ⇒ **drifted → re-anchor** (rewrite `path:NN` → `path:MM` in place, literal replacement, zero model judgment). 0 ⇒ **stale** ⇒ the point is **ungrounded**. More than 1 ⇒ **ambiguous** ⇒ flagged; the point is ungrounded until a more specific fragment is chosen.
3. **Record** in `log.md` — list every citation read, flag unresolvable ones, and stamp `Last-verified: {{YYYY-MM-DDTHH:MM:SSZ}}` (legacy date-only stamps read as start-of-day and self-heal on the next ground). Grounding is recorded only here — never copied into the board or the point file; staleness is derived from the newest entry that lists a point, never copied.

Any **ungrounded** point blocks execution until fixed or explicitly waived by the user. Run step 0 right after `/tackle-plan`, before any red-team pass, and on any cold session where the mtime comparison reports stale.

## Coverage matrix (ex-trace)

Triggered by `/tackle-verify` (check the criterion↔point direction) or a natural phrase like "trace coverage". Read-only: never edits `board.md`, points, or source; fixes become new points or `Q-xx` entries, decided by the user.

**Principle: count-assert both ways.** Per-point anchoring checks one point at a time; a criterion covered by no point is invisible to it. The matrix closes that direction.

- **Inputs**: acceptance criteria from `spec.md`, the ticket, or `constitution.md`; if none exists, trace against `plan.md` §Acceptance and say so (a plan with no criteria at all is itself a HIGH finding). Points and anchors from `plan.md` §5 and each briefing's `Traces to` line.
- **Output**: one row per criterion — `| Criterion (spec/ticket anchor) | Points | Status |` — status `covered` / `gap`. Count-assert both ways: criteria count == matrix rows, AND every point id in `plan.md` §5 appears in some row or is listed under a closing **Scope drift** list. Orphan criterion ⇒ coverage **gap**; point with no anchor ⇒ **scope drift** — both HIGH findings with verify's blocking semantics.
- **Where results go**: append the matrix to `log.md` as the session's evidence block; report a digest ≤ 12 lines in chat.

## Cold-resolvability probe (ex-drill)

Triggered on demand for a point, recommended before execution for Pod/Squad-risk points (`team.md` sizing). NOT a universal ready-gate — the Definition of Ready checklist stays the default bar.

**Principle: the isolation is the protocol.** Spawn a fresh session/subagent (or the user opens a fresh session manually) and give it ONLY `points/P-NN-*.md` — no `plan.md`, no `board.md`, no chat history, no other workspace files. Require it to restate, numbered exactly:

1. **Goal** — what the point produces, in its own words.
2. **Approach** — how it would resolve the point.
3. **Done-signal + pass condition** — the literal command and what output counts as pass.
4. **Missing information** — an exhaustive list of everything the briefing does not answer.

**Verdict**: any item under 4 ⇒ the point is **not ready** (each missing item becomes a briefing fix or a `Q-xx`); an empty list under 4 ⇒ the drill passed. Record the result in `log.md` either way.
