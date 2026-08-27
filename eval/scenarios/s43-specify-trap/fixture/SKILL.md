---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative needing a durable action plan of self-contained points, before writing implementation code. Also use when resuming, checking status, listing plans, getting the next point, or migrating an old plan.
---

# Tackle

## Overview

**Tackle 7.0** — model-agnostic planning/execution methodology: durable plans under `docs/plans/<initiative>/`, self-contained points that survive handoffs; runs in the target repo, grounds every claim in `file:line`.

## Routing

| The user says (any language) | Mode |
|---|---|
| `/tackle-plan` | **Plan** → Steps 1–7; intake may instantiate optional `spec.md`/`constitution.md` when the user brings formal material |
| `stop evolving` | **Evolution opt-out** → pause/purge learning-loop profile, per scope (inside retro) |

Natural-language triggers are canonical; slash commands are aliases.

**Commands are entry points, not boundaries** — internal invocation never bypasses guardrails (`intake-and-gate.md`).

## Core conventions

2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
8. **Decision ownership** — the user decides every doubt; batch recommendations with defaults.
11. **Authority order** — user > spec > tests > current code, at every gate including None. A check that contradicts the spec is surfaced, never silently satisfied.

## Where the detail lives

`references/guides/` (per-step guides) · `AGENTS.tmpl.md` (workspace contract) · `team.tmpl.md` (teams) · `*.tmpl.md` (templates).
