# Step 7 — Verify (red-team pass)

Triggered by `/tackle-verify`. Run this after the plan is decomposed and linted, before `/tackle-implement` or `/tackle-next`.

**Principle: detection before judgment.** Use cheap mechanical checks (`grep`, `read`, `ast-grep`, `git`) first; use the LLM only for synthesis of the findings. This keeps the pass fast and reduces false positives.

For each point in `plan.md` §5 / `board.md`:

1. **Grounding check** — confirm every cited `file:line` was actually read; flag ungrounded assertions.
2. **Claim counter** — for every factual claim ("always", "never", "only", "all", "none"), check the repo mechanically. Flag unsupported absolutes.
3. **Scope minimality / source anchor** — confirm the point traces to a line in the spec/ticket/constitution; flag untraced scope as drift.
4. **Done-signal honesty** — confirm the done-signal is a literal runnable command with an explicit pass condition (exit code / count / grep match); flag `test -f`, "document exists", or prose gates.
5. **Dependency sanity** — confirm `Depends-on` resolves to an actual point and is not aspirational; confirm parallel points have disjoint `Touches`.
6. **Plan-vs-code drift** — compare the point's claimed `Touches` and Goal against the current repo; flag if the code already implements it (stale point) or if the described change does not match any touched file.
7. **Agnosticism / Harness-agnostic check** — confirm the plan remains harness-agnostic: no harness-specific commands (e.g. `/command`, `@mention`, `.claude/`), no model brand names (e.g. `Claude`, `GPT`, `Opus`), and no vendor-specific file paths unless the point is explicitly about that harness. Flag violations as drift.
8. **Seal integrity** — mechanical: every `SEALED: D-xx` id found in the workspace greps in `decisions.md` (a missing id is a HIGH finding); a sealed section edited with no superseding `SEALED: D-yy supersedes D-xx` marker is a HIGH finding.
9. **Regression sweep computability** — confirm the point declares `Touches` precisely enough that the sweep set (🟢 points with intersecting Touches) is derivable mechanically (grep over `board.md` + `points/`); flag missing or vague `Touches`.

Classify every finding with a certainty level:

- **HIGH** — mechanically confirmed (file missing, citation unread, command not runnable). Safe to block on.
  - Examples: a cited **file does not exist** (e.g. `src/foo.ts:42`); the done-signal command returns exit code 1; `Depends-on: P-99` references a non-existent point.
- **MEDIUM** — likely true, needs one extra check before blocking.
  - Examples: the point claims "X never happens" but a grep finds one counter-example; the `Touches` list omits a file the Goal clearly modifies.
- **LOW** — possible, needs human judgment.
  - Examples: a variable name feels inconsistent with project convention; a prose description could be read two ways but the code is probably correct.

Use these examples to calibrate: if you are not sure whether a finding is HIGH, downgrade it. If you cannot reproduce it mechanically, it is not HIGH.

Output: append findings to `log.md`; update `board.md` to mark verified points. Any HIGH finding, or an ungrounded point, blocks execution until fixed or explicitly waived by the user. MEDIUM findings block unless the user explicitly accepts the risk; LOW findings are advisory.
