# Tackle

A model-agnostic planning skill that turns an initiative into a durable action plan, broken into self-contained points that can be attacked across different sessions and agents — and can execute that plan point-by-point when you ask it to.

## What it does

Tackle produces a workspace of grounded markdown artifacts under `docs/plans/<initiative>/` in your repository. Each point's `.md` carries all the info needed to resolve it in a fresh session — context, approach, recommended prompt, and alternatives.

**Tackle plans and can execute the plan it produces.** It never writes implementation code on its own. The optional `/tackle-implement` and `/tackle-next` modes drive execution by spawning the point team defined in `team.md`, running each point's done-signal, and advancing the board.

## Who is it for

Any team or developer that:
- Works on multi-session initiatives (Jira tickets, features, refactors, investigations)
- Hands off work between agents, models, or humans
- Needs plans that survive context window limits and session boundaries
- Wants every point to be independently tackleable by a cold agent
- Wants the same skill to drive execution, not just planning

## Install

Tackle follows the [Agent Skills](https://github.com/anthropics/skills) format.

**Claude Code:**
```bash
cp -r tackle ~/.claude/skills/
```

**Cursor / other:**
```bash
cp -r tackle ~/.cursor/skills/  # or your agent's skills directory
```

**Any model / IDE:**
Copy `SKILL.md` and the `references/` directory into your agent's skill directory.

## How to use

Trigger words: `plan de acción`, `armar un plan`, `plan this out`, `tackle this`, `iniciativa`.

**SDD phase triggers (optional, chainable):**

| You say | Mode |
|---|---|
| `/tackle-init [preset]` | **Init** — create the plan-local customization tree (`presets/`, `overrides/`) |
| `/tackle-constitution` | **Constitution** — establish project principles |
| `/tackle-specify` | **Specify** — write the product spec |
| `/tackle-plan` | **Plan** — build the full decomposed plan (standalone default) |
| `/tackle-tasks` | **Tasks** — flatten the plan into a checklist |
| `/tackle-implement` | **Implement** — execute the plan point-by-point |
| `/tackle-next` | **Execute next** — execute one ready point |
| `/tackle-checklist` | **Checklist** — generate a quality checklist |
| `/tackle-verify` | **Verify** — red-team pass over each point before implementation |
| `/tackle-ground` | **Ground** — mechanically read and mark every `file:line` cited in the plan |

**Legacy modes:**

| You say | Mode |
|---|---|
| "tackle this" / new initiative | **Create** — build the plan (same as `/tackle-plan`) |
| "resume / retomá `<x>`" | **Resume** — re-enter a plan |
| "how is `<x>` going?" / "status" | **Status** — read-only digest |
| "what plans are there?" | **List** — one line per initiative |
| "what's next?" / "qué sigue" | **Next** — the next point's pre-attack summary |
| "migrate / upgrade `<x>`" | **Migrate** — bring an old plan up to the current methodology (Step 8.5; v2.0 → v2.1.0 checklist in `references/guides/migrate.md`) |
| "mejorá este plan" / "improve this plan" | **Improve** — upgrade a Tackle plan or convert an unstructured plan |

**The Create pipeline:** Intake → Gate (None/Lite/Full) → Location & gitignore → Scaffold → Briefing → Architecture → Stabilize contract → Decompose → Lint → Handoff.

**Execution:** `/tackle-implement` reads `board.md`, picks the next ready point in dependency order, runs its done-signal, and updates `board.md` + `log.md`. Team sizing is Solo/Pair/Pod/Squad per `team.md`.

**Template-resolution stack:** overrides → presets → sdd → core.

**Version:** Tackle 2.1.1. See `references/CHANGELOG.md` for what's new.

## What it produces

| Artifact | Purpose |
|---|---|
| `README.md` | Human index, reading order |
| `AGENTS.md` | Operating contract for any agent that picks up the plan |
| `plan.md` | Objective, non-goals, point decomposition + dependency graph |
| `board.md` | Canonical status board for execution (canonical; do not duplicate status in `plan.md`) |
| `log.md` | Append-only session log (canonical state) |
| `todo.md` | Planning-readiness checklist |
| `questions.md` | Single source of open questions |
| `decisions.md` | Closed decisions register |
| `reference.md` | Current code state with `file:line` |
| `points/P-0N-*.md` | One self-contained briefing per point |

**Depth artifacts (Full only, created only when their trigger fires):**

| Artifact | When |
|---|---|
| `foundations.md` | Non-trivial architecture |
| `design-contract.md` | Shared surface that points must conform to |
| `execution-strategy.md` | Multi-agent/parallel/phased execution |
| `team.md` | Multi-agent execution teams |
| `reference-docs/` | External material snapshots |

## Model-agnostic

Works with GPT, Claude Opus/Sonnet, Cursor Composer, Kimi, DeepSeek, or any agent that can read markdown and search code. No vendor-specific tools assumed.

## Optional companions

- [superpowers](https://github.com/obra/superpowers) — for `brainstorming` / `writing-plans` depth
- [karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) — for simplicity-first discipline
- [solid-skills](https://github.com/ramziddin/solid-skills) — for architecture / SOLID decisions

## License

MIT
