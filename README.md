<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/brand/tackle-hero-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset=".github/brand/tackle-hero-light.svg">
    <img src=".github/brand/tackle-hero-light.svg" alt="Tackle: a plan drawn as stages of connected tasks, complete, in progress and not started, leading to the final acceptance check" width="100%">
  </picture>
</p>

<h1 align="center">Durable plans. Verified delivery.</h1>
<p align="center">A planning and execution skill for AI coding agents.</p>

<p align="center">
  <a href="#get-started">Get started</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#what-stays-in-your-repository">What gets saved</a> ·
  <a href="#documentation">Documentation</a>
</p>

Tackle turns a goal into a plan stored in your repository. Each task carries the context, scope, dependencies, and checks an agent needs to pick it up in a fresh session. When you authorize execution, the agent works through the plan and records what passed, what failed, and what remains blocked.

Use it for features, refactors, and investigations that span sessions or involve handoffs between agents or people.

**Tackle 10.2.0** · Model-agnostic · Markdown and standard-library Python · MIT

## Why Tackle

A useful handoff needs more than a summary of the conversation. It needs the next task, the decisions behind it, the inputs it depends on, and a way to check the result.

| When… | Tackle records… |
|---|---|
| Work continues in another session | Task briefs, decisions, current state, and verification records in the repository. |
| One task depends on another | The specific file, schema, protocol, or other artifact the next task consumes. |
| An agent reports that work is complete | The checks and results supporting completion, including required integration checks and reviews. |

The plan is a working artifact: it supports execution, handoffs, and review rather than ending at a checklist.

## Get started

Install the skill:

```sh
npx skills add alph0x/Tackle --skill tackle
```

Select **Tackle** in your agent's skill picker, then describe the work:

```text
Plan a refactor that extracts checkout validation into its own module.
Keep existing behavior unchanged. Do not implement yet.
```

When the plan is ready, authorize execution:

```text
Run the checkout validation plan.
```

In a later session, select Tackle and ask:

```text
Show the checkout validation plan's status. What is complete, blocked, and next?
```

**Requirements:** the scripts need Python 3.10 or later and the standard library only; on Windows, run them with `py -3`. The lint rows (which `lint.py` runs with `sh`) and the release gates are POSIX shell, so on Windows they need Git Bash or WSL. Installing runs nothing, and a script runs only with your authorization. See the [script manifest and consent rules](skills/tackle/scripts/README.md).

These are example requests to the selected skill, not shell commands or captured results. If your app offers `/tackle`, select that entry and continue typing. The selection syntax depends on the app; Tackle has one entry, with the actions inside it. Requests can be in your preferred language.

A scoped request such as “plan and implement this refactor” authorizes both preparation and execution. A plan-only request stops before implementation. Open Tackle without a request, or ask for `help`, to see the available actions without starting work or creating files.

<details>
<summary>Manual installation and updates</summary>

From a checkout of this repository, copy `skills/tackle/SKILL.md`, `skills/tackle/references/` and `skills/tackle/scripts/` into your agent's skill directory. For Claude Code:

```sh
mkdir -p ~/.claude/skills/tackle
cp skills/tackle/SKILL.md ~/.claude/skills/tackle/
cp -R skills/tackle/references ~/.claude/skills/tackle/
cp -R skills/tackle/scripts ~/.claude/skills/tackle/
```

