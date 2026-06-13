# Tackle

A model-agnostic planning skill that turns an initiative into a durable action plan, broken into self-contained points that can be attacked across different sessions and agents.

## What it does

Tackle produces a workspace of grounded markdown artifacts under `docs/plans/<initiative>/` in your repository. Each point's `.md` carries all the info needed to resolve it in a fresh session — context, approach, recommended prompt, and alternatives.

**Tackle plans. It does not execute.** Execution happens later, in separate sessions, using the point briefings.

## Who is it for

Any team or developer that:
- Works on multi-session initiatives (Jira tickets, features, refactors, investigations)
- Hands off work between agents, models, or humans
- Needs plans that survive context window limits and session boundaries
- Wants every point to be independently tackleable by a cold agent

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

**Modes** (Tackle routes on what you say):

| You say | Mode |
|---|---|
| "tackle this" / new initiative | **Create** — build the plan (the pipeline below) |
| "resume / retomá `<x>`" | **Resume** — re-enter a plan, re-validate the active point, continue |
| "how is `<x>` going?" / "status" | **Status** — read-only digest |
| "what plans are there?" | **List** — one line per initiative |
| "what's next?" / "qué sigue" | **Next** — the next point's pre-attack summary + ready-to-paste prompt |
| "migrate / upgrade `<x>`" | **Migrate** — bring an old plan up to the current methodology, preserving history |

**The Create pipeline:** Intake (infer first, then ask) → Gate (None/Lite/Full) → Location & gitignore → Scaffold → Briefing (ground in `file:line`, lead with the de-risking finding, anchor to precedent) → Architecture (recommended, you decide) → Decompose into loop-runnable points → Lint the wired plan → Handoff in chat. Each point is engineered as a closed loop: a runnable **done-signal**, `Depends-on`/`Touches` wiring for parallelism, recovery + an iteration budget — so execution can run autonomously, point by point, across agents.

**Principles that hold at every gate:** Tackle assumes nothing — every doubt goes to you as a decision (recommended default marked, batched, never drip-fed); self-documenting code; a runnable done-signal; rollout/reversibility when it touches production.

## What it produces

| Artifact | Purpose |
|---|---|
| `README.md` | Human index, reading order |
| `AGENTS.md` | Operating contract for any agent that picks up the plan |
| `plan.md` | Objective, non-goals, point decomposition + dependency graph |
| `log.md` | Append-only session log (canonical state) |
| `todo.md` | Planning-readiness checklist |
| `questions.md` | Single source of open questions (`Q-01`…) |
| `decisions.md` | Closed decisions register (`D-01`…, "don't revisit without cause") |
| `reference.md` | Current code state with `file:line` (shared across points) |
| `points/P-0N-*.md` | One self-contained briefing per point (goal, done-signal, wiring, approach, prompt) |

**Depth artifacts (Full only, created only when their trigger fires):**

| Artifact | When |
|---|---|
| `foundations.md` | The initiative introduces non-trivial architecture (decision → principle → source grounding) |
| `design-contract.md` | Several points must conform to one shared surface (API, wire format, state machine, errors) |
| `execution-strategy.md` | Execution will be multi-agent / parallel / phased (waves + quality gate + the code-quality guardian loop) |
| `reference-docs/` | The plan depends on material outside the repo (read-only snapshots + provenance) |

Lite folds the essentials into a single `plan.md`; None plans inline with no workspace. Bigger workspace ≠ better plan — the gate scales ceremony to the real shape of the work.

## Model-agnostic

Works with GPT, Claude Opus/Sonnet, Cursor Composer, Kimi, DeepSeek, or any agent that can read markdown and search code. No vendor-specific tools assumed.

## Optional companions

- [superpowers](https://github.com/obra/superpowers) — for `brainstorming` / `writing-plans` depth
- [karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) — for simplicity-first discipline
- [solid-skills](https://github.com/ramziddin/solid-skills) — for architecture / SOLID decisions

## License

MIT
