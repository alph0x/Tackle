# Tackle

Tackle helps an AI agent plan work, carry it across sessions, and execute it when you ask. Plans live in your repository as Markdown. Each task includes the context, scope, and checks an agent needs to pick it up in a fresh session.

Use it for features, refactors, and investigations that span sessions or involve handoffs between agents or people. It works with any agent that can read Markdown and search your code.

Tackle 8.2.1 ships as `SKILL.md` plus `references/`. Select Tackle, then tell it what you need: a plan, implementation, a progress check, or a review.

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

For example, select Tackle and write “plan and implement an email export.” The agent prepares ready tasks and runs them within the authorized scope. A plan-only request stops after preparation. You can also ask in Spanish: “armá un plan,” “ejecutá el punto P-03,” or “verificá este plan sin modificarlo.”

Short forms work too. These are requests to the selected skill, not separate menu commands:

| You say | What happens |
|---|---|
| `plan <task>` | The agent clarifies the goal, records decisions, prepares task briefs, checks readiness, and prepares a handoff. |
| `run` | Execute ready tasks in dependency order, check the results, and record what passed or remains blocked. |
| `run --one` or `run <P-id>` | Run one task. |
| `status [<workspace>]`, `list`, or `next` | Read progress, list plans, or find the next task. |
| `status <workspace> --handoff` | Write a handoff for the next session. |

Open Tackle without a request, or ask for `help`, to see the available actions. It shows help without creating files or starting work. When a request is unclear, it asks before acting.

PLAN prepares the work. RUN needs execution intent; a scoped PLAN+RUN request supplies it once. Status questions during active work receive an answer and do not cancel that authorization. STATUS, “next,” and an unqualified “resume” leave source files, the board, and the log unchanged; `--handoff` writes only the requested handoff.

