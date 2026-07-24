---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative needing a durable action plan of self-contained points, before writing implementation code. Also use when resuming, checking status, listing plans, getting the next point, or migrating an old plan. Also use to verify or red-team a plan before implementation, to judge finished work adversarially, or to run a retro at initiative close.
---

# Tackle

## Overview

**Tackle 4.2.0** — model-agnostic planning and execution methodology: durable plans under `docs/plans/<initiative>/`, self-contained points that survive handoffs.

- Plans by default; executes only when explicitly asked.
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
| `/tackle-verify` | **Verify** → red-team pass over each point before implementation |
| `/tackle-judge` | **Judge** → adversarial verification of finished work |
| `/tackle-judge suite <target>` | **Judge suite** → run the trap suite against a skill, model, or prompt |
| `/tackle-ground` | **Ground** → mechanically read and mark every `file:line` cited in a plan |
| `/tackle-retro` or `retro / retrospectiva / how did it go` | **Retro** → mine `board.md` + `log.md` into `retro.md` at initiative close |
| `/tackle-pulse` or `run a pulse / health check / cómo está todo` | **Pulse** → read-only standing digest (Step 9 guide); scheduler-friendly, never executes points |
| `stop evolving / dejá de evolucionar` (any phrasing) | **Evolution opt-out** → pause or purge the learning-loop profile at `~/.tackle/user-profile.md` or `<repo>/.tackle/profile.md`, per scope |
| `/tackle-drill` or `drill this point` | **Drill** → cold-start readiness drill on one point briefing |
| `/tackle-trace` or `trace coverage` | **Trace** → criterion↔point coverage matrix, gaps and drift |
| `/tackle-handoff` or `prepare a handoff` | **Handoff packet** → generate portable `HANDOFF.md` for the initiative |
| `/tackle-update` | **Update** → self-update |
| `resume / retomá <initiative>` | **Resume** → Step 8 |
| `status / seguimiento / cómo viene` | **Status** → Step 9 |
| `what plans are there? / qué planes hay` | **List** → Step 9 |
| `give me the next point / qué sigue` | **Next** → Step 9 |
| `migrate / upgrade / modernizar <initiative>` | **Migrate** → Step 8.5 |
| `improve this plan / tackle-upgrade <initiative>` | **Improve** → Step 10 |

Several initiatives? Show the List.

**Guide map** (`references/guides/`): Steps 0–2 `intake-and-gate` · 3–4 `scaffold` · 5–5.75 `design-and-contract` · 6–6.6 `decompose-and-lint` (+ `lint-spec`) · 7 `verify` · 7.5 `ground` · 8 `resume` · 8.5 `migrate` · 9 `status-list-next` · 10 `improve`; same-named: `judge` · `retro` · `drill` · `trace` · `handoff-packet` · `update`. SDD templates: `references/sdd/`.

Natural-language triggers are canonical; slash commands are aliases.

**Commands are entry points, not boundaries.** Internal invocation never bypasses guardrails: the ladder gates edits, intent stays explicit, consents and the log/board trail match user-invoked ones.

## Template-resolution stack

```
docs/plans/<initiative>/overrides/
  > docs/plans/<initiative>/presets/<preset>/
  > references/sdd/
  > references/
```

**overrides > presets > sdd > core**, first match wins. Only `.tackle/` (opt-in profiles) lives at repo root.

## Execution loop

`/tackle-implement` and `/tackle-next` spawn the `team.md` point team (mandatory) and run `board.md` in dependency order. Read-first: `board.md`, `log.md`, `decisions.md` (`questions.md` if unresolved) before acting; cold-session modes (`resume`, `status`, list, next, verify, ground, pulse) follow the same rule. Team sizes (Solo/Pair/Pod/Squad) and tier bindings: `references/team.tmpl.md` + `AGENTS.md` §Model map.

- **Maker/checker** — the Driver's done-signal run is informative, not gating; the 🟢 flip requires an independent checker per `team.md`, evidence in `log.md`.
- **Closure report** — Full-gate points close via `reports/P-0N-report.md`; Coordinator sign-off gates the 🟢 flip; the recorded grade is derived from the section-4 evidence block (checker command + output + exit line), never from a declared grade. Reviewers verify; one logical Coordinator updates `board.md` + `log.md`.
- **Regression sweep** — before a 🟢 flip, re-run done-signals of 🟢 points with intersecting Touches; failure reopens them and blocks the flip.
- **Explicit intent** — without an upfront plan+execute ask, present the pre-attack summary and ask before changing code; silence or ambiguity means stop. Default rung L2 (assisted) of the `AGENTS.md` §Autonomy ladder.

Subagents are optional in planning for grounding/verify/drill; intake, doubts, decisions never delegate.

## Companion skills

Step 0 checks optional companions (`superpowers`, `karpathy-guidelines`, `solid-skills`/`clean-architecture`); procedure: `references/guides/intake-and-gate.md`. Never used for execution.

## Core conventions

1. **Log append-only** — one entry per session; never rewrite history.
2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
3. **Ground every claim in `file:line`** — a point is **ungrounded** until every citation is read this session; ungrounded points can't be ready or executed.
4. **One point = one responsibility + one runnable done-signal**.
5. **Contract supersede-first**: implement `design-contract.md` as written; deviations require a `D-xx` first.
6. **Self-documenting code**: Clean Code + SOLID; no explanatory inline comments.
7. **Status vocabulary**: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done · ⚪ skipped.
8. **Decision ownership** — the user decides every doubt; batch recommendations with defaults.
9. **Scaffold asks gitignore** — `/tackle-plan` asks about `.gitignore` for `docs/plans/` before creating files; records the decision.
10. **Harness-agnostic** — works with any agent/LLM and IDE harness; never assume a specific one. Use generic terms ("the agent", "your harness", "the most capable model available"); single-harness features belong outside Tackle.
11. **Authority order** — user > spec > tests > current code, at every gate including None. A check that contradicts the spec is surfaced, never silently satisfied.

## Output contract

Open with one status line (🟢/🟡/🔴); close with `⚠️ On you: ...` and `▶ Continue: ...`. Digest ≤ 12 lines; handoff ≤ one screen. Point to files, don't paste.

## Where the detail lives

- **Full methodology (per-step guides)**: `references/guides/`
- **Workspace contract**: `references/AGENTS.tmpl.md`
- **Execution teams**: `references/team.tmpl.md`
- **Templates**: `references/*.tmpl.md`, `references/sdd/*.tmpl.md` (presets ship empty).
