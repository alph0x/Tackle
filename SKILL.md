---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative that needs a durable action plan broken into self-contained points, before writing implementation code. Also use when resuming, checking status, listing plans, getting the next point, or migrating an old plan.
---

# Tackle

## Overview

**Tackle 3.2.0** — model-agnostic planning and execution methodology. Tackle creates a durable action plan under `docs/plans/<initiative>/`, broken into self-contained points that survive handoffs.

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
| `resume / retomá <initiative>` | **Resume** → Step 8 |
| `status / seguimiento / cómo viene` | **Status** → Step 9 |
| `what plans are there? / qué planes hay` | **List** → Step 9 |
| `give me the next point / qué sigue` | **Next** → Step 9 |
| `migrate / upgrade / modernizar <initiative>` | **Migrate** → Step 8.5 |
| `improve this plan / tackle-upgrade <initiative>` | **Improve** → Step 10 |

If several initiatives exist under `docs/plans/`, show the List and ask which.

**Guide map** (all under `references/guides/`): Steps 0–2 `intake-and-gate` · 3–4 `scaffold` · 5–5.75 `design-and-contract` · 6–6.6 `decompose-and-lint` (+ `lint-spec`) · 7 `verify` · 7.5 `ground` · 8 `resume` · 8.5 `migrate` · 9 `status-list-next` · 10 `improve`; same-named guides: `judge` · `retro` · `drill` · `trace` · `handoff-packet`. SDD phase templates live in `references/sdd/`.

Natural-language triggers are canonical; slash commands are aliases for harnesses that support them. `/tackle-plan` (or `tackle this`) is the standalone default path.

**Commands are entry points, not boundaries.** Tackle may invoke any of its modes and subagents internally, at will, whenever the flow benefits — planning may run grounding, lint, verify, drill, or trace mid-flow; execution may re-ground a point or re-run the regression sweep. Guardrails are never bypassed by going internal: the autonomy ladder still gates anything that edits source, execution intent stays explicit, writes still require the same consents as if the user had invoked the command, and internal invocations leave the same log/board trail as user-invoked ones.

## Template-resolution stack

First match wins:

```
docs/plans/<initiative>/overrides/
  > docs/plans/<initiative>/presets/<preset>/
  > references/sdd/
  > references/
```

In short: **overrides > presets > sdd > core**. Nothing Tackle-related lives at the repo root, except `.tackle/` (opt-in learning-loop profiles).

## Execution loop
`/tackle-implement` and `/tackle-next` spawn the point team defined in `team.md` and run `board.md` in dependency order. Before acting, the agent MUST read `board.md`, `log.md`, and `decisions.md` (and `questions.md` if any question is unresolved). The Driver executes each point and runs its done-signal; that run is informative, not gating. The 🟢-flipping run comes from an independent checker (maker/checker) per `team.md`, with its evidence recorded in `log.md`. Reviewers verify and the Coordinator updates `board.md` + `log.md`. Team size is Solo/Pair/Pod/Squad per `team.md`.

In execution, spawning the `team.md` point team is **mandatory**. In planning, subagents are **optional, recommended** for grounding reads, the `/tackle-verify` red-team, and the `/tackle-drill` cold-start drill; intake, doubts, and decisions never delegate to a subagent.

**Regression sweep.** Before a point flips 🟢, re-run the done-signals of every 🟢 point whose Touches intersect the current point's Touches. Any failure reopens that point (🟢 → 🟡) and blocks the current one.

Cold-session modes (`resume`, `status`, `what plans are there?`, `give me the next point`, `/tackle-verify`, `/tackle-ground`, `/tackle-pulse`) follow the same rule: read the state files first, then answer or act.

**Execution requires explicit intent.** If the user did **not** upfront ask for plan+execute, `/tackle-implement` and `/tackle-next` must present the point's pre-attack summary and ask for confirmation before changing code. "Yes", "go ahead", or equivalent confirms; silence or ambiguity means stop. This rule is L2 (assisted), the default rung of the autonomy ladder declared in the workspace `AGENTS.md` §Autonomy (per-point overrides in the point briefing). L1 (report) is read-only and never edits source; L3 (unattended) skips per-point confirmation only when the workspace's `AGENTS.md` §Autonomy conditions all hold — never on production-path points without an explicit waiver.


## Companion skills

Planning Step 0 checks three optional companions — `superpowers`, `karpathy-guidelines`, and a `solid-skills`/`clean-architecture` skill — and records the result in the log (procedure: `references/guides/intake-and-gate.md` Step 0). Companions improve planning; they are **never** used for execution.

## Core conventions

1. **Log append-only** — one entry per session; never rewrite history.
2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
3. **Ground every claim in `file:line`** from the repo. A point is **ungrounded** until every cited `file:line` has been read in the current session; ungrounded points cannot be marked ready or executed.
4. **One point = one responsibility + one runnable done-signal**.
5. **Contract supersede-first**: implement `design-contract.md` as written; deviations require a `D-xx` first.
6. **Self-documenting code**: Clean Code + SOLID; no explanatory inline comments.
7. **Status vocabulary**: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done.
8. **Decision ownership** — the user decides every doubt; batch recommendations with defaults.
9. **Scaffold asks gitignore** — `/tackle-plan` must ask whether to add `docs/plans/` to `.gitignore` before creating files, and record the decision in `log.md` / `decisions.md`. Do not silently default.
10. **Harness-agnostic** — Tackle works with any agent/LLM and any IDE harness. Never assume Claude, Anthropic, Cursor, Codex, or a specific model. Use generic terms: "the agent", "the orchestrator", "your harness", "the most capable model available". Any feature that only works on one harness belongs outside Tackle.

## Output contract

Open with one status line (`🟢 on track / 🟡 needs your input / 🔴 blocked`). Close with `⚠️ On you: ...` and `▶ Continue: ...`. Digest ≤ 12 lines; handoff ≤ one screen. Don't paste file contents — point to them.

## Where the detail lives

- **Full methodology (per-step guides)**: `references/guides/`
- **Workspace contract**: `references/AGENTS.tmpl.md`
- **Execution teams**: `references/team.tmpl.md`
- **Templates**: `references/*.tmpl.md`, `references/sdd/*.tmpl.md`; presets ship empty (see Template-resolution stack).