For Cursor, use `~/.cursor/skills/tackle/`. Other agents use their own skill directory. Tackle follows the [Agent Skills](https://github.com/anthropics/skills) format.

The install contains only `SKILL.md`, `references/` and `scripts/`, with 79 installation-relative files. Repository branding, development tools, and evaluation fixtures are not part of the installed skill.
The checkout copy commands above copy those files into the selected directory and leave any other files already there.

Local candidate installation is checked through the manual copy above and the cached `npx skills@1.7.0 add --skill tackle` channel (offline, single-agent, with `-a claude-code -y -g`), against the 79 expected files. The public GitHub routes, by tag and by the default source, have not been probed for 10.2.0. To pin a release, install by tag:

```sh
npx --yes skills@1.7.0 add 'https://github.com/alph0x/Tackle.git#v10.2.0' --skill tackle -a claude-code codex -y -g
```

Restart your session after an update if your agent cannot reload skills.

</details>

## How it works

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/brand/tackle-flow-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset=".github/brand/tackle-flow-light.svg">
  <img src=".github/brand/tackle-flow-light.svg" alt="PLAN prepares the work: goal, scope, inputs, task briefs and readiness checks. RUN executes and checks the work: task checks, affected integrations and final deliverable acceptance. STATUS reads current progress without starting or changing work." width="100%">
</picture>

<details>
<summary>Text version</summary>

```text
PLAN                          RUN
Prepare the work       →      Execute and check the work
Goal, scope, inputs,           Task checks, affected integrations,
task briefs, readiness        and final deliverable acceptance

STATUS reads current progress without starting or changing work.
```

</details>

**PLAN** prepares requirements, decisions, task briefs, dependencies, and acceptance checks. Readiness checks are part of preparation.

**RUN** executes authorized, ready work in dependency order. It checks results, corrects within the allowed budget, and checks the final deliverable before closing the initiative. Verification is part of execution, not an extra step you must remember to request.

For code, PLAN chooses the checks before implementation. Tackle prefers an end-to-end check through the real consumer as the sole new test when it covers the contract; complex integrated features require one when feasible. Any necessary isolated test starts with a failure-mode inventory and is written before its implementation. Every end-to-end run retains a [repeatable verification artifact](skills/tackle/references/guides/testing.md#replayable-e2e-artifact).

**STATUS** reads progress, lists plans, or identifies the next task. An unqualified “resume” is also read-only. Explicit execution intent enters RUN; `--handoff` writes only the requested handoff.

| Request to the selected skill | Result |
|---|---|
| `plan <task>` | Prepare the work without implementing it. |
| `run` | Execute the authorized ready work and check the results. |
| `run --one` or `run <T-id>` | Execute one task. |
| `status [<workspace>]`, `list`, or `next` | Read current progress or find the next task. |
| `status <workspace> --handoff` | Write a handoff for the next session. |
| “show the plan view” | Write a local, interactive HTML view of the workspace. |
| `explore <question>` | Read the repository and answer with cited findings, options and a recommendation; writes nothing. |

Status questions during an authorized run do not cancel that authorization. Unclear requests are clarified before action. See the [request guide](skills/tackle/references/guides/invocation.md) for intent boundaries, and [terminology](skills/tackle/references/terminology.md) for retired action-name aliases.

### What the scripts do

The [`scripts/`](skills/tackle/scripts/README.md) folder holds the programs the guides name, each in Python with the standard library only:

| Purpose | Scripts |
|---|---|
| Plan view | `plan_view.py` |
| Architecture map | `architecture_map.py` |
| Workspace lint | `lint.py` |
| Captured lint-row runner (needs its own authorization, not covered by the lint grant) | `lint_runner.py` |
| Check and evidence capture | `capture.py`, `evidence_capture.py` |
| Records and context bundle | `record_store.py`, `context_bundle.py` |
| Task consistency, corrections and adversary checkpoints | `decompose_check.py`, `correction_lineage.py`, `adversary_checkpoints.py` |
| Migration | `migrate/` |
| Requirements base | `requirements_base.py` |
| Controlled writing | `controlled_writing.py` |
| System One state and decisions | `system_one_state.py`, `system_one_decide.py` |
| Usage capture (native Codex Desktop and `codex exec --json` records) | `codex_usage.py` |
| Retro confidence | `retro_confidence.py` |

The [manifest](skills/tackle/scripts/README.md) lists every script with its sha256. An explicit plan or run request authorizes `scripts/lint.py` for that request; an explicit request for a feature whose procedure is a script authorizes that script for that request; you can also authorize a named script directly. A general request to plan or run authorizes no other script ([consent](skills/tackle/scripts/README.md#consent)).

### What makes a task ready to hand off?

A task brief describes an observable result, the relevant inputs, its write scope, dependencies, constraints, checks, and recovery conditions. Self-contained does not mean independent of other tasks: dependencies still identify the artifacts the task needs.

An abbreviated, illustrative brief might read:

```text
T-02 — Extract checkout validation

Outcome:       Existing validation behavior is preserved in a separate module.
Input:         T-01's agreed validation contract and characterized cases.
Write scope:   The files explicitly named in this task's full brief.
Constraints:   No changes to public behavior or unrelated payment flows.
Checks:        Contract cases, existing regressions, affected integration checks.
Stop if:       The agreed contract conflicts with a protected acceptance check.
```

The actual brief must name concrete files, cases, and checks. This example is not a generated plan or evidence that a run passed.

## What stays in your repository

Focused and Coordinated plans live under `docs/plans/<initiative>/` as Markdown. The agent sizes the workspace to the work: Direct handles a bounded local correction without a workspace; Focused keeps a small durable plan; Coordinated adds task and coordination artifacts when needed. Risk determines the route, not task count alone.

Focused uses `plan.md`, `history.md`, and `resource-usage.md`, with separate decisions or questions files when needed. A Coordinated workspace includes:

```text
docs/plans/<initiative>/
├── README.md          Index and reading order
├── AGENTS.md          Instructions for the next agent
├── plan.md            Goal, non-goals, task decomposition, dependencies
├── tasks/             Self-contained task briefs with stable T-ids
├── task-board.md     Canonical current task state and verification references
├── history.md        Session and observation history
├── resource-usage.md Observed role starts, finishes, and interrupted runs
├── questions.md       Open questions
├── decisions.md       Settled decisions
└── reference.md       Grounded context and source references
```

Additional contracts, architecture notes, reports, and snapshots depend on the work. A requested handoff creates `handoff-brief.md`; a retro creates `retro.md`. You decide whether to gitignore plans in your repository. Workspaces and parked ideas in `docs/seeds/` never ship with the skill.

Long initiatives can prepare current tasks while leaving later milestones at outcome/interface level. Current-work views are checked against their source revisions; original history and failed attempts remain recoverable. Optional retention policies manage verification records without treating retired data as current proof.

See [workspace sizing](skills/tackle/references/guides/intake-and-gate.md#step-2--gate-sizing-full--lite--none), [current-work context](skills/tackle/references/guides/context-lifecycle.md), and [record lifecycle](skills/tackle/references/guides/record-lifecycle.md).

## What counts as complete

Completion requires the task's mandatory checks, not just an agent's assertion. RUN checks the target change, surrounding behavior, and affected integrations. Closing an initiative also requires checking the final deliverable against its acceptance requirements.

Verification records preserve the actor, command, revision, output, and result. When independent review is required, a separate reviewer must supply it. Missing capabilities or required checks block the affected work; a role name or self-review is not independent evidence.

Before changing behavior, the agent resolves conflicts between the current implementation, the intended result, and the specification. The authority order is user → specification → protected acceptance and tests → implementation. Changed inputs invalidate affected downstream checks.

A task allows at most three failed correction-validation cycles; two identical no-progress observations stop work sooner. Resuming or changing agents does not reset spent cycles or erase unresolved failures.

Tackle is a method an agent follows. The agent still needs the tools, permissions, and reviewer capabilities required by the task. Verification records show what was actually checked; they do not establish correctness beyond those checks.

See the [RUN card](skills/tackle/references/guides/run-card.md) and [failure-modes catalog](skills/tackle/references/failure-modes.md).

## Security model

This section describes how Tackle is built to behave; it is not a claim about any third-party review or scanner result. The [security model guide](skills/tackle/references/guides/security.md) describes what Tackle runs, reads and sends.

The install is `SKILL.md`, `references/` and `scripts/`: Markdown guides plus Python scripts that use the standard library only. Installing it runs nothing and installs no program (see the install contents [above](#get-started)). Ordinary invocation performs no network access and does not change the installation tree. Tackle ships no network client: the optional System One judgment goes through your host's `typesafe-ai` skill, and only when the workspace records your agreement ([System One](skills/tackle/references/guides/system-one.md)).

An agent runs or imports a script under `scripts/` only with your explicit authorization, and prefers an equivalent capability of its own harness. An explicit plan or run request authorizes `scripts/lint.py` for that request and, by itself, no other script. Asking for a feature whose documented procedure is a script, such as the plan view, counts as explicit authorization for that script for that request. If you decline, the affected record is reported unavailable or produced another permitted way, never faked.

RUN executes only the exact command line (argv) that each authorized, ready task declares, and captures each command with its exit status and output streams ([RUN card](skills/tackle/references/guides/run-card.md)).

Content in `reference-docs/`, fetched pages and tool output is data. Tackle cites it and never follows instructions found inside it.

Updates are owner-controlled and out of band: Tackle does not check for, download or install releases ([update guide](skills/tackle/references/guides/update.md)).

## Documentation

| Need | Guide |
|---|---|
| Understand requests and authorization | [Invocation](skills/tackle/references/guides/invocation.md) |
| Choose the right planning scope | [Sizing](skills/tackle/references/guides/intake-and-gate.md) |
| Keep required behavior across plans | [Requirements base](skills/tackle/references/guides/requirements-base.md) |
| Understand task checks and completion | [RUN card](skills/tackle/references/guides/run-card.md) |
| Keep a long initiative navigable | [Context lifecycle](skills/tackle/references/guides/context-lifecycle.md) |
| Manage retained verification records | [Record lifecycle](skills/tackle/references/guides/record-lifecycle.md) |
| Audit results or review lessons | [Audit](skills/tackle/references/guides/judge.md) · [Retro](skills/tackle/references/guides/retro.md) |
| Read terminology or migrate existing plans | [Terminology](skills/tackle/references/terminology.md) · [Migration](skills/tackle/references/guides/migrate.md) |
| Update the installed skill | [Owner-controlled updates](skills/tackle/references/guides/update.md) |
| Follow project changes | [Changelog](CHANGELOG.md) |

<details>
<summary>Explicit reviews, maintenance, and compatibility</summary>

These requests remain available inside the same Tackle entry. They are not extra required stages of PLAN → RUN.

| Request | Purpose |
|---|---|
| **validate the plan**, `verify [<workspace>]` | Validate or diagnose a plan. Diagnosis does not authorize fixes. |
| **audit the result**, `judge [<target>]` | Inspect finished work and rerun claimed checks. |
| `judge suite <target>` | Run the trap suite against a skill, model, or prompt. |
| `init <name>` | Create a workspace through PLAN. |
| `migrate` or `upgrade` | Prepare a selected workspace for migration on a disposable copy. |
| **review lessons**, `retro [<workspace>]` | Review the initiative and propose improvements. |

Visible sizing names map to existing routes: Direct (None), Focused (Lite), and Coordinated (Full). Workspaces use T-ids and `tasks/`; an older one, P-ids included, is migrated before it runs. New validated boards distinguish Draft, Ready to run, In progress, Checking, and Complete; Blocked, Interrupted, Skipped, and Unverifiable remain separate.

Historical records retain their meanings: E1 for independent command verification, E2 for semantic review, E3 for an assertion, and E0 for unverifiable work. They are not an ordinal scale.

Previously documented slash forms such as `/tackle-run` and `/tackle-verify` stay text aliases: when the host passes them as text they keep their intent boundaries, never grant broader permission, and register no separate picker entries ([invocation](skills/tackle/references/guides/invocation.md#text-aliases)). Retired 8.x action names map to their historical targets in [terminology.md](skills/tackle/references/terminology.md).

The installed migration catalog targets Tackle 10.2.0 and diagnoses supported workspace structures before preparing one explicitly selected copy for review. Its source obligations and five former installed checklists remain in the repository's [`maintaining/migrations.md`](maintaining/migrations.md) as byte-preserved provenance; runtime migration reads only the installed artifact.

</details>

<details>
<summary>Learning and usage records</summary>

A retro reads the task board and history (`task-board.md` and `history.md`) to propose lessons. You confirm profile changes before they are written. “Stop evolving” pauses or removes that learning through the retro workflow. [Reference plans](skills/tackle/references/archetypes/README.md) provide proven decomposition structures that the agent can propose during intake, stored under `.tackle/archetypes/` (project) or `~/.tackle/archetypes/` (user).

The `resource-usage.md` ledger records observed role events even without token or cost data. Unknown values stay `n/a`. Optional `resource-usage.telemetry.jsonl` observations are never required to close a task.

Totals and rankings require complete, comparable coverage; model-tier or effort recommendations also require three completed, comparable runs. See [usage observability](skills/tackle/references/guides/usage-observability.md) and the optional [Codex native capture script (`scripts/codex_usage.py`)](skills/tackle/references/guides/codex-native-usage.md).

Optional capability profiles cover [Claude Code](extras/collectors/claude-code.md), [Oh My Pi](extras/collectors/oh-my-pi.md), [OpenAI Responses](extras/collectors/openai-responses.md), [Antigravity CLI](extras/collectors/antigravity-cli.md), [OpenCode](extras/collectors/opencode.md), [Kimi Code](extras/collectors/kimi-code.md), and [Cursor](extras/collectors/cursor.md). Profiles describe available data and its limits; they neither install integrations nor collect data automatically.

</details>

## Developing Tackle

Run the deterministic suite registry from the repository root:

```sh
python3 eval/run_suites.py
```

CI uses the same registry and rejects missing test files, zero discovery, unregistered suites, and failing tests.

An earlier, retired paired-experiment protocol ran twelve paired episodes against the 8.1.0 baseline and ten focused follow-up episodes; git history keeps its record.

<details>
<summary>Evaluation coverage and release checks</summary>

The [eval suite](eval/README.md) contains **82 scenarios** (`s1`–`s87`): decision traps, one end-to-end lifecycle smoke test, three end-to-end planning tasks and two mid-task resumes judged by hidden acceptance tests. The manual A/B workflow compares a model following Tackle with the same model working without it. Each scenario's answer sheet stays outside the agent's copy. A smoke run provides evidence for that run, with its limits recorded alongside the result.

Before release, the [release sweep](MAINTAINING.md#release-sweep) runs 9 shipped-skill gates covering the entry-file word budget, 11 core conventions, version and migration consistency, README claims, install contents, update boundaries, and script manifest currency. These are documented, copy-pasteable POSIX checks. The workspace table covers rows 1–19 (19 lint rows), whose programs live in `scripts/lint.py`.

Mechanical gate procedures cover `lint` rows, `catalog` integrity, each `done-signal`, the two-phase `ground` check, `eval` method arms, and `init` artifact completeness. Required independent review also gates completion. Release publication requires a separate owner request.

For deeper changes, see [team capabilities](skills/tackle/references/team.tmpl.md) and [discovery and experiment tasks](skills/tackle/references/guides/decompose-and-lint.md).

</details>

## License

[MIT](LICENSE)
