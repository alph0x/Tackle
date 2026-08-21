---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative needing a durable action plan of self-contained points, before writing implementation code. Also use when resuming, checking status, listing plans, getting the next point, or migrating an old plan. Also use to verify or red-team a plan before implementation, to judge finished work adversarially, or to run a retro at initiative close.
---

# Tackle

## Overview

**Tackle 5.5.0** — model-agnostic planning/execution methodology: durable plans under `docs/plans/<initiative>/`, self-contained points that survive handoffs; runs in the target repo, grounds every claim in `file:line`.

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

Natural-language triggers are canonical; slash commands are aliases.

## Learning intake

If `.tackle/profile.md` or `~/.tackle/user-profile.md` exists, read the active hypotheses before proposing defaults (tag proposals `(from your profile)`). If the host repo has `docs/seeds/`, check it for pending items when planning. Write paths are exclusive: profiles only via `/tackle-retro`; seeds deliberately, never silently. Mid-session, before performing an action a directive scopes to (`applies_to: <action>`), re-read the matching directives and apply them to that action — intake-time application does not cover actions taken deep in a long session.

## Execution loop

`/tackle-implement` and `/tackle-next` spawn the `team.md` point team (mandatory) and run `board.md` in dependency order. Read-first: `board.md`, `log.md`, `decisions.md` (`questions.md` if unresolved) before acting.

- **Maker/checker** — Driver's run informative, not gating; flip needs an independent checker (`team.tmpl.md` §Done-conditions).
- **Closure report** — Full-gate closes via `reports/P-0N-report.md`; Coordinator sign-off gates the flip; grade from section-4 evidence (`team.tmpl.md` §Closure report).
- **Explicit intent** — no upfront plan+execute ask → pre-attack summary + ask before changing code; silence/ambiguity means stop; default L2 (`AGENTS.md` §Autonomy).

## Core conventions

1. **Log append-only** — one entry per session; never rewrite history.
2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
3. **Ground every claim in `file:line`** — a point is **ungrounded** until every citation passes the drift check (with re-anchor) recorded by the newest ground entry in `log.md`; ungrounded points can't be ready or executed.
4. **One point = one responsibility + one runnable done-signal**.
7. **Status vocabulary**: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done · ⚪ skipped.
11. **Authority order** — user > spec > tests > current code, at every gate including None. A check that contradicts the spec is surfaced, never silently satisfied.

## Where the detail lives

`references/guides/` (per-step guides) · `AGENTS.tmpl.md` (workspace contract) · `team.tmpl.md` (teams) · `*.tmpl.md` + `sdd/` (templates).
