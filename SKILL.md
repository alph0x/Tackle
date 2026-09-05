---
name: tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative needing a durable action plan of self-contained points, before writing implementation code. Also use when resuming, checking status, listing plans, getting the next point, or migrating an old plan. Also use to verify or red-team a plan before implementation, to judge finished work adversarially, or to run a retro at initiative close.
---

# Tackle

## Overview

**Tackle 7.2.1** — model-agnostic planning/execution methodology: durable plans under `docs/plans/<initiative>/`, self-contained points that survive handoffs; runs in the target repo, grounds every claim in `file:line`. Eight public commands — **init, plan, verify, next, run, judge, status, retro** — each also reachable by its canonical natural-language trigger.

- Ordinary Tackle invocation performs no network access or installation-tree mutation. Updates are
  owner-controlled and out-of-band; use `references/guides/update.md` only when the owner explicitly
  requests update guidance.
- Plans by default; executes only when explicitly asked.
- Workspace artifacts are in English.

## Routing

| The user says (any language) | Mode |
|---|---|
| `start this / initialize` or `/tackle-init <name>` | **Init** → create the workspace (9 core artifacts + `points/`) |
| `plan this / armar un plan` or `/tackle-plan` | **Plan** → Steps 1–7; intake may instantiate optional `spec.md`/`constitution.md` |
| `/tackle-plan` + explicit execute | **Plan + Execute** → Steps 1–7, then run execution |
| `/tackle-verify` | **Verify** → grounding (step 0: the two-phase citation/mtime check), coverage matrix, then the red-team pass |
| `give me the next point / qué sigue` or `/tackle-next` | **Next** → select the next ready point; pre-attack summary + starting prompt; never executes |
| `/tackle-run` | **Run** → execute all ready points in dependency order |
| `/tackle-run --one` / `/tackle-run <P-id>` | **Run one** → execute a single ready point |
| `/tackle-judge` | **Judge** → adversarial check of finished work |
| `/tackle-judge suite <target>` | **Judge suite** → trap suite vs skill/model/prompt |
| `status / how is <x> going?` or `/tackle-status [<ws>]` | **Status** → read-only digest (Step 9); `--handoff` writes `HANDOFF.md` |
| `what plans are there?` | **List** → one line per initiative |
| `resume / retomá <x>` | **Resume** → re-enter a plan (read-first) |
| `migrate / upgrade <x>` | **Migrate** → bring an old plan to the current methodology (checklist chain v2.0 → v7.2 in `references/guides/migrate.md`) |
| `stop evolving` | **Evolution opt-out** → pause/purge learning-loop profile, per scope (inside retro) |
| `/tackle-retro` | **Retro** → mine `board.md` + `log.md` into `retro.md` |

**Guide map** (`references/guides/`): 0–2 `intake-and-gate` · 3–4 `scaffold` · 5–5.75 `design-and-contract` · 6–6.6 `decompose-and-lint` · 7 `verify` · 8.5 `migrate` · 9 `status` · retro `retro` · judge `judge` · update `update` (internal). Natural-language triggers are canonical; slash commands are aliases.

**Commands are entry points, not boundaries** — internal invocation never bypasses guardrails (`intake-and-gate.md`).

## Execution loop

`/tackle-run` and `/tackle-next` use the `team.md` point team (mandatory) and follow `board.md` in dependency order. `/tackle-next` only **selects and prepares**: it picks the next executable point, checks grounding freshness with the two-phase citation/mtime procedure in `references/guides/verify.md`, and emits the pre-attack summary + starting prompt for the user's consent — it never changes code. `/tackle-run` executes: all ready points in dependency order (`run`), one point (`run --one` or `run <P-id>`). Read-first: `board.md`, `log.md`, `decisions.md` (`questions.md` if unresolved) before acting; cold-session modes (`status`, resume, list, next, verify) follow the same rule. Team sizes/tiers/efforts: `team.tmpl.md` + `AGENTS.md` §Model map (plan proposes default tiers by complexity/risk; the user confirms in the intake batch).

- **Maker/checker** — Driver's run informative, not gating; flip needs an independent checker (`team.tmpl.md` §Done-conditions).
- **Closure report** — Full-gate closes via `reports/P-0N-report.md`; Coordinator sign-off gates the flip; grade from section-4 evidence (`team.tmpl.md` §Closure report).
- **Regression sweep** — re-run done-signals of 🟢 points with intersecting Touches before a flip; failure reopens and blocks (`team.tmpl.md` step 9).
- **Explicit intent** — no upfront plan+execute ask → pre-attack summary + ask before changing code; silence/ambiguity means stop; default L2 (`AGENTS.md` §Autonomy).
- **Usage ledger** — every role run appends one `usage.md` row (model, tier, effort, tokens as the harness exposes them; `n/a`, never estimated); retro mines it for cost; recording is informative, never gating.
- **Lifecycle ledger** — append `start` before substantive role work and one honest `finish` or `observe-incomplete` observation at close; never infer a successful end or duration from a missing close. Usage never gates point closure.

Subagents are optional in planning for grounding/verify/drill; intake, doubts, decisions never delegate.

Planning is self-contained: intake, simplicity, and architecture guidance live in `references/guides/` and the templates — no external planning skills required.

## Core conventions

1. **Log append-only** — one entry per session; never rewrite history.
2. **Questions only in `questions.md`**; **decisions only in `decisions.md`**.
3. **Ground every claim in `file:line`** — a point is **ungrounded** until every citation passes the drift check (with re-anchor) recorded by the newest ground entry in `log.md`; ungrounded points can't be ready or executed.
4. **One point = one responsibility + one runnable done-signal**.
5. **Contract supersede-first**: implement `design-contract.md` as written; deviations require a `D-xx` first.
6. **Self-documenting code**: Clean Code + SOLID; no explanatory inline comments.
7. **Status vocabulary**: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done · ⚪ skipped.
8. **Decision ownership** — the user decides every doubt; batch recommendations with defaults.
9. **Scaffold asks gitignore** — `/tackle-plan` asks about `.gitignore` for `docs/plans/` before creating files; records the decision.
10. **Harness-agnostic** — works with any agent/LLM and IDE harness; never assume a specific one. Use generic terms ("the agent", "your harness", "the most capable model available"); single-harness features belong outside Tackle.
11. **Authority order** — user > spec > tests > current code, at every gate including None. A check that contradicts the spec is surfaced, never silently satisfied.

## Output contract

Open with one status line; close with `⚠️ On you: ...` and `▶ Continue: ...`. Digest ≤ 12 lines; handoff ≤ one screen. Point to files, don't paste.
Terse by default; say it fully for security warnings, irreversible actions, or anywhere compression risks misread.

## Where the detail lives

`references/guides/` (per-step guides) · `AGENTS.tmpl.md` (workspace contract) · `team.tmpl.md` (teams) · `*.tmpl.md` (templates).
