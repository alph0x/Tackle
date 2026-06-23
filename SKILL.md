---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative that needs a durable action plan broken into self-contained points, before writing implementation code. Also use when resuming, checking status, listing plans, getting the next point, or migrating an old plan.
---

# Tackle

## Overview

Tackle creates a durable action plan under `docs/plans/<initiative>/`, broken into self-contained points that survive handoffs.

- Plans by default; executes only when explicitly asked. `/tackle-plan` stops at handoff; `/tackle-implement` and `/tackle-next` require confirmation unless the user upfront asked for plan+execute.
- Runs inside the target repo; grounds every claim in `file:line`.
- Model-agnostic: `SKILL.md` + `references/`.
- Workspace artifacts are in English.

## Routing

| The user says (any language) | Mode |
|---|---|
| `/tackle-init [preset]` | **Init** → create plan-local `presets/` and `overrides/` |
| `/tackle-constitution` | **Constitution** → write `constitution.md` |
| `/tackle-specify` | **Specify** → write `spec.md` |
| `/tackle-plan` or `tackle this` / `plan de acción` / `armar un plan` / `plan this out` / `iniciativa` | **Plan** → Steps 1–7, then hand off |
| `/tackle-plan` + explicit execute request, or `tackle this and implement it` / `plan de acción y ejecutá` / `do it` | **Plan + Execute** → Steps 1–7, then run execution |
| `/tackle-tasks` | **Tasks** → write `tasks.md` |
| `/tackle-implement` | **Implement** → execute all ready points |
| `/tackle-next` | **Execute next** → execute one ready point |
| `/tackle-checklist` | **Checklist** → write `checklist.md` |
| `resume / retomá <initiative>` | **Resume** → Step 8 |
| `status / seguimiento / cómo viene` | **Status** → Step 9 |
| `what plans are there? / qué planes hay` | **List** → Step 9 |
| `give me the next point / qué sigue` | **Next** → Step 9 |
| `migrate / upgrade / modernizar <initiative>` | **Migrate** → Step 8.5 |
| `improve this plan / tackle-upgrade <initiative>` | **Improve** → Step 10 |

If several initiatives exist under `docs/plans/`, show the List and ask which.

`/tackle-plan` is the standalone default path.

## Template-resolution stack

First match wins:

```
docs/plans/<initiative>/overrides/
  > docs/plans/<initiative>/presets/<preset>/
  > references/sdd/
  > references/
```

In short: **overrides > presets > sdd > core**. Nothing Tackle-related lives at the repo root.

## Execution loop
`/tackle-implement` and `/tackle-next` spawn the point team defined in `team.md` and run `board.md` in dependency order. The Driver executes each point and runs its done-signal; reviewers verify and the Coordinator updates `board.md` + `log.md`. Team size is Solo/Pair/Pod/Squad per `team.md`.

**Execution requires explicit intent.** If the user did **not** upfront ask for plan+execute, `/tackle-implement` and `/tackle-next` must present the point's pre-attack summary and ask for confirmation before changing code. "Yes", "go ahead", or equivalent confirms; silence or ambiguity means stop.


## Optional skills

At the start of planning, check whether these optional companion skills are available:

- `superpowers` — for `brainstorming` and `writing-plans` depth.
- `karpathy-guidelines` — for simplicity-first discipline.
- A `solid-skills` or clean-architecture skill — for architecture / SOLID decisions.

If they are not installed, suggest installing them to the user. If the user agrees, install them. If the user declines, ask what planning-related skills they do have installed, and use any relevant ones. If the user has none and does not want to install any, plan with your own judgment and note the gap once — do not re-nag.

Always use these skills for planning aids only, never for execution.

## Core conventions

1. **Log append-only** — one entry per session; never rewrite history.
2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
3. **Ground every claim in `file:line`** from the repo.
4. **One point = one responsibility + one runnable done-signal**.
5. **Contract supersede-first**: implement `design-contract.md` as written; deviations require a `D-xx` first.
6. **Self-documenting code**: Clean Code + SOLID; no explanatory inline comments.
7. **Status vocabulary**: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done.
8. **Decision ownership** — the user decides every doubt; batch recommendations with defaults.

## Output contract

Open with one status line (`🟢 on track / 🟡 needs your input / 🔴 blocked`). Close with `⚠️ On you: ...` and `▶ Continue: ...`. Digest ≤ 12 lines; handoff ≤ one screen. Don't paste file contents — point to them.

## Where the detail lives

- **Full methodology (per-step guides)**: `references/guides/`
- **Workspace contract**: `references/AGENTS.tmpl.md`
- **Execution teams**: `references/team.tmpl.md`
- **Templates**: `references/*.tmpl.md`, `references/sdd/*.tmpl.md`, `references/presets/<preset>/*.tmpl.md`
