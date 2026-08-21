---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative needing a durable action plan of self-contained points, before writing implementation code. Also use when the user asks to initialize a plan-local customization tree.
---

# Tackle

## Overview

**Tackle 6.0.0** — model-agnostic planning/execution methodology: durable plans under `docs/plans/<initiative>/`, self-contained points that survive handoffs; runs in the target repo, grounds every claim in `file:line`.

## Routing

| The user says (any language) | Mode |
|---|---|
| `/tackle-init [preset]` | **Init** → plan-local `presets/` + `overrides/` |
| `/tackle-plan` | **Plan** → Steps 1–7, then hand off |

Natural-language triggers are canonical; slash commands are aliases.

**Commands are entry points, not boundaries** — internal invocation never bypasses guardrails.

## Template-resolution stack

`overrides/ > presets/<preset>/ > sdd/ > references/`, first match wins; only `.tackle/` lives at repo root.

## Core conventions

2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
3. **Ground every claim in `file:line`**.
8. **Decision ownership** — the user decides every doubt; batch recommendations with defaults.
9. **Scaffold asks gitignore** — `/tackle-plan` asks about `.gitignore` for `docs/plans/` before creating files; records the decision.
10. **Harness-agnostic** — works with any agent/LLM and IDE harness; never assume a specific one.
11. **Authority order** — user > spec > tests > current code, at every gate including None.

## Where the detail lives

`references/guides/` (per-step guides) · `references/*.tmpl.md` (templates) · `tackle-check` (the mechanical runner, incl. the `scaffold` subcommand).
