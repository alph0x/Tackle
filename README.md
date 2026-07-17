# Tackle

A model-agnostic planning skill that turns an initiative into a durable action plan, broken into self-contained points that can be attacked across different sessions and agents — and can execute that plan point-by-point when you ask it to.

## What it does

Tackle produces a workspace of grounded markdown artifacts under `docs/plans/<initiative>/` in your repository. Each point's `.md` carries all the info needed to resolve it in a fresh session — context, approach, recommended prompt, and alternatives.

**Tackle plans and can execute the plan it produces.** It never writes implementation code on its own. The optional `/tackle-implement` and `/tackle-next` modes drive execution by spawning the point team defined in `team.md`, running each point's done-signal, and advancing the board.

## Execution discipline

Tackle's execution loop is hardened with rules proven against common agent failures:

- **INTENT gate** — before any behavior-changing edit, the agent must write `INTENT: current code does X; done-signal expects Y; source says Z` and resolve any contradiction.
- **Retry bound** — stop after 3 failed fix-verify cycles on the same issue.
- **Two-halves verification** — every done-signal must check both the target criterion and the surrounding system (build/tests/lint).
- **Triviality gate** — a task is trivial only if it is one file, <10 changed lines, no new behavior, and no searching.
- **Failure-modes catalog** — `references/failure-modes.md` maps common failures to the Tackle rule that prevents them.
- **Model-bound teams** — point teams bind roles to abstract model tiers resolved by the workspace §Model map; Full-gate points close with closure reports and sign-off, and one persistent Coordinator carries continuity in `coordinator.md`.

## Verification and judge

- `/tackle-verify` is a pre-execution red-team pass over the plan.
- `/tackle-judge` is a post-completion adversarial audit: it treats the agent's report as claims, diffs what actually changed, re-runs claimed verifications, hunts weakened tests and false completion, and delivers a verdict of **VERIFIED**, **VERIFIED WITH CAVEATS**, or **REFUTED**.
- `/tackle-judge suite <target>` runs the trap suite in `eval/scenarios/` against a skill, model, or prompt.

## Eval

Tackle ships a smoke-test A/B eval in `eval/`:

- `eval/README.md` describes the manual workflow.
- `eval/scenarios/` contains trap fixtures with `GROUND-TRUTH.md` answer sheets.
- Each scenario tests whether a mid-tier model following Tackle literally beats the same model free-styling at a trap.
- Current scenarios:
  - `s1-assessment-trap/` — question-shaped ask; the trap is editing files instead of diagnosing.
  - `s2-surprise-trap/` — spec-vs-test conflict; the trap is silently editing correct code to satisfy a wrong test.
  - `s3-intake-trap/` — vague planning ask; the trap is decomposing a full plan before asking one pointed question.
  - `s4-gate-trap/` — one-line copy fix; the trap is Full-gate ceremony for a None-gate task.
  - `s5-consent-trap/` — bare plan-shaped ask; the trap is implementing the plan instead of stopping at handoff to ask before executing.
  - `s6-profile-trap/` — retro-time profile candidates; the trap is writing profile files without an explicit batched user confirmation.
  - `s7-grounding-trap/` — stale ground log; the trap is executing the next point without re-grounding first.

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
| `/tackle-judge` | **Judge** — adversarial verification of finished work |
| `/tackle-judge suite <target>` | **Judge suite** — run the trap suite against a skill, model, or prompt |
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

**Execution:** `/tackle-implement` reads `board.md`, picks the next ready point in dependency order, runs its done-signal, and updates `board.md` + `log.md`. Team sizing is Solo/Pair/Pod/Squad per `team.md`. The learning loop stores profiles at `~/.tackle/user-profile.md` and `<repo>/.tackle/profile.md`.

**Template-resolution stack:** overrides → presets → sdd → core.

**Version:** Tackle 3.3.0. See `references/CHANGELOG.md` for what's new.

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
| `retro.md` | Initiative retrospective artifact (created by `/tackle-retro`) |
| `HANDOFF.md` | Portable handoff packet (created by `/tackle-handoff`) |
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
