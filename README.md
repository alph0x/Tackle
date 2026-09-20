# Tackle

Tackle helps an AI agent plan work, carry it across sessions, and execute it when you ask. Plans live in your repository as Markdown. Each task, called a Point, includes the context, scope, and checks an agent needs to pick it up in a fresh session.

Use it for features, refactors, and investigations that span sessions or involve handoffs between agents or people. It works with any agent that can read Markdown and search your code.

Tackle 8.1.0 ships as `SKILL.md` plus `references/`. Select Tackle, then tell it what you need: a plan, implementation, a progress check, or a review.

## Install

Install with [skills.sh](https://github.com/alph0x/Tackle):

```sh
npx skills add alph0x/Tackle --skill tackle
```

For a manual install, copy `SKILL.md` and `references/` from a checkout of this repository into your agent's skill directory. For Claude Code:

```sh
mkdir -p ~/.claude/skills/tackle
cp SKILL.md ~/.claude/skills/tackle/
cp -r references ~/.claude/skills/tackle/
```

For Cursor, use `~/.cursor/skills/tackle/`. Other agents use their own skill directory. Tackle follows the [Agent Skills](https://github.com/anthropics/skills) format; the install contains only `SKILL.md` and `references/`.

You control updates through the [manual update guide](references/guides/update.md). Ordinary invocation leaves the installation untouched and performs no network access. Restart your session after an update if your agent cannot reload skills.

## Start a plan, then run it

Select **Tackle** in your agent's skill picker, then write your request. If your app offers `/tackle`, select that entry and continue typing. Selection syntax depends on the app; Tackle has one entry, with the actions inside it.

For example, select Tackle and write “plan an email export,” then “run the plan” when you're ready. You can also ask in Spanish: “armá un plan,” “ejecutá el punto P-03,” or “verificá este plan sin modificarlo.”

Short forms work too. These are requests to the selected skill, not separate menu commands:

| You say | What happens |
|---|---|
| `plan <task>` | The agent clarifies the goal, records decisions, breaks work into Points, checks readiness, and prepares a handoff. |
| `run` | Execute ready Points in dependency order, check the results, and record what passed or remains blocked. |
| `run --one` or `run <P-id>` | Run one Point. |
| `status [<workspace>]`, `list`, or `next` | Read progress, list plans, or find the next Point. |
| `status <workspace> --handoff` | Write a handoff for the next session. |

Open Tackle without a request, or ask for `help`, to see the available actions. It shows help without creating files or starting work. When a request is unclear, it asks before acting.

PLAN prepares the work. RUN needs your explicit request to implement it. STATUS, “next,” and an unqualified “resume” leave source files, the board, and the log unchanged; `--handoff` writes only the requested handoff.

The agent sizes the plan during intake. None handles a bounded local correction, Lite fits a small coherent task, and Full covers work that needs more coordination. Risk takes precedence over Point count. The [sizing guide](references/guides/intake-and-gate.md#step-2--gate-sizing-full--lite--none) lists the conditions.

Each Point names what to change, which files it may touch, how to verify the result, and what it depends on. A dependency names the artifact the next Point needs, such as a file, schema, or protocol. That gives a new agent a concrete place to start.

## What stays in your repository

Lite and Full plans live under `docs/plans/<initiative>/`. Lite uses `plan.md`, `log.md`, and `usage.md`, with separate decisions or questions files when needed. Full adds coordination artifacts:

| File | Purpose |
|---|---|
| `README.md` | Index and reading order. |
| `AGENTS.md` | Instructions for an agent picking up the plan. |
| `plan.md` | Goal, non-goals, Point decomposition, and dependencies. |
| `points/P-0N-*.md` | A self-contained briefing for each Point. |
| `board.md` | Current Point status and evidence grade. |
| `log.md` | Append-only record of sessions and observations. |
| `usage.md` | Observed role starts, finishes, and interrupted runs. |
| `questions.md` / `decisions.md` | Open questions and settled decisions. |
| `reference.md` | Grounded context and source references. |

Full plans add architecture, shared contracts, team bindings, reference snapshots, and reports when the work needs them. A coordinator file is a projection of the current records. Optional `spec.md` and `constitution.md` capture formal material you provide. A requested handoff creates `HANDOFF.md`; a retro creates `retro.md`.

Workspaces and parked ideas in `docs/seeds/` stay local to this repository and never ship with the skill. During setup, you decide whether to gitignore plans in your own repository; seeds receive the same treatment.

## How work gets checked

Before changing behavior, the agent compares the current implementation, the intended result, and the specification. If they contradict one another, it raises the conflict. The authority order is user → specification → protected acceptance and tests → implementation.

RUN checks the target change, surrounding behavior, and affected integrations. Before closing the initiative, the agent checks the merged deliverable against its global acceptance requirements. A passing unit test alone cannot establish that the delivered package or integrated flow works.

Evidence records who ran a check, the command, revision, output, and result. Where a Point requires independent review, a separate reviewer must provide it. Missing checks or capabilities leave the affected work blocked. Historical grades remain readable: E1 for independent command verification, E2 for semantic review, E3 for an assertion, and E0 for unverifiable work.

A Point allows at most three failed correction-validation cycles. Two identical observations with no progress stop the work sooner. Resuming or changing agents preserves the count. When an input changes, the agent rechecks the affected consumers, including dependencies that reach beyond shared file paths.

The [RUN guide](references/guides/run.md) defines these rules. The [failure-modes catalog](references/failure-modes.md) connects them to problems such as weakened tests, invented evidence, and changes outside the agreed scope.

For review or maintenance, select Tackle and ask:

| Request | Purpose |
|---|---|
| `verify [<workspace>]` | Validate a plan before execution, or diagnose it on request. A diagnosis does not authorize fixes. |
| `judge [<target>]` | Audit finished work by inspecting changes and rerunning claimed checks. |
| `judge suite <target>` | Run the trap suite against a skill, model, or prompt. |
| `init <name>` | Create a workspace through PLAN. |
| `migrate` or `upgrade` | Prepare a selected workspace for migration on a disposable copy. |
| `retro [<workspace>]` | Review lessons from the initiative and propose improvements. |

Older examples use names such as `/tackle-verify` and `/tackle-run`. During 8.x, Tackle still understands those as text aliases if your app passes them to the agent. They do not create separate picker entries. If one is unavailable, select Tackle and write `verify` or `run` instead. See the [request guide](references/guides/invocation.md) for the full mapping.

During 8.x, older routes such as `implement`, `ground`, `trace`, `drill`, `pulse`, and `handoff` forward to PLAN, RUN, or STATUS while preserving intent. These aliases retire in 9.0. The migration guide retains the checklist chain v2.0 → v8.1, including the [8.0 → 8.1 checklist](references/guides/migrate.md#v80--v81-checklist) and the [copy-first 7.3 → 8.0 checklist](references/guides/migrate.md#v73--v80-checklist).

## Learning and usage

A retro reads the board and log to propose lessons for the project or your user profile. You confirm profile changes before they are written. “Stop evolving” pauses or removes that learning through the retro workflow. Proven plan structures live in [archetypes](references/archetypes/); the agent can offer one during intake.

The `usage.md` ledger records role events even when token or cost data is unavailable. Unknown values stay `n/a`. An optional `usage.telemetry.jsonl` file can add exact provider observations; recording telemetry is never required to close a Point.

Retro reports measured coverage before comparing usage. Totals and rankings require complete, comparable coverage; model-tier or effort recommendations also require three completed, comparable runs. The [usage guide](references/guides/usage-observability.md) explains the schema, partial coverage, and joining records by exact `run_id`.

Optional capability profiles cover [Claude Code](references/collectors/claude-code.md), [Oh My Pi](references/collectors/oh-my-pi.md), [OpenAI Responses](references/collectors/openai-responses.md), [Antigravity CLI](references/collectors/antigravity-cli.md), [OpenCode](references/collectors/opencode.md), [Kimi Code](references/collectors/kimi-code.md), and [Cursor](references/collectors/cursor.md). They describe available data and its limits. Collection requires separate setup; profiles do not install integrations or collect data automatically.

## Developing Tackle

The [eval suite](eval/README.md) contains **50 scenarios** (`s1`–`s54`): decision traps and one end-to-end lifecycle smoke test. The manual A/B workflow compares a model following Tackle with the same model working without it. Each scenario has an answer sheet that must stay outside the agent's copy. A smoke run provides evidence for that run, with its limits recorded alongside the result.

Before a release, the [release sweep](references/guides/lint-spec.md#release-sweep) runs 8 shipped-skill gates covering the entry-file word budget, 11 core conventions, version and migration consistency, README claims, install contents, and update boundaries. The workspace table covers rows 1–16 (16 lint rows). These are documented, copy-pasteable POSIX checks.

Mechanical gate procedures cover `lint` rows, `catalog` integrity, each `done-signal`, the two-phase `ground` check, `eval` method arms, and `init` artifact completeness. Required independent review also gates completion. Release publication requires a separate owner request.

For deeper changes, see the [team capabilities](references/team.tmpl.md), [discovery and experiment Points](references/guides/decompose-and-lint.md), and [changelog](references/CHANGELOG.md).

## License

MIT
