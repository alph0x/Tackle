# AGENTS — workspace `docs/plans/{slug}/`

**Methodology: Tackle 2.0**

Conventions for any agent (Claude Code, Cursor, GPT, human) that picks up this plan.

## Context in one line

Tackle 2.0 extends Tackle from a planning-only skill into a specification-driven planning + execution workflow that agents run end-to-end inside a repo.

## File map

```
docs/plans/{slug}/
├── README.md      ← index, objective, status, reading order
├── AGENTS.md      ← this file
├── context.md     ← objective, expected result, non-goals, risks
├── contract.md    ← authoritative surface: triggers, states, errors, invariants
├── foundations.md ← grounding: decision → principle → source
├── plan.md        ← point decomposition + acceptance criteria
├── strategy.md    ← waves, quality gates, deferral
├── team.md        ← execution team roles and protocol
├── board.md       ← canonical status board
├── log.md         ← append-only session log (CANONICAL STATE SOURCE)
├── todo.md        ← planning-readiness checklist
├── questions.md   ← open questions (single source)
├── decisions.md   ← closed decisions register
├── reference.md   ← current code state with file:line
├── points/        ← one self-contained .md per point
└── snapshots/     ← read-only external/reference snapshots (optional)
```

## Rules

1. **State**: `log.md` is append-only; `board.md` is execution status. Don't duplicate either elsewhere.
2. **Single source**: questions in `questions.md`; closed decisions in `decisions.md` (`D-id`, append-only, supersede to change).
3. **Ground every claim in `file:line`** verified against the repo.
4. **Scope**: don't touch out-of-scope (see `context.md` §Non-goals).
5. **Verification**: point's done-signal + `plan.md` §4.1. Default loop budget: 3 attempts, then STOP and escalate.
6. **Contract supersede-first** (if `contract.md` exists): implement it as written; deviations become a `D-xx` before the divergent code.
7. **Grounding** (if `foundations.md` exists): new patterns need decision → principle → source before merge.
8. **Quality loop** (multi-agent): a code-quality guardian reviews before a point flips 🟢.
9. **Execution rule**: `/tackle-implement` runs `board.md` in dependency order; only the Coordinator updates board/log, only the Driver writes code.

Full conventions: `SKILL.md` §Core conventions.

## Executor contract (when you work a point)

When you pick up, finish, pause, or abandon a point you MUST:

1. Set its status in `board.md` — vocabulary: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done.
2. Append a `log.md` entry with an updated State snapshot.
3. Record questions answered as `D-xx` in `decisions.md`; mark the `Q-xx` resolved.
4. If code drifted from the point's `file:line` claims, update that point's Context.

## Status / next

See the last entry in `log.md`.
