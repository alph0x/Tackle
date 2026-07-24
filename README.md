# Tackle

A model-agnostic planning and execution skill that turns an initiative into a durable action plan — self-contained points a cold agent can resolve in a fresh session — and executes that plan point-by-point when you ask it to.

**Tackle 4.0.0: durable plans that are graph-real and honest about their evidence.** Every dependency edge names its crossing artifact; every closed point carries an evidence grade derived from how it was actually verified; a plan's confidence is its weakest link.

## What it does

Tackle produces a workspace of grounded markdown artifacts under `docs/plans/<initiative>/` in your repository. Each point briefing carries everything needed to resolve it cold — context, approach, recommended prompt, and alternatives.

**Tackle plans and can execute the plan it produces.** It never writes implementation code on its own. The optional `/tackle-implement` and `/tackle-next` modes drive execution by spawning the point team defined in the workspace's team roster, running each point's done-signal, and advancing the board.

## Graph execution

- **Edge audit** — every `Depends-on` edge must name the **crossing artifact** the downstream point consumes (a file, a section, a schema, a protocol); `/tackle-verify` flags edges that don't. False edges get cut; legitimate ordering-only edges get waived as recorded decisions.
- **Loop archetypes** — a point can be `Type: discovery` (done-signal is convergence: K consecutive rounds surfacing zero new findings, dedupe against everything seen, never a fake pass at budget) or `Type: experiment` (done-signal is a metric threshold: one change per round, keep on improvement, roll back otherwise, the evaluator file untouchable). The **loop-worthiness test** gates both — a loop earns its cost only when the task repeats, verification is automated, the round budget absorbs the waste, and the agent has real tools.
- **Multi-lens checker** — an optional `Lenses:` field in a point briefing runs N independent skeptic checks, one per lens (e.g. correctness, security, repro); a finding survives only under majority vote.

## Proof-carrying plans

- **Evidence grades, derived not declared** — every closed point carries an evidence grade: **E1** command-verified (an independent checker re-ran the done-signal), **E2** review-gated (rubric + named reviewer), **E3** asserted, **E0** explicitly unverifiable. The grade is derived mechanically from the closure evidence, never self-declared; a declared grade that doesn't match derivation is a grade-inflation finding.
- **Weakest-link propagation** — a point's effective confidence is the minimum of its own grade and the effective confidence of every upstream point. Digests and handoff packets report the initiative's weakest link, and unattended (L3) execution requires an E1-pure dependency chain.
- The status board gains a trailing **Confidence** column; grades are orthogonal to the five status glyphs.

## Learning

- **Plan archetypes** — proven decomposition skeletons (point list, edge pattern, wave shape, trap warnings, provenance) live in `references/archetypes/`; `/tackle-retro` offers extraction at initiative close, intake offers a matching skeleton as a proposal — never a silent default.
- **Retro loop** — the learning loop mines board + log into profile candidates (stored under `~/.tackle/` and `<repo>/.tackle/`), batch-confirmed, written only by `/tackle-retro`, pausable or purgeable anytime.

## Release self-lint

Four shipped-skill gates run locally in the release sweep before every tag (`references/guides/lint-spec.md`): word budget (`SKILL.md` ≤ 1100 words), exactly 11 core conventions, changelog currency, and migrate-chain currency. No CI infrastructure — the release tag is the gate.

## Execution discipline

Tackle's execution loop is hardened with rules proven against common agent failures:

- **INTENT gate** — before any behavior-changing edit, the agent must write `INTENT: current code does X; done-signal expects Y; source says Z` and resolve any contradiction.
- **Retry bound** — stop after 3 failed fix-verify cycles on the same issue.
- **Two-halves verification** — every done-signal must check both the target criterion and the surrounding system (build/tests/lint).
- **Triviality gate** — a task is trivial only if it is one file, <10 changed lines, no new behavior, and no searching.
- **Authority order** — user > spec > tests > current code, at every gate including None; a check that contradicts the spec is surfaced, never silently satisfied.
- **Failure-modes catalog** — `references/failure-modes.md` maps common failures to the Tackle rule that prevents them.
- **Model-bound teams** — point teams bind roles to abstract model tiers resolved by the workspace §Model map; Full-gate points close with closure reports and sign-off, and one persistent Coordinator carries continuity.

## Verification and judge

- `/tackle-verify` is a pre-execution red-team pass over the plan — including the edge audit above.
- `/tackle-judge` is a post-completion adversarial audit: it treats the agent's report as claims, diffs what actually changed, re-runs claimed verifications, hunts weakened tests and false completion, and delivers a verdict of **VERIFIED**, **VERIFIED WITH CAVEATS**, or **REFUTED**.
- `/tackle-judge suite <target>` runs the trap suite in `eval/scenarios/` against a skill, model, or prompt.

## Eval

Tackle ships a manual A/B eval in `eval/`: **15 trap scenarios** (`s1`–`s15`), each pitting a mid-tier model following Tackle literally against the same model free-styling at a known agent failure. The registry and workflow live in `eval/README.md`; each scenario carries its own `GROUND-TRUTH.md` answer sheet.

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

