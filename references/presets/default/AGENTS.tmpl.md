# AGENTS — workspace `docs/plans/{{slug}}/`

**Methodology: Tackle 2.0** <!-- the Tackle version this workspace was built/migrated under; a future version reads this to decide whether to migrate (Step 8.5 / Step 10). -->

Conventions for any agent (Claude Code, Cursor, GPT, human) that picks up this plan.
<!-- If it inherits from a root AGENTS.md, say so here and don't repeat its rules. -->

## Context in one line

{{What this initiative is, in one sentence.}}

## File map

```
docs/plans/{{slug}}/
├── README.md      ← index, objective, reading order
├── plan.md        ← objective, non-goals, point decomposition, acceptance criteria, risks
├── board.md       ← canonical status board for execution
├── log.md         ← append-only session log (CANONICAL STATE SOURCE)
├── todo.md        ← planning-readiness checklist per point
├── questions.md   ← single source of questions
├── decisions.md   ← closed decisions register (D-01…, single source)
├── reference.md   ← current code state (file:line)
├── points/        ← one self-contained .md per point (goal, approach, prompt, alternatives)
└── AGENTS.md      ← this file
```
<!-- Depth artifacts (list each one you actually created; delete the lines you didn't):
├── foundations.md        ← grounding: decision → principle → source (if new architecture)
├── design-contract.md    ← authoritative API/state/error surface; points implement it (if a shared surface)
├── execution-strategy.md ← waves + quality gate + deferral (if multi-agent / phased execution)
├── team.md               ← execution team roles and protocol (if multi-agent execution)
├── reference-docs/       ← READ-ONLY snapshots of external material + provenance (if the plan depends on anything outside this repo)
├── external-questions/   ← packets sent to other teams (if a question goes external) -->
<!-- Reuse (don't duplicate) shared docs from the root if any. List appendices here. -->

## Rules

1. **Log append-only**: one entry per session, chronological, never rewrite old entries.
2. **Questions only in `questions.md`** (single source). External ones also as a packet in
   `external-questions/` (create the folder only when needed).
   **Closed decisions only in `decisions.md`** (`D-id`, "don't revisit without cause", append-only by
   superseding). A resolved `Q-xx` becomes a `D-xx`; the log links the `D-id`.
3. **Canonical state = last `log.md` entry; execution status = `board.md`.** Don't duplicate either elsewhere.
4. **Ground in code, don't infer.** Every claim about the code carries a `file:line`,
   verified against the repo `{{repo path}}`.
5. **No new files without reason.** If you add one, update `README.md` and this `AGENTS.md`.
6. **Domain invariants / constraints**: consult the authoritative domain source/MCP if your
   environment has one; otherwise use the repo's own canonical constants and annotate it.
7. **Don't touch out-of-scope** (see non-goals in `plan.md`).
8. **Verification = the point's done-signal + `plan.md` §6.1.** Nothing else; no separate
   verification surface. A point is done when its done-signal command passes and §6.1 holds.
   **Loop budget (default): {{N — suggest 3}} attempts, then STOP and escalate** (Decision
   ownership) — a point overrides this only in its own Acceptance.
9. **Contract supersede-first** (if `design-contract.md` exists): implement it as written; a
   genuine deviation supersedes the spec (edit it + add a `D-xx`) BEFORE the divergent code.
10. **Grounding** (if `foundations.md` exists): a new pattern/abstraction does not merge
    without its decision → principle → source row; "it felt cleaner" is not a justification.
11. **Best practices are the backbone**: Clean Code + SOLID. **Self-documenting code** — no
    explanatory inline comments; doc-comments on the public surface only, the *why* in commit
    bodies / these docs. An internal comment is a review finding; its fix is to clarify the
    code, not reword the comment.
12. **Quality loop** (multi-agent execution): a code-quality guardian runs per point
    (smells, redundancy, SOLID, naming) and loops with the implementer until clean before the
    unit is accepted — see `execution-strategy.md` / `team.md`.
13. **Execution rule**: if `/tackle-implement` or `/tackle-next` is running, `board.md` is the
    state machine; only the Coordinator updates it and `log.md`; the Driver writes code;
    reviewers review only.

## Executor contract (when you work a point)

Tackle planned this workspace; execution happens here, in sessions like yours. To keep
tracking alive, when you pick up, finish, pause, or abandon a point you MUST:

1. Set its status in `board.md` — fixed vocabulary: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done.
2. Append a `log.md` entry with an updated State snapshot. Never rewrite old entries.
3. Record questions answered along the way as `D-xx` in `decisions.md`; mark the `Q-xx` resolved.
4. If the code drifted from the point's `file:line` claims, update that point's Context.

A merged PR with a stale status board is a broken handoff — the board is part of the work.

## Status / next

See the last entry in `log.md`.
