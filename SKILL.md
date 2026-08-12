---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative needing a durable action plan of self-contained points, before writing implementation code. Also use when resuming, checking status, listing plans, getting the next point, or migrating an old plan. Also use to verify or red-team a plan before implementation, to judge finished work adversarially, or to run a retro at initiative close.
---

# Tackle

## Overview

**Tackle 5.2.0** — model-agnostic planning/execution methodology: durable plans under `docs/plans/<initiative>/`, self-contained points that survive handoffs; runs in the target repo, grounds every claim in `file:line`.

- On any invocation, first run the daily self-update check (`references/guides/update.md` Check phase; cache-gated, non-blocking).
- Plans by default; executes only when explicitly asked.
- Workspace artifacts are in English.

## Routing

| The user says (any language) | Mode |
|---|---|
| `/tackle-init [preset]` | **Init** → plan-local `presets/` + `overrides/` |
| `/tackle-constitution` | **Constitution** → `constitution.md` |
| `/tackle-specify` | **Specify** → `spec.md` |
| `/tackle-plan` | **Plan** → Steps 1–7, then hand off |
| `/tackle-plan` + explicit execute | **Plan + Execute** → Steps 1–7, then run execution |
| `/tackle-tasks` | **Tasks** → `tasks.md` |
| `/tackle-implement` | **Implement** → all ready points |
| `/tackle-next` | **Execute next** → one ready point |
| `/tackle-checklist` | **Checklist** → `checklist.md` |
| `/tackle-verify` | **Verify** → red-team points pre-implementation |
| `/tackle-judge` | **Judge** → adversarial check of finished work |
| `/tackle-judge suite <target>` | **Judge suite** → trap suite vs skill/model/prompt |
| `/tackle-ground` | **Ground** → mechanically mark cited `file:line`s |
| `/tackle-retro` | **Retro** → mine `board.md` + `log.md` into `retro.md` |
| `/tackle-pulse` | **Pulse** → read-only digest (Step 9); never executes points |
| `stop evolving` | **Evolution opt-out** → pause/purge learning-loop profile, per scope |
| `/tackle-drill` | **Drill** → cold-start drill on one point briefing |
| `/tackle-trace` | **Trace** → criterion↔point coverage matrix, gaps, drift |
| `/tackle-handoff` | **Handoff packet** → portable `HANDOFF.md` (`guides/handoff-packet.md`) |
| `/tackle-update` | **Update** → self-update |
| `resume <initiative>` | **Resume** → Step 8 |
| `status <initiative>` | **Status** → Step 9 |
| `what plans are there?` | **List** → Step 9 |
| `give me the next point` | **Next** → Step 9 |
| `migrate <initiative>` | **Migrate** → Step 8.5 |
| `improve this plan` | **Improve** → Step 10 |

**Guide map** (`references/guides/`): 0–2 `intake-and-gate` · 3–4 `scaffold` · 5–5.75 `design-and-contract` · 6–6.6 `decompose-and-lint` · 7 `verify` · 7.5 `ground` · 8 `resume` · 8.5 `migrate` · 9 `status-list-next` · 10 `improve`; SDD: `references/sdd/`.

Natural-language triggers are canonical; slash commands are aliases.

**Commands are entry points, not boundaries** — internal invocation never bypasses guardrails (`intake-and-gate.md`).

## Template-resolution stack

`overrides/ > presets/<preset>/ > sdd/ > references/`, first match wins; only `.tackle/` lives at repo root.

## Execution loop

`/tackle-implement` and `/tackle-next` spawn the `team.md` point team (mandatory) and run `board.md` in dependency order. Read-first: `board.md`, `log.md`, `decisions.md` (`questions.md` if unresolved) before acting; cold-session modes (`resume`, `status`, list, next, verify, ground, pulse) follow the same rule. Team sizes/tiers/efforts: `team.tmpl.md` + `AGENTS.md` §Model map.

- **Maker/checker** — Driver's run informative, not gating; flip needs an independent checker (`team.tmpl.md` §Done-conditions).
- **Closure report** — Full-gate closes via `reports/P-0N-report.md`; Coordinator sign-off gates the flip; grade from section-4 evidence (`team.tmpl.md` §Closure report).
- **Regression sweep** — re-run done-signals of 🟢 points with intersecting Touches before a flip; failure reopens and blocks (`team.tmpl.md` step 9).
- **Explicit intent** — no upfront plan+execute ask → pre-attack summary + ask before changing code; silence/ambiguity means stop; default L2 (`AGENTS.md` §Autonomy).
- **Usage ledger** — every role run appends one `usage.md` row (model, tier, effort, tokens as the harness exposes them; `n/a`, never estimated); retro mines it for cost; recording is informative, never gating.

Subagents are optional in planning for grounding/verify/drill; intake, doubts, decisions never delegate.

Planning is self-contained: intake, simplicity, and architecture guidance live in `references/guides/` and the templates — no external planning skills required.

## Core conventions

1. **Log append-only** — one entry per session; never rewrite history.
2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
3. **Ground every claim in `file:line`** — a point is **ungrounded** until every citation passes the drift check (with re-anchor) recorded by the newest ground entry in `log.md`; ungrounded points can't be ready or executed.
4. **One point = one responsibility + one runnable done-signal**.
5. **Contract supersede-first**: implement `design-contract.md` as written; deviations require a `D-xx` first.
6. **Self-documenting code**: Clean Code + SOLID; no explanatory inline comments.
7. **Status vocabulary**: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done · ⚪ skipped.
8. **Decision ownership** — the user decides every doubt; batch recommendations with defaults.
9. **Scaffold asks gitignore** — `/tackle-plan` asks about `.gitignore` for `docs/plans/` before creating files; records the decision.
10. **Harness-agnostic** — works with any agent/LLM and IDE harness; never assume a specific one. Use generic terms ("the agent", "your harness", "the most capable model available"); single-harness features belong outside Tackle.
11. **Authority order** — user > spec > tests > current code, at every gate including None. A check that contradicts the spec is surfaced, never silently satisfied.

## Output contract

Open with one status line; close with `⚠️ On you: ...` and `▶ Continue: ...`. Digest ≤ 12 lines; handoff ≤ one screen. Point to files, don't paste.
Terse by default; say it fully for security warnings, irreversible actions, or anywhere compression risks misread.

## Where the detail lives

`references/guides/` (per-step guides) · `AGENTS.tmpl.md` (workspace contract) · `team.tmpl.md` (teams) · `*.tmpl.md` + `sdd/` (templates).
