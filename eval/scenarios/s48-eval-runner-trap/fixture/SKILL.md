---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative needing a durable action plan of self-contained points, before writing implementation code. Also use to verify or red-team a plan before implementation, to judge finished work adversarially, or to run a retro at initiative close.
---

# Tackle

## Overview

**Tackle 6.0.0** — model-agnostic planning/execution methodology: durable plans under `docs/plans/<initiative>/`, self-contained points that survive handoffs; runs in the target repo, grounds every claim in `file:line`.

## Routing

| The user says (any language) | Mode |
|---|---|
| `/tackle-init [preset]` | **Init** → plan-local `presets/` + `overrides/` |
| `/tackle-plan` | **Plan** → Steps 1–7, then hand off |
| `/tackle-judge suite <target>` | **Judge suite** → trap suite vs skill/model/prompt |

Natural-language triggers are canonical; slash commands are aliases.

**Commands are entry points, not boundaries** — internal invocation never bypasses guardrails.

## Core conventions

2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
3. **Ground every claim in `file:line`**.
10. **Harness-agnostic** — works with any agent/LLM and IDE harness; never assume a specific one.
11. **Authority order** — user > spec > tests > current code, at every gate including None.

## Where the detail lives

`references/guides/` (per-step guides) · `eval/README.md` (trap-suite workflow) · `tackle-check` (the mechanical runner).
