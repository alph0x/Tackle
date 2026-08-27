# Tackle

A model-agnostic planning and execution skill that turns an initiative into a durable action plan — self-contained points a cold agent can resolve in a fresh session — and executes that plan point-by-point when you ask it to.

**Tackle 7.0: surface consolidation.** Tackle cuts its public surface to eight commands — **init, plan, verify, next, run, judge, status, retro** — and its workspace core to nine artifacts, with a hard rename (no aliases), a v6.1→v7.0 migration, a realigned eval suite (46 scenarios), and two live runner defects fixed (`scaffold_core` unbound variable; `init --check` false-green on a missing workspace). The repository-local runner gates workspaces with rows 1–15 plus its done-signal executor; the install artifact remains Markdown-only.

## What it does

Tackle produces a workspace of grounded markdown artifacts under `docs/plans/<initiative>/` in your repository. Each point briefing carries everything needed to resolve it cold — context, approach, recommended prompt, and alternatives.

**Tackle plans and can execute the plan it produces.** It never writes implementation code on its own. `/tackle-run` and `/tackle-next` drive execution by spawning the point team defined in the workspace's team roster, running each point's done-signal, and advancing the board. `/tackle-next` only selects and prepares (pre-attack summary + starting prompt); `/tackle-run` executes (all ready points, or one via `run --one` / `run <P-id>`).

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
- **Retro loop** — the learning loop mines board + log into profile candidates (stored under `~/.tackle/` and `<repo>/.tackle/`), batch-confirmed, written only by `/tackle-retro`, pausable or purgeable anytime (the `stop evolving` opt-out lives inside retro).

## Release self-lint

7 shipped-skill gates run in the release sweep before every tag (`references/guides/lint-spec.md`): word budget (`SKILL.md` ≤ 1100 words), exactly 11 core conventions, changelog currency, migrate-chain currency, README currency, artifact-manifest currency (the update channel must list exactly the files that ship), and README content claims (row count, scenario count/range, migrate-chain head, runner subcommands, gate count — every expected value derived from the files it describes). Since 5.0 the gates compose into the repository-local `tackle` runner (POSIX sh, zero deps) — the runner is not part of the installed artifact; the rows stay copy-pasteable for hosts without the runner. `tackle sweep` runs gates 1–7 plus `catalog` plus the lint rows over every workspace in one local check.

## Execution discipline

Tackle's execution loop is hardened with rules proven against common agent failures:

- **INTENT gate** — before any behavior-changing edit, the agent must write `INTENT: current code does X; done-signal expects Y; source says Z` and resolve any contradiction.
- **Retry bound** — stop after 3 failed fix-verify cycles on the same issue.
- **Two-halves verification** — every done-signal must check both the target criterion and the surrounding system (build/tests/lint).
- **Triviality gate** — a task is trivial only if it is one file, <10 changed lines, no new behavior, and no searching.
- **Authority order** — user > spec > tests > current code, at every gate including None; a check that contradicts the spec is surfaced, never silently satisfied.
- **Failure-modes catalog** — `references/failure-modes.md` maps common failures to the Tackle rule that prevents them.
- **Model-bound teams** — point teams bind roles to abstract model tiers resolved by the workspace §Model map (`plan` proposes default tiers by complexity/risk in decompose; the user confirms in the intake batch); Full-gate points close with closure reports and sign-off, and one persistent Coordinator carries continuity.
- **Double-gate flip** — a point flips only after `tackle done-signal <point>` is green AND the independent checker signs off (workspace flag `tackle-gate`; absent = off preserves the 4.x flip, `on` = default for new workspaces).

## Verification and judge

