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

Classify every finding with a certainty level:

- **HIGH** — mechanically confirmed (file missing, citation unread, command not runnable). Safe to block on.
- **MEDIUM** — likely true, needs one extra check before blocking.
- **LOW** — possible, needs human judgment.

Output: append findings to `log.md`; update `board.md` to mark verified points. Any HIGH finding, or an ungrounded point, blocks execution until fixed or explicitly waived by the user. MEDIUM findings block unless the user explicitly accepts the risk; LOW findings are advisory.