**Updates:** the skill checks for a new release once a day during planning intake and self-updates (only `SKILL.md` + `references/` are touched); `/tackle-update` forces a check. If your harness can't reload skills, restart the session after an update.

The install artifact is `SKILL.md` + `references/` only. `docs/plans/` (workspaces) and `docs/seeds/` (this project's backlog) are local to this repo and never ship with the skill; your own plans and seeds get the same gitignore treatment in your repo.

## How to use

Trigger words: `plan de acción`, `armar un plan`, `plan this out`, `tackle this`, `iniciativa`.

| You say | Mode |
|---|---|
| `/tackle-init [preset]` | **Init** — create the plan-local customization tree (`presets/`, `overrides/`) |
| `/tackle-constitution` | **Constitution** — establish project principles |
| `/tackle-specify` | **Specify** — write the product spec |
| `/tackle-plan` | **Plan** — build the full decomposed plan (standalone default) |
| `/tackle-plan` + "implement it", or "tackle this and implement it" | **Plan + Execute** — build the plan, then run execution |
| `/tackle-tasks` | **Tasks** — flatten the plan into a checklist |
| `/tackle-implement` | **Implement** — execute the plan point-by-point |
| `/tackle-next` | **Execute next** — execute one ready point |
| `/tackle-checklist` | **Checklist** — generate a quality checklist |
| `/tackle-verify` | **Verify** — red-team pass over each point before implementation |
| `/tackle-judge` | **Judge** — adversarial verification of finished work |
| `/tackle-judge suite <target>` | **Judge suite** — run the trap suite against a skill, model, or prompt |
| `/tackle-ground` | **Ground** — mechanically read and mark every `file:line` cited in the plan |
| `/tackle-retro` | **Retro** — mine board + log into the retro artifact; batch-confirmed profile writes and plan-archetype extraction |
| `/tackle-pulse` | **Pulse** — read-only standing digest for schedulers; never executes points |
| `/tackle-drill` | **Drill** — cold-start readiness drill on one point briefing |
| `/tackle-trace` | **Trace** — criterion↔point coverage matrix, gaps and drift |
| `/tackle-handoff` | **Handoff packet** — generate a portable handoff artifact |
| `stop evolving` | **Evolution opt-out** — pause or purge the learning-loop profile |
| "resume / retomá `<x>`" | **Resume** — re-enter a plan |
| "how is `<x>` going?" / "status" | **Status** — read-only digest |
| "what plans are there?" | **List** — one line per initiative |
| "what's next?" / "qué sigue" | **Next** — the next point's pre-attack summary |
| "migrate / upgrade `<x>`" | **Migrate** — bring an old plan to the current methodology (checklist chain v2.0 → v4.0 in `references/guides/migrate.md`) |
| "mejorá este plan" / "improve this plan" | **Improve** — upgrade a Tackle plan or convert an unstructured plan |

**The Create pipeline:** Intake → Gate (None/Lite/Full) → Location & gitignore → Scaffold → Briefing → Architecture → Stabilize contract → Decompose → Lint → Handoff.

**Execution:** `/tackle-implement` reads the board, picks the next ready point in dependency order, runs its done-signal, and updates board + log. Team sizing is Solo/Pair/Pod/Squad, with roles bound to model tiers (`fast`/`standard`/`frontier`) resolved by the workspace §Model map; Full-gate points close with a closure report under `reports/` plus sign-off; one persistent Coordinator keeps continuity.

**Template-resolution stack:** overrides → presets → sdd → core.

**Version:** Tackle 4.0.0. See `references/CHANGELOG.md` for what's new.

## What it produces

All artifacts are `.md` files under `docs/plans/<initiative>/`:

| Artifact | Purpose |
|---|---|
| `README` | Human index, reading order |
| `AGENTS` | Operating contract for any agent that picks up the plan |
| `plan` | Objective, non-goals, point decomposition + dependency graph |
| `board` | Canonical status board for execution (🔴🟡⏸🟢⚪ plus a trailing **Confidence** column carrying the derived evidence grade; do not duplicate status in the plan) |
| `log` | Append-only session log (canonical state) |
| `todo` | Planning-readiness checklist |
| `questions` | Single source of open questions |
| `decisions` | Closed decisions register |
| `retro` | Initiative retrospective artifact (created by `/tackle-retro`) |
| `HANDOFF` | Portable handoff packet (created by `/tackle-handoff`) |
| `points/P-0N-*` | One self-contained briefing per point |

Full-gate plans also produce, only when each trigger fires: `foundations` (non-trivial architecture), `design-contract` (shared surface points conform to), `execution-strategy` + `team` (multi-agent execution), `reference-docs/` (external snapshots), `coordinator` (Coordinator continuity projection; generated, never canonical), `reports/` (per-point closure reports with sign-off).

## Model-agnostic

Works with GPT, Claude Opus/Sonnet, Cursor Composer, Kimi, DeepSeek, or any agent that can read markdown and search code. No vendor-specific tools assumed.

## Optional companions

- [superpowers](https://github.com/obra/superpowers) — for `brainstorming` / `writing-plans` depth
- [karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) — for simplicity-first discipline
- [solid-skills](https://github.com/ramziddin/solid-skills) — for architecture / SOLID decisions

## License

MIT