- `/tackle-verify` is a pre-execution red-team pass over the plan — including the edge audit above, the mechanical grounding step 0 (`tackle probe` + `tackle ground`), the criterion↔point coverage matrix, and an optional cold-resolvability probe.
- `/tackle-judge` is a post-completion adversarial audit: it treats the agent's report as claims, diffs what actually changed, re-runs claimed verifications, hunts weakened tests and false completion, and delivers a verdict of **VERIFIED**, **VERIFIED WITH CAVEATS**, or **REFUTED**.
- `/tackle-judge suite <target>` runs the trap suite in `eval/scenarios/` against a skill, model, or prompt.

## Mental model

```
INIT → PLAN → VERIFY → (NEXT | RUN) → JUDGE → STATUS → RETRO
```

`INIT` creates the workspace; `PLAN` decomposes (intake may instantiate optional `spec.md`/`constitution.md`); `VERIFY` red-teams + grounds; `NEXT` selects/prepares the next point (read-only); `RUN` executes; `JUDGE` adversarially audits; `STATUS` is the read-only digest (list/resume/handoff); `RETRO` mines the loop and the opt-out.

## Eval

Tackle uses a repository-local runner-assisted A/B eval in `eval/`: **46 scenarios** (`s1`–`s49`) — decision traps pitting a mid-tier model following Tackle literally against the same model free-styling at a known agent failure, plus one end-to-end lifecycle smoke (`s25-e2e-lifecycle`, the full intake → plan → execute → close → retro chain). The registry and workflow live in `eval/README.md`; `tackle eval` mechanizes staging/diff/audit/judge-packing (the answer sheet never reaches an arm), each scenario carries its own `GROUND-TRUTH.md` answer sheet, and `tackle catalog` verifies scenarios ⊆ registry plus fixture-integrity so the list can't drift.

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
mkdir -p ~/.claude/skills/tackle
cp SKILL.md ~/.claude/skills/tackle/
cp -r references ~/.claude/skills/tackle/
```

**Cursor / other:**
```bash
mkdir -p ~/.cursor/skills/tackle
cp SKILL.md ~/.cursor/skills/tackle/
cp -r references ~/.cursor/skills/tackle/
```

**Any model / IDE:**
Copy only `SKILL.md` and the `references/` directory into your agent's skill directory. The repository-local `tackle` runner is not installed with the skill.

**Updates:** the installed Markdown artifact self-checks for a new release once a day on any invocation and self-updates (`SKILL.md` + `references/` are replaced); to force a check, delete `~/.tackle/last-update-check` and invoke Tackle again. If your harness can't reload skills, restart the session after an update.

The install artifact is `SKILL.md` + `references/` only. The repository-local `tackle` runner remains available for maintainers' release checks; `docs/plans/` (workspaces) and `docs/seeds/` (this project's backlog) are local to this repo and never ship with the skill; your own plans and seeds get the same gitignore treatment in your repo.

## How to use

Trigger words: `plan de acción`, `armar un plan`, `plan this out`, `tackle this`, `iniciativa`.

| You say | Mode |
|---|---|
| `start this / initialize` or `/tackle-init <name>` | **Init** — create the workspace (9 core artifacts + `points/`) |
| `plan this / armar un plan` or `/tackle-plan` | **Plan** — build the full decomposed plan; intake may instantiate optional `spec.md`/`constitution.md` |
| `/tackle-plan` + "implement it", or "tackle this and implement it" | **Plan + Execute** — build the plan, then run execution |
| `/tackle-verify` | **Verify** — grounding (step 0), coverage matrix, red-team pass before implementation |
| `give me the next point / qué sigue` or `/tackle-next` | **Next** — select the next ready point; pre-attack summary + starting prompt; never executes |
| `/tackle-run` | **Run** — execute all ready points in dependency order |
| `/tackle-run --one` / `/tackle-run <P-id>` | **Run one** — execute a single ready point |
| `/tackle-judge` | **Judge** — adversarial verification of finished work |
| `/tackle-judge suite <target>` | **Judge suite** — run the trap suite against a skill, model, or prompt |
| `status / how is <x> going?` or `/tackle-status [<ws>]` | **Status** — read-only digest; `--handoff` writes a portable `HANDOFF.md`; detects an old Methodology stamp and offers migrate |
| `what plans are there?` | **List** — one line per initiative |
| `resume / retomá <x>` | **Resume** — re-enter a plan (read-first) |
| `migrate / upgrade <x>` | **Migrate** — bring an old plan to the current methodology (checklist chain v2.0 → v7.0 in `references/guides/migrate.md`) |
| `stop evolving` | **Evolution opt-out** — pause/purge the learning-loop profile, per scope (inside retro) |
| `/tackle-retro` | **Retro** — mine board + log into the retro artifact; batch-confirmed profile writes and plan-archetype extraction |
| `tackle` (repository-local) | **Mechanical gate** — POSIX-sh runner for maintainers: `lint <workspace>` (15 lint rows), `catalog` (eval scenarios ⊆ registry + fixture-integrity), `done-signal <point>` (run the point's exit-gate), `probe <workspace>` (cited-file staleness vs newest `Last-verified`), `ground <workspace>` (re-anchor drifted citations), `eval` (`prepare`/`diff`/`audit`/`judge`/`verdict` — stage, diff, audit, and judge-pack a trap run; never scores), `init <ws>` + `init --check` (create / verify a workspace), `sweep` (release sweep: gates 1–7 + catalog + workspace lint); flip requires its green when the workspace flag `tackle-gate: on` |

**The Create pipeline:** Intake → Gate (None/Lite/Full) → Location & gitignore → Scaffold → Briefing → Architecture → Stabilize contract → Decompose → Lint → Handoff.

**Execution:** `/tackle-run` reads the board, picks the next ready point in dependency order, runs its done-signal, and updates board + log. Team sizing is Solo/Pair/Pod/Squad, with roles bound to model tiers (`fast`/`standard`/`frontier`) resolved by the workspace §Model map (`plan` proposes defaults by complexity/risk, user confirms in intake); Full-gate points close with a closure report under `reports/` plus sign-off; one persistent Coordinator keeps continuity.

**Version:** Tackle 7.0.0. See `references/CHANGELOG.md` for what's new.

## What it produces

All artifacts are `.md` files under `docs/plans/<initiative>/`:

| Artifact | Purpose |
|---|---|
| `README` | Human index, reading order |
| `AGENTS` | Operating contract for any agent that picks up the plan |
| `plan` | Objective, non-goals, point decomposition + dependency graph |
| `board` | Canonical status board for execution (🔴🟡⏸🟢⚪ plus a trailing **Confidence** column carrying the derived evidence grade; references `plan.md` §5 for the graph — never copies it) |
| `log` | Append-only session log (canonical state) |
| `usage` | Token/model/effort ledger — one row per role run, as the harness exposes them (`n/a`, never estimated); mined by the retro's cost analysis (born ≥ 5.2) |
| `questions` | Single source of open questions |
| `decisions` | Closed decisions register |
| `retro` | Initiative retrospective artifact (created by `/tackle-retro`) |
| `HANDOFF` | Portable handoff packet (created by `/tackle-status <ws> --handoff`) |
| `points/P-0N-*` | One self-contained briefing per point |

Full-gate plans also produce, only when each trigger fires: `foundations` (non-trivial architecture), `design-contract` (shared surface points conform to), `team` (multi-agent execution, incl. §Wave gates), `reference-docs/` (external snapshots), `coordinator` (Coordinator continuity projection; generated, never canonical), `reports/` (per-point closure reports with sign-off). Optional intake artifacts: `spec` / `constitution` (instantiated by `plan` when the user brings formal material).

## Model-agnostic

Works with GPT, Claude Opus/Sonnet, Cursor Composer, Kimi, DeepSeek, or any agent that can read markdown and search code. No vendor-specific tools assumed. Planning is self-contained — no external planning skills are required, recommended, or checked for (adopted in 5.1.0).

## License

MIT