The agent sizes the plan during intake. Direct (None) handles a bounded local correction, Focused (Lite) fits bounded durable work, and Coordinated (Full) covers cross-module/API, multi-session/team or handoff needs. The original risk triggers take precedence over task count. The [sizing guide](references/guides/intake-and-gate.md#step-2--gate-sizing-full--lite--none) lists the conditions.

Each task names what to change, which files it may touch, how to verify the result, and what it depends on. A dependency names the artifact the next task needs, such as a file, schema, or protocol. That gives a new agent a concrete place to start.

## What stays in your repository

Focused and Coordinated plans live under `docs/plans/<initiative>/`. Focused uses `plan.md`, `log.md`, and `usage.md`, with separate decisions or questions files when needed. Coordinated adds coordination artifacts:

| File | Purpose |
|---|---|
| `README.md` | Index and reading order. |
| `AGENTS.md` | Instructions for an agent picking up the plan. |
| `plan.md` | Goal, non-goals, Task decomposition, and dependencies. |
| `points/P-0N-*.md` | A self-contained briefing for each task. |
| `board.md` | Canonical current task state and verification references. |
| `log.md` | Append-only record of sessions and observations. |
| `usage.md` | Observed role starts, finishes, and interrupted runs. |
| `questions.md` / `decisions.md` | Open questions and settled decisions. |
| `reference.md` | Grounded context and source references. |

Coordinated plans add architecture, shared contracts, team bindings, reference snapshots, and reports when the work needs them. A coordinator file is a projection of the current records. Optional `spec.md` and `constitution.md` capture formal material you provide. A requested handoff creates `HANDOFF.md`; a retro creates `retro.md`.

Workspaces and parked ideas in `docs/seeds/` stay local to this repository and never ship with the skill. During setup, you decide whether to gitignore plans in your own repository; seeds receive the same treatment.

## Current work and retained records

A criterion states what must hold, a check defines how to observe it, and a verification record
preserves what happened. [Terminology and compatibility](references/terminology.md) maps the
English names to stable P-ids, existing files, historical fields and evidence codes. New validated
boards distinguish Draft, Ready to run, In progress, Checking and Complete; Complete requires all
mandatory task checks. Blocked, Interrupted, Skipped and Unverifiable remain separate.

Long initiatives may keep later milestones at outcome/interface level while preparing current
tasks. All requirements retain owners. [Current-work projections](references/guides/context-lifecycle.md)
validate source revisions before reuse and retrieve archived detail for a specific dependency or
audit. Original history and failed attempts stay recoverable; current decisions never expire by age.

The optional [record lifecycle](references/guides/record-lifecycle.md) stores identical bytes once
per initiative while preserving each actual check event. It protects current proof, unresolved
failures and pinned audits; previews show what an authorized retention policy could retire.
Retired data cannot prove a current check. Export includes required objects. STATUS is read-only;
historical evidence deletion requires existing policy authority or a concrete approval.

## How work gets checked

Before changing behavior, the agent compares the current implementation, the intended result, and the specification. If they contradict one another, it raises the conflict. The authority order is user → specification → protected acceptance and tests → implementation.

RUN checks the target change, surrounding behavior, and affected integrations. Before closing the initiative, the agent checks the merged deliverable against its deliverable acceptance requirements. A passing unit test alone cannot establish that the delivered package or integrated flow works.

Verification records preserve who ran a check, the command, revision, output, and result. Where a task requires independent review, a separate reviewer must provide it. Missing checks or capabilities leave the affected work blocked. Historical grades remain readable: E1 for independent command verification, E2 for semantic review, E3 for an assertion, and E0 for unverifiable work.

A task allows at most three failed correction-validation cycles. Two identical observations with no progress stop the work sooner. Resuming, changing agents, splitting or merging tasks preserves unresolved failure pools and their spent cycles. When an input changes, the agent rechecks the affected consumers, including dependencies that reach beyond shared file paths.

The [RUN guide](references/guides/run.md) defines these rules. The [failure-modes catalog](references/failure-modes.md) connects them to problems such as weakened tests, invented evidence, and changes outside the agreed scope.

For review or maintenance, select Tackle and ask:

| Request | Purpose |
|---|---|
| **validate the plan**, `verify [<workspace>]` | Validate a plan before execution, or diagnose it on request. A diagnosis does not authorize fixes. |
| **audit the result**, `judge [<target>]` | Audit finished work by inspecting changes and rerunning claimed checks. |
| `judge suite <target>` | Run the trap suite against a skill, model, or prompt. |
| `init <name>` | Create a workspace through PLAN. |
| `migrate` or `upgrade` | Prepare a selected workspace for migration on a disposable copy. |
| **review lessons**, `retro [<workspace>]` | Review lessons from the initiative and propose improvements. |

Older examples use names such as `/tackle-verify` and `/tackle-run`. During 8.x, Tackle still understands those as text aliases if your app passes them to the agent. They do not create separate picker entries. If one is unavailable, select Tackle and write `verify` or `run` instead. See the [request guide](references/guides/invocation.md) for the full mapping.

During 8.x, older routes such as `implement`, `ground`, `trace`, `drill`, `pulse`, and `handoff` forward to PLAN, RUN, or STATUS while preserving intent. These aliases retire in 9.0. The migration guide retains the checklist chain v2.0 → v8.2, including the [8.1 → 8.2 checklist](references/guides/migrate.md#v81--v82-checklist), [8.0 → 8.1 checklist](references/guides/migrate.md#v80--v81-checklist) and [copy-first 7.3 → 8.0 checklist](references/guides/migrate.md#v73--v80-checklist).

## Learning and usage

A retro reads the board and log to propose lessons for the project or your user profile. You confirm profile changes before they are written. “Stop evolving” pauses or removes that learning through the retro workflow. Proven plan structures live in [reference plans](references/archetypes/); the agent can offer one during intake.

The `usage.md` ledger records role events even when token or cost data is unavailable. Unknown values stay `n/a`. An optional `usage.telemetry.jsonl` file can add exact provider observations; recording telemetry is never required to close a task.

Retro reports measured coverage before comparing usage. Totals and rankings require complete, comparable coverage; model-tier or effort recommendations also require three completed, comparable runs. The [usage guide](references/guides/usage-observability.md) explains the schema, partial coverage, and joining records by exact `run_id`. For Codex Desktop or `codex exec --json`, an [optional native capture recipe](references/guides/codex-native-usage.md) fills session-scoped token observations and available configured model/effort without guessing per-role usage or cost.

Optional capability profiles cover [Claude Code](references/collectors/claude-code.md), [Oh My Pi](references/collectors/oh-my-pi.md), [OpenAI Responses](references/collectors/openai-responses.md), [Antigravity CLI](references/collectors/antigravity-cli.md), [OpenCode](references/collectors/opencode.md), [Kimi Code](references/collectors/kimi-code.md), and [Cursor](references/collectors/cursor.md). They describe available data and its limits. Collection requires separate setup; profiles do not install integrations or collect data automatically.

## Developing Tackle

Run `python3 eval/run_suites.py` for the explicit deterministic suite registry. CI uses the same
registry and rejects missing test files, zero discovery, unregistered suites and failing tests.
The [paired experiment protocol](eval/clear-language/protocol.md) defines fixed tasks, oracle,
budget and model capabilities. The [8.2 development results](eval/clear-language/results-8.2.md)
summarize twelve paired episodes against the 8.1.0 baseline and ten focused follow-up episodes.
Observed fixes and failed attempts are reported separately; these runs do not establish general
reliability or delivery-efficiency improvement.


The [eval suite](eval/README.md) contains **50 scenarios** (`s1`–`s54`): decision traps and one end-to-end lifecycle smoke test. The manual A/B workflow compares a model following Tackle with the same model working without it. Each scenario has an answer sheet that must stay outside the agent's copy. A smoke run provides evidence for that run, with its limits recorded alongside the result.

Before a release, the [release sweep](references/guides/lint-spec.md#release-sweep) runs 8 shipped-skill gates covering the entry-file word budget, 11 core conventions, version and migration consistency, README claims, install contents, and update boundaries. The workspace table covers rows 1–16 (16 lint rows). These are documented, copy-pasteable POSIX checks.

Mechanical gate procedures cover `lint` rows, `catalog` integrity, each `done-signal`, the two-phase `ground` check, `eval` method arms, and `init` artifact completeness. Required independent review also gates completion. Release publication requires a separate owner request.

For deeper changes, see the [team capabilities](references/team.tmpl.md), [discovery and experiment tasks](references/guides/decompose-and-lint.md), and [changelog](references/CHANGELOG.md).

## License

MIT
