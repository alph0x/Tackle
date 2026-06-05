# AGENTS — workspace `docs/plans/{{slug}}/`

Conventions for any agent (Claude Code, Cursor, GPT, human) that picks up this plan.
<!-- If it inherits from a root AGENTS.md, say so here and don't repeat its rules. -->

## Context in one line

{{What this initiative is, in one sentence.}}

## File map

```
docs/plans/{{slug}}/
├── README.md      ← index, objective, tickets
├── plan.md        ← objective, non-goals, point decomposition, acceptance criteria, risks
├── log.md         ← append-only session log (CANONICAL STATE SOURCE)
├── todo.md        ← planning-readiness checklist per point
├── questions.md   ← single source of questions
├── decisions.md   ← closed decisions register (D-01…, single source)
├── reference.md   ← current code state (file:line)
├── points/        ← one self-contained .md per point (goal, approach, prompt, alternatives)
└── AGENTS.md      ← this file
```
<!-- Reuse (don't duplicate) shared docs from the root if any. List appendices here. -->

## Rules

1. **Log append-only**: one entry per session, chronological, never rewrite old entries.
2. **Questions only in `questions.md`** (single source). External ones also as a packet in
   `external-questions/` (create the folder only when needed).
   **Closed decisions only in `decisions.md`** (`D-id`, "don't revisit without cause", append-only by
   superseding). A resolved `Q-xx` becomes a `D-xx`; the log links the `D-id`.
3. **Canonical state = last log entry; per-point execution status = `plan.md` §5.** Don't duplicate either elsewhere.
4. **Ground in code, don't infer.** Every claim about the code carries a `file:line`,
   verified against the repo `{{repo path}}`.
5. **No new files without reason.** If you add one, update `README.md` and this `AGENTS.md`.
6. **Domain invariants / constraints**: consult the authoritative domain source/MCP if your
   environment has one; otherwise use the repo's own canonical constants and annotate it.
7. **Don't touch out-of-scope** (see non-goals in `plan.md`).
8. **Verification**: per-module tests + local mock when applicable. No-regression mandatory
   on shared code.

## Executor contract (when you work a point)

Tackle planned this workspace; execution happens here, in sessions like yours. To keep
tracking alive, when you pick up, finish, pause, or abandon a point you MUST:

1. Set its status in `plan.md` §5 — fixed vocabulary: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done.
2. Append a `log.md` entry with an updated State snapshot. Never rewrite old entries.
3. Record questions answered along the way as `D-xx` in `decisions.md`; mark the `Q-xx` resolved.
4. If the code drifted from the point's `file:line` claims, update that point's Context.

A merged PR with a stale status board is a broken handoff — the board is part of the work.

## Status / next

See the last entry in `log.md`.
