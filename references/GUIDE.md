# Tackle 2.0 — Full methodology guide

This is the detailed companion to `SKILL.md`. `SKILL.md` is the index; this guide contains the Step-by-Step methodology, design rules, and advanced modes.

## When to use Tackle

Use when starting a non-trivial, multi-session or multi-track initiative (Jira ticket, feature, refactor, investigation, bug with unknowns) that needs a durable action plan broken into self-contained points, before writing implementation code. Also use for resume, status, list, next, migrate, and improve modes.

## Language

All workspace artifacts are written in **English**, regardless of the conversation language.

## Step 1 — Intake (infer first, then ask)

Understand the user's intent. Extract or confirm:
- Problem
- Observable result expected
- Top 2 non-goals
- Highest-shape decision

Do not assume; ground claims in `file:line`.

## Step 1.5 — Anchor the intake before sizing

Lock the problem, observable result, top 2 non-goals, and highest-shape decision before choosing a gate.

## Step 2 — Gate sizing (Full / Lite / None)

| Gate | Use for | Example |
|---|---|---|
| **None** | One-session, one-file, no handoff | add a constant, rename a local |
| **Lite** | Single-session, bounded scope, few unknowns | add one validation to an existing endpoint |
| **Full** | Multi-session / multi-track / multi-team / high uncertainty / handoff expected | introduce a new subsystem |

**Tie-breaker**: touches ≥2 modules OR changes public API OR spans sessions/teams OR handoff expected → **Full**.

## Step 3 — Location & gitignore

Create `docs/plans/<initiative>/`. Ask the user if the plans directory should be gitignored. If yes, add `docs/plans/` to `.gitignore`.

## Step 4 — Scaffold the core

Copy templates from `references/` and fill `{{PLACEHOLDERS}}`. Delete unused sections. Never leave empty slots you won't fill.

Depth artifacts (create only when their trigger fires):
- `foundations.md` — grounding table (decision → principle → source).
- `design-contract.md` — authoritative public surface points implement.
- `execution-strategy.md` — waves + quality gate + deferral.
- `team.md` — execution team roles and protocol.
- `board.md` — canonical status board for execution.
- `reference-docs/` — read-only external snapshots.

## Step 5 — Briefing (ground in `file:line`)

For each point, write:
- Goal (single responsibility)
- Depends-on / Touches
- Context grounded in code
- Recommended approach
- Alternatives
- Done-signal (runnable command)
- Acceptance criteria

## Step 5.5 — Architecture recommendation

If Full, recommend an architecture. Record the decision as `D-xx` in `decisions.md`. Open `foundations.md` with the Clean Code + SOLID backbone.

## Step 5.75 — Stabilize the design contract (Full only)

Do not write point briefings until `design-contract.md` survives one full planning session unchanged. Points cite contract sections instead of inlining spec.

## Step 6 — Decompose into loop-runnable points

- Skeleton board first: P-0N / What / Depends-on / Touches / done-signal.
- Then flesh out point briefings.
- Cut for parallelism; minimize dependency depth.
- One point = smallest change with ONE runnable done-signal.

## Step 6.5 — Lint the wired plan

Check:
- Pipeline wired (every `Depends-on` resolves).
- Contract churn guard (contract sections changed → citing points reconciled).
- Quality dimensions derived into done-signals.
- Deferral & questions sound.
- Q-guard (active point may not depend on unresolved user-owned `Q-xx`).
- Depth artifacts coherent.
- Plan passes the lint.

## Step 7 — Handoff

Present the plan in chat with the output contract:
1. Status line.
2. Digest ≤ 12 lines.
3. Action footer: `⚠️ On you: ...` and `▶ Continue: ...`.

## Step 8 — Resume

Re-enter an existing plan. Read `AGENTS.md` → last `log.md` entry → `decisions.md` → `questions.md` → relevant `points/P-0N.md` → depth artifacts if they exist.

Open with a digest and re-ask user-owned open `Q-xx` directly in chat.

## Step 8.5 — Migrate

Bring an old plan to the current methodology:
1. Detect the gap (trust structure, not just the stamp).
2. Preserve what's settled.
3. Scope to forward-looking work.
4. Re-ground remaining points.
5. Add missing artifacts.
6. Lint + checkpoint.
7. Record migration `D-xx` + log entry + bump stamp.

## Step 9 — Status / List / Next

- **Status**: read-only digest from `board.md` + last log snapshot.
- **List**: scan `docs/plans/*/`; one line each.
- **Next**: print the next ready point's pre-attack summary + ready-to-paste prompt.

## Step 10 — Improve / upgrade

Triggered by `improve this plan` / `tackle-upgrade <initiative>`.

### 10.1 Detect the source

| What is there | Mode | Action |
|---|---|---|
| Tackle workspace with intact core structure | **Mode A** | Diff methodology, apply non-breaking changes, re-lint, bump stamp. |
| Old Tackle / pre-Tackle structure | **Mode A'** | Run Step 8.5 first, then Mode A. |
| Unstructured source | **Mode B** | Ingest, infer, extract decisions/questions, create workspace. |
| Nothing / empty path | **Stop** | Ask for the source. |

### 10.2 Stop conditions

- Source already in execution → Resume + migrate board hygiene only.
- Source is archaeological → recommend fresh **Create**.
- Source is wrong, not old → **Create** with preserved decisions.

## Step 11 — Versioning and release notes

Record methodology changes in `references/CHANGELOG.md`:

```
## Tackle 2.0
- SDD phase entry points: `/tackle-init`, `/tackle-constitution`, `/tackle-specify`, `/tackle-tasks`, `/tackle-implement`, `/tackle-next`, `/tackle-checklist`.
- Plan execution: `/tackle-implement` and `/tackle-next` run points point-by-point.
- Template-resolution stack: overrides > presets > sdd > core.
- Visible plan-local customization: `presets/` and `overrides/` inside `docs/plans/<initiative>/`.
- New depth artifacts: `team.md` and `board.md`.
```

## Decision ownership — the user decides every doubt

Tackle assumes nothing. Every doubt goes to the user as a decision with a recommended default. Batch doubts; don't drip-feed. Tag each as 🔴 blocking or 🟡 proceed-on-default. Under delegation, every mandatory choice becomes a provisional `Q-xx` with your default.

## Quality-dimensions catalog

Each fired axis (security, performance, concurrency, correctness, data-integrity, a11y, i18n, observability) becomes a runnable done-signal fragment or a review-gate. Initiative-wide axes live in `plan.md` §6.1.

## Conventions summary

1. Log append-only.
2. Questions in `questions.md`; decisions in `decisions.md`.
3. Canonical state = last `log.md`; execution status = `board.md`.
4. Ground every claim in `file:line`.
5. No new files without reason.
6. Don't touch out-of-scope.
7. Verification = done-signal + `plan.md` §6.1.
8. Contract supersede-first.
9. Grounding before merge.
10. Self-documenting code.
11. Status vocabulary: 🔴 🟡 ⏸ 🟢.
12. Single-source per-point acceptance.
13. Quality loop before flipping 🟢.
14. Decisions carry their why; questions carry what they determine.
