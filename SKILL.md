---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative that needs a durable action plan broken into self-contained points, before writing implementation code. Also use when resuming, checking status, listing plans, getting the next point, or migrating an old plan.
---

# Tackle

## Overview

Tackle turns an initiative into a **durable action plan** under `docs/plans/<initiative>/`, broken into self-contained **points** that survive session and agent handoffs.

- **It plans and can execute the plan it produces.** It never writes implementation code on its own.
- **It runs inside the target repo.** Ground every claim in `file:line`.
- **It is model-agnostic.** Follows the Agent Skills format: this `SKILL.md` + `references/`.
- **All workspace artifacts are written in English.**

## Routing

| The user says (any language) | Mode |
|---|---|
| `/tackle-init [preset]` | **Init** → create plan-local `presets/` and `overrides/` |
| `/tackle-constitution` | **Constitution** → write `constitution.md` |
| `/tackle-specify` | **Specify** → write `spec.md` |
| `/tackle-plan` or `tackle this` / `plan de acción` / `armar un plan` / `plan this out` / `iniciativa` | **Plan** → run Steps 1–7 |
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

## SDD phase entry points (optional)

| Phase | Trigger | Output |
|---|---|---|
| Init | `/tackle-init [preset]` | `presets/<preset>/`, `overrides/` |
| Constitution | `/tackle-constitution` | `constitution.md` |
| Specify | `/tackle-specify` | `spec.md` |
| Plan | `/tackle-plan` | Full workspace |
| Tasks | `/tackle-tasks` | `tasks.md` |
| Implement | `/tackle-implement` | Updated `board.md` + `log.md` |
| Execute next | `/tackle-next` | Updated `board.md` + `log.md` |
| Checklist | `/tackle-checklist` | `checklist.md` |

`/tackle-plan` remains the standalone default path.

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

`/tackle-implement` and `/tackle-next` read `board.md`, pick the next ready point in dependency order, run its done-signal, and update `board.md` + `log.md`. Team size is Solo/Pair/Pod/Squad per `team.md`.

## Core conventions

1. **Log append-only** — one entry per session; never rewrite history.
2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
3. **Ground every claim in `file:line`** from the repo.
4. **One point = one responsibility + one runnable done-signal**.
5. **Contract supersede-first** — implement `design-contract.md` as written; deviations require a `D-xx` first.
6. **Self-documenting code** — Clean Code + SOLID; no explanatory inline comments.
7. **Status vocabulary** — 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done.
8. **Decision ownership** — the user decides every doubt; batch recommendations with defaults.

## Output contract

Open every plan response with one status line (`🟢 on track / 🟡 needs your input / 🔴 blocked`). Close with an action footer: `⚠️ On you: ...` and `▶ Continue: ...`. Hard caps: digest ≤ 12 lines; handoff ≤ one screen. Don't paste file contents into chat — point to them.

## Where the detail lives

- **Full methodology (Steps 1–11)**: `references/GUIDE.md`
- **Workspace contract**: `references/AGENTS.tmpl.md`
- **Execution teams**: `references/team.tmpl.md`
- **Templates**: `references/*.tmpl.md`, `references/sdd/*.tmpl.md`, `references/presets/<preset>/*.tmpl.md`
