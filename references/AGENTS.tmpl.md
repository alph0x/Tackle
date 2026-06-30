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

1. **State**: `log.md` is append-only; `board.md` is the execution status. Don't duplicate either elsewhere.
2. **Single source**: questions in `questions.md`; closed decisions in `decisions.md` (`D-id`, append-only, supersede to change).
3. **Ground every claim in `file:line`** verified against the repo.
4. **Scope**: don't touch out-of-scope (see `plan.md` §Non-goals).
5. **Verification**: point's done-signal + `plan.md` §6.1. Default loop budget: 3 attempts, then STOP and escalate.
6. **Contract supersede-first** (if `design-contract.md` exists): implement it as written; deviations become a `D-xx` before the divergent code.
7. **Grounding** (if `foundations.md` exists): new patterns need decision → principle → source before merge.
8. **Quality loop** (multi-agent): a code-quality guardian reviews before a point flips 🟢.
9. **Execution rule**: `/tackle-implement` runs `board.md` in dependency order; only the Coordinator updates board/log, only the Driver writes code.

## Harness map

Tackle is harness-agnostic. This workspace records the concrete tools this environment uses to perform generic Tackle operations. Update this section if the tooling changes.

| Generic operation | Harness tool / command in this repo | Notes |
|---|---|---|
| Read code at `file:line` | {{`read`, `cat`, LSP hover, etc.}} | |
| Search code | {{`grep`, `ast_grep`, IDE symbol search, etc.}} | |
| Run tests / done-signal | {{`npm test`, `bun test`, `pytest`, `swift test`, etc.}} | |
| Run lint / typecheck | {{`npm run lint`, `tsc`, `cargo check`, etc.}} | |
| Spawn parallel agents | {{Claude Code multi-agent, `task` subagent, manual fan-out, etc.}} | |
| Git operations | {{`git`, GitHub CLI, IDE git UI, etc.}} | |

If this workspace is shared across agents, fill this map once and never assume a specific IDE, model, or vendor tool.

Full conventions: `SKILL.md` §Core conventions.

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
