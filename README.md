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

Tackle runs in 8 steps:

1. **Intake** — asks for requirement, docs, scope, owners, codebase
2. **Gate** — sizes the initiative (None / Lite / Full)
3. **Location** — creates `docs/plans/<initiative>/` in your repo
4. **Scaffold** — copies templates, fills placeholders
5. **Briefing** — grounds the plan in real `file:line`
6. **Decompose** — breaks into independent, self-contained points
7. **Compose** — optionally uses superpowers / karpathy / solid for depth
8. **Resume** — re-enters an existing plan and continues from the last entry

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
| `points/P-0N-*.md` | One self-contained briefing per point |

## Model-agnostic

Works with GPT, Claude Opus/Sonnet, Cursor Composer, Kimi, DeepSeek, or any agent that can read markdown and search code. No vendor-specific tools assumed.

## Optional companions

- [superpowers](https://github.com/obra/superpowers) — for `brainstorming` / `writing-plans` depth
- [karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) — for simplicity-first discipline
- [solid-skills](https://github.com/ramziddin/solid-skills) — for architecture / SOLID decisions

## License

MIT
