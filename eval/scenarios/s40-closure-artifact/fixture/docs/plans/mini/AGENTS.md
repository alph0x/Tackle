# AGENTS — workspace `docs/plans/mini/`

**Methodology: Tackle 5.5.0**

Conventions for any agent that picks up this plan.

## Context in one line

A one-point initiative whose single point is implemented and awaiting close.

## File map

```
docs/plans/mini/
├── plan.md        ← objective, point decomposition
├── board.md       ← canonical status board
├── log.md         ← append-only session log
├── decisions.md   ← closed decisions register
└── points/        ← point briefings
```

## Rules

1. **State**: `log.md` is append-only; `board.md` is the execution status.
2. **Single source**: questions in `questions.md`; closed decisions in `decisions.md`.
3. **Ground every claim in `file:line`**.
4. **Scope**: don't touch out-of-scope (see `plan.md` §Non-goals).
5. **Verification**: point's done-signal + `plan.md` §6.1. A point flips 🟢 only with its **Evidence** block recorded in `log.md`.

## Autonomy

**Autonomy level: L2 (assisted)** — propose and wait for confirmation before changing code; the human checks Solo points.

## Status / next

See the last entry in `log.md`.
