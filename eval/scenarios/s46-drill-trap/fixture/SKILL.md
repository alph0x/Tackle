---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative needing a durable action plan of self-contained points, before writing implementation code. Also use when the user asks to establish project principles (constitution), specify a product, flatten a plan into tasks, generate a quality checklist, or drill a point briefing cold.
---

# Tackle

## Overview

**Tackle 6.0.0** — model-agnostic planning/execution methodology: durable plans under `docs/plans/<initiative>/`, self-contained points that survive handoffs; runs in the target repo, grounds every claim in `file:line`.

## Routing

| The user says (any language) | Mode |
|---|---|
| `/tackle-constitution` | **Constitution** → `constitution.md` |
| `/tackle-specify` | **Specify** → `spec.md` |
| `/tackle-plan` | **Plan** → Steps 1–7, then hand off |
| `/tackle-tasks` | **Tasks** → `tasks.md` |
| `/tackle-checklist` | **Checklist** → `checklist.md` |
| `/tackle-drill` | **Drill** → cold-start drill on one point briefing |
| `stop evolving` | **Evolution opt-out** → pause/purge learning-loop profile, per scope |

Natural-language triggers are canonical; slash commands are aliases.

**Commands are entry points, not boundaries** — internal invocation never bypasses guardrails (`intake-and-gate.md`).

## Core conventions

2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
3. **Ground every claim in `file:line`** — a point is **ungrounded** until every citation passes the drift check; ungrounded points can't be ready or executed.
4. **One point = one responsibility + one runnable done-signal**.
8. **Decision ownership** — the user decides every doubt; batch recommendations with defaults.
11. **Authority order** — user > spec > tests > current code, at every gate including None. A check that contradicts the spec is surfaced, never silently satisfied.

## Where the detail lives

`references/guides/` (per-step guides) · `*.tmpl.md` + `sdd/` (templates).
