---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative (Jira ticket, feature, refactor, investigation, bug with unknowns) that needs a durable action plan broken into self-contained points, before writing implementation code. Triggers include "plan de acción", "armá/armar un plan", "plan this out", "tackle this", "iniciativa". Also use when resuming such an initiative from an existing plan folder under docs/plans/, or when asked how an existing initiative is going ("cómo viene", "status", "seguimiento", progress check), which initiatives exist ("qué planes hay"), or what the next point to work on is ("qué sigue").
---

# Tackle

## Overview

Tackle turns an initiative into a **durable action plan**, broken into self-contained **points** that can be attacked across different sessions and agents. It produces a workspace of grounded markdown artifacts under `docs/plans/<initiative>/` that survives session and agent handoffs.

**Scope — Tackle PLANS, it does NOT execute.** It stops at "everything is ready to be tackled". It does not write implementation code. Each point's `.md` must carry *all* the info needed to resolve that point in a fresh session — context, approach, recommended prompt, and alternatives. Execution happens later, in separate sessions, using those point briefings.

**Runs on the codebase.** Tackle is designed to run from inside the target repository. If you are not inside a repo, stop and ask for the codebase path before proceeding. Once confirmed, ground every claim in real `file:line`.

**Model- and harness-agnostic.** Works with any agent, model or IDE (GPT, Claude Opus/Sonnet, Cursor Composer, Kimi, DeepSeek, …). Follows the open Agent Skills format (this `SKILL.md` + `references/`). Instructions name *capabilities*, not vendor tools: use whatever **code search** (grep/ripgrep, IDE search, LSP), **go-to-definition / find-references**, **file read/write**, and **ask-the-user** facilities your environment provides. Anything your environment lacks, do by hand. Other skills mentioned below are **optional aids** — use them only if present.

**Language:** all workspace artifacts are written in **English**, regardless of the conversation language.

**Routing — what the user says → what runs:**

| The user says (any language) | Mode |
|---|---|
| "tackle this" / "plan de acción" / new initiative | **Create** → Steps 1–7 |
| "resume / retomá `<initiative>`" — keep planning | **Resume** → Step 8 |
| "how is `<initiative>` going?" / "status" / "seguimiento" | **Status** → Step 9 |
| "what plans are there?" / "qué iniciativas hay" | **List** → Step 9 |
| "give me the next point" / "qué sigue" | **Next** → Step 9 |

If the initiative is ambiguous (several under `docs/plans/`), show the List and ask which.

## Output contract (chat = signal; files = depth)

Applies to every Tackle chat response that presents a plan or its state (Create/Resume/Status/List/Next). A **None**-gate inline answer or a one-line clarification is exempt from the full status-line/footer — keep those terse. The user must never have to dig through prose to learn whether action is needed:

1. **Open with one status line**: `🟢 on track — nothing on you` · `🟡 needs your input` · `🔴 blocked`.
2. **Close with the action footer** — the only two questions the user actually has:
   ```
   ⚠️ On you: <what only the user can decide/do, with answer options ready> — or "✅ nothing on you"
   ▶ Continue: <ONE literal next thing to say — e.g. say "next" and I'll print P-04's prompt>
   ```
3. **Hard caps**: digest ≤ 12 lines; handoff ≤ one screen. Don't paste file contents into chat — point to them.
4. **Group blockers by owner — you / other teams / me — in that order.** The user's first question is "is it on me?".
5. **One recommended next action, singular.** Alternatives live in the files; offer them only if asked.
6. **Progressive disclosure**: compact first, then offer depth ("want the full board / the point detail?") — never dump it unprompted.

## Decision ownership — the user decides every doubt (no exceptions)

**Tackle assumes nothing.** Every doubt that surfaces while planning — scope, architecture, naming, a tradeoff, an ambiguous requirement, a gap in the codebase — goes to the user as a decision. **Recommend** (mark your pick, give options + a one-line why), but the user decides; this is the one rule with no exception. *Infer* (from branch/repo/code) to turn a question into a fast confirmation — that's not assuming, it's grounding, and you still confirm. The only time you proceed without a live answer is when the user **explicitly delegated** it ("just figure it out") or is unavailable; even then you don't bake a silent assumption — you record it as a **user-owned open `Q-xx`**, surface it, and let them overturn it later. A planning choice the user never saw is a bug.

**Cadence — batch doubts, don't drip-feed.** Surfacing every doubt does NOT mean a stream of one-off questions (that's its own failure mode). Collect the doubts a phase raises — intake, architecture, decomposition — and ask them in **ONE consolidated round** via your environment's structured-ask facility (a form), so the user clears many in one pass. Rules:
- **Every item carries a recommended default + a one-line why** — so the user can rubber-stamp ("take the defaults") or override only the ones they care about. N questions become one low-effort review, not an interrogation.
- **Tag each: 🔴 blocking** (can't proceed without it — gates the phase) vs **🟡 proceed-on-default** (you move on the recommendation now, recorded as a ⚠️ provisional `Q-xx`, confirmed later). Only the 🔴 ones stop you.
- **Lead with the few that change the plan's shape**; bundle the rest as "defaults I'll take unless you object."
- **Never drip-feed inside a phase** (ask → wait → ask → wait), and **never re-ask a closed `D-xx`** without cause.
The chat footer points to the batch as ONE action (e.g. `⚠️ On you: 3 architecture decisions — defaults marked, reply "ok" or override any`), consistent with the Output contract's single-action close.

## Step 1 — Intake (infer first, then ASK to contextualize)

**Infer before asking — turn the interrogation into a confirmation.** First detect what the environment already tells you: ticket ID from the branch name (`feature/MBTX-4488` → MBTX-4488), repo from the working directory, sibling plans under `docs/plans/`, ticket content via your issue-tracker integration if one is available. Present what you inferred as *"this is what I already know — confirm or correct"*, and ask — **one batched round, each gap with a recommended default** (Decision ownership → Cadence), not drip-fed — only the real gaps. Never silently assume what you didn't verify. Cover at least:
- **The explicit requirement** — the ask in the user's words; ticket ID / link if any.
- **Documentation** — relevant docs, specs, design notes, API/vendor docs, links, files to read.
- **Scope hints** — what's in, what's explicitly out, deadlines, target validation, related/sibling work.
- **Decision owners & external deps** — who decides open questions, which teams to ask.
- **Codebase** — confirm the repo/path Tackle is running against.

Read what they point you to. Record what was gathered in the first `log.md` entry; it feeds `plan.md` and `reference.md`.

If the intake surfaces questions that need another team, note them as draft Qs and create
`external-questions/` packets as soon as they become concrete.

**Doubts during intake → ask, don't assume** (per *Decision ownership*). Recover from the codebase what the codebase can answer; for anything it can't, raise it to the user with recommended options. The default is to ask, not to proceed.

**Only if the user explicitly delegated** ("just figure it out") or is unavailable do you proceed provisionally — and then record, per gap, a **user-owned `Q-xx`** in `questions.md`:
  1. What you provisionally chose (and the option you'd recommend they confirm).
  2. What you couldn't verify.
  3. The risk if the choice is wrong.
Mark these **provisional — awaiting user confirmation** so they're visible and overturnable; never let one harden into a silent assumption.

## Step 2 — Size the initiative (gate)

Do NOT scaffold a full workspace for everything. Pick a level:

| Level | When | Examples | Produces |
|---|---|---|---|
| **None** | Single obvious change, <~3 steps, no unknowns | typo, rename a local, bump a constant | No workspace. Just plan inline. |
| **Lite** | Single-session, bounded scope, a few unknowns | add one validation to an existing endpoint, plumb a field already wired | `plan.md` + `log.md` + `todo.md` only (`references/lite-plan.tmpl.md`) |
| **Full** | Multi-session OR multi-track OR multi-team OR high uncertainty OR handoff expected | introduce a new subsystem, multi-module refactor, feature spanning sessions | Full core + `points/` + appendices |

**Decide by the tie-breaker, not by vibe:** touches ≥2 modules OR changes the public API OR spans sessions/teams OR a handoff is expected → **Full**; confined to one file with no public surface change → **Lite**. Only when the tie-breaker genuinely doesn't settle it, start **Lite** (it upgrades cleanly by adding `README.md` / `AGENTS.md` / `reference.md` / `points/`).

**Bigger workspace ≠ better plan.** Over-sizing burns effort and buries the work in ceremony; under-sizing loses context across sessions. Match the level to the real shape — don't default to Full because it feels thorough.

**The gate scales ceremony, not principles.** *Decision ownership* (no silent assumptions — ask, recommend a default), **self-documenting code**, a **runnable done-signal**, and **rollout/reversibility if it touches production** apply at EVERY level. Only the *artifacts* are gated: `points/` + depth files are Full; Lite folds them into `plan.md` (`references/lite-plan.tmpl.md`). If **None** (inline, no workspace): still don't assume doubts, and still state the one done-signal you'll verify the change with before stopping here.

Present the level as a one-tap choice with your recommendation marked and a one-line justification (use your environment's structured-ask facility if present; plain question otherwise). Same for the gitignore 3-way in Step 3.

## Step 3 — Location & gitignore

Plans live under **`docs/plans/<initiative>/`** in the repo. Name `<initiative>` after the ticket (`MBTX-4488/`) or a slug (`error-handling/`); provisional slug if unassigned, rename later. Create `docs/plans/` if missing.

Then ASK the user how to treat plans in version control (3-way, never decide silently):
- **Ignore all plans** → add `docs/plans/` to `.gitignore`.
- **Ignore specific plans** → add `docs/plans/<initiative>/` to `.gitignore` (this plan only).
- **Ignore nothing** → commit everything (don't touch `.gitignore`).

## Step 4 — Scaffold the core (copy templates, fill placeholders)

Steps 4–6 are minutes of silent file work — **keep visible progress** (your environment's task/todo tracker if present, else one-line updates in chat: "core scaffolded → grounding → decomposing"). Don't go dark on the user.

Copy from `references/` and fill `{{PLACEHOLDERS}}`. NEVER leave empty slots you won't fill — delete unused sections.

**Core (fixed, semantic names — no forced numbering):**
- `README.md` — human index → `references/README.tmpl.md`
- `AGENTS.md` — operating contract for any agent → `references/AGENTS.tmpl.md`
- `plan.md` — objective, **non-goals**, current state, point decomposition + dependency graph (**the per-point status board**), acceptance criteria, risks → `references/plan.tmpl.md`
- `log.md` — append-only session log (**canonical state**; holds the intake) → `references/log.tmpl.md`
- `todo.md` — planning-readiness checklist per point → `references/todo.tmpl.md`
- `questions.md` — single source of open questions → `references/questions.tmpl.md`
- `decisions.md` — closed decisions register (`D-01`…), single source → `references/decisions.tmpl.md`
- `reference.md` — current code state with `file:line` (shared, cross-point map) → `references/reference.tmpl.md`
- `points/` — one self-contained `.md` per point (Full only) → `references/point.tmpl.md` (filled example: `references/EXAMPLE-point.md`)

**Optional:** `external-questions/` — packets to send to other teams → `references/external-question.tmpl.md` (create only when a question goes external). · `reference-docs/` — read-only snapshots of external material (sibling-repo source, vendor docs, diagrams, adopted rules) so the workspace is self-contained → `references/reference-docs-README.tmpl.md` (create when the plan depends on anything outside this repo; see Step 5).

**Depth artifacts (Full only — create each ONLY when its trigger fires; never by default, they're ceremony otherwise):**
- `foundations.md` — grounding table (decision → principle → source) → `references/foundations.tmpl.md`. **When:** the initiative introduces non-trivial architecture (new subsystem, layering, a set of patterns).
- `design-contract.md` (a.k.a. `api-spec.md`) — the authoritative public surface points implement → `references/design-contract.tmpl.md`. **When:** several points must agree on one shared surface (API, wire format, state machine, error taxonomy).
- `execution-strategy.md` — waves + inter-wave quality gate + deferral → `references/execution-strategy.tmpl.md`. **When:** execution will be multi-agent/parallel or phased. (Still planning, not executing — it plans the attack.)

If using superpowers for depth, also create `specs/` and `plans/` as needed (not scaffolded by
default — create them when you start using `brainstorming` / `writing-plans`).

**Appendices (free, descriptive names):** add only when needed (`error-catalog.md`, `design-strategy.md`). When you add one, update the `README.md` and `AGENTS.md` file maps.

**Reference organization for a large, multi-domain initiative:** when one `reference.md` would be a wall, split it into a **numbered, feature-sliced set** with an ordered reading path — architecture/foundation first, then one self-contained doc per domain (e.g. `00-architecture.md`, `01-foundation.md`, `02-<domain>.md`, …`NN-<domain>.md`). The numbering gives a cold agent a deterministic onboarding order; the slices map cleanly onto point cuts (a domain doc ↔ the point[s] that touch it). Use this only when the domain is genuinely broad — for a focused change, one `reference.md` is better.

## Step 5 — Briefing (ground it in the codebase)

Investigate the actual repo and fill `plan.md` / `reference.md` from it, not from assumptions:
- **Lead with the de-risking finding.** Actively hunt for the ONE verified fact that reshapes the risk profile — and put it first in `plan.md` §4. Usually it makes the work *safer/smaller* ("the old path is dormant → adoption, not hot replacement → low regression risk by construction"), but it may instead *raise* the risk ("this is the hot path for 30 targets → every change needs a parity gate") — surface it either way. Finding it is the highest-leverage move in planning; don't bury it under a generic state dump.
- **Anchor the approach to precedent.** Find the existing **house pattern** in this repo (the convention sibling modules already follow) and/or a **proven reference architecture** (in-house module, external project) this design should mirror — cite it `file:line`. Default to mirroring precedent over inventing; deviating from it is a decision (`D-xx`), not a default.
- **Objective + expected result**: observable outcome.
- **Non-goals**: explicit out-of-scope — prevents scope creep. Name the specific anti-patterns (from this codebase) you're deliberately NOT carrying over.
- **Current state**: every claim about code cites `file:line`, verified with your code-search / find-references tools — not memory.
- **Domain invariants / constraints**: consult the authoritative source for the domain (spec, domain MCP, canonical constants) if your environment has one; else use the repo's own constants and annotate. Phrase invariants so they're **structural and verifiable** (a check, not prose) — they become per-point acceptance.
- **Rollout / reversibility (if it touches a production path)**: plan how it ships safely as a first-class concern, not an afterthought — enablement flag default-off, canary target, coexistence with the old path, and the **no-op/parity check** that proves flag-off changes nothing. Record it in `plan.md` §7; make the parity check **universal acceptance** (§6.1) when the old/new paths coexist for the whole initiative, or point-level when one point owns the cutover.
- **Boundary**: `reference.md` holds facts shared by ≥2 points. Most Context in a point will simply link to `reference.md`; a point only needs unique Context when it touches code no other point touches.
- **Snapshot external dependencies into `reference-docs/` (read-only).** When the plan leans on material outside this repo — a sibling repo's source, vendor/API docs, diagrams, a prior initiative's rules or resolved external Q&A — copy it into `reference-docs/` so the workspace survives the source moving or going unavailable (Tackle's durability promise depends on this). Add a `reference-docs/README.md` (`references/reference-docs-README.tmpl.md`) with **provenance** (source · branch · date), a **never-edit/re-snapshot** rule, and an **index** (folder → contents → which point/spec uses it). `reference.md` still lists the *live* paths — prefer them when both exist; the snapshot is the fallback.

## Step 5.5 — Architecture (recommend; the user decides) — gate-appropriate

**The backbone is always Clean Code + SOLID and the best referents of software design** — grounded in `foundations.md`, never "it felt cleaner". The *shape* on top of that is a choice scaled to the gate:
- **None / Lite** → no new architecture: follow the existing structure of the file/module you're touching. Don't impose a paradigm on a bounded change.
- **Full** → **recommend** one architecture matched to the initiative (e.g. hexagonal/ports-&-adapters, layered/clean, MVVM, event-driven…), justified from what Step 5 found — and **present it as the user's choice** (one-tap structured ask: the recommendation marked, 1–2 line rationale, the realistic alternatives). The user decides; Tackle proposes. **Default the recommendation to the house pattern** you anchored to in Step 5 — deviating from precedent must earn it.

Record the chosen architecture as a `D-xx` (with its why) and open `foundations.md` with it. The point decomposition (Step 6) then follows the architecture's seams — the layers/ports/boundaries become natural point cuts.

## Step 6 — Decompose into points (the heart)

Break the initiative into **independent points** (work units) with a dependency graph in `plan.md`. IDs are zero-padded: `P-01`, `P-02`…

**Checkpoint — validate before writing briefings:** present the point table + dependency graph **in chat** and get the user's OK before writing the `points/*.md` files. Redoing a table is cheap; redoing N briefings is not. Adjust the cut on feedback, then write.

For each point write `points/P-0N-<slug>.md` from `references/point.tmpl.md` so a cold agent can resolve it **from that file alone**. Each point MUST include: Goal (single responsibility) · **Consumes / Produces / Runs-alongside / Touches** (write scope) · grounded Context (`file:line`) · Non-goals · **Recommended approach** · **Alternatives / fallbacks** · **Recommended starting prompt** · Acceptance · **Done signal** (the loop's runnable exit check) · **recovery + iteration budget** · Dependencies · linked open questions · a **Definition of Ready** self-check. A point links to deeper artifacts instead of duplicating them. Per-point execution status lives only in `plan.md` §5.

**Engineer each point as a loop (loop engineering).** Plan so execution can be a tight autonomous loop: *do → run the done-signal → green = next · red = recover → escalate if stuck*. So every point carries an explicit **done-signal command** (a pass/fail exit, no human judgment), a **recovery path + iteration budget** (self-correct a bounded number of times, then STOP and ask — Decision ownership), and explicit **Consumes/Produces** so points chain as a pipeline and independent ones run as concurrent loops. A point you can't reduce to a runnable done-signal isn't ready — sharpen it until you can.

**Point size — max granularity, one verifiable done-signal.** A point is the *smallest* change that has ONE responsibility AND ends in its own machine-checkable done-signal. Default to splitting: two small loop-runnable points beat one that bundles two concerns (smaller loops = smaller blast radius, more parallelism, cleaner recovery). **Common split that's easy to miss: a pure/port-free core vs the effectful shell around it** (functional core / imperative shell) — the pure part has its own done-signal with zero test doubles and usually no dependencies, so it's its own (often earlier, more-parallel) point. Floor: if a candidate has no done-signal you can run *without* finishing another point, merge them. Rough clock 30 min–3 h, but the responsibility + done-signal test wins over the clock.

**Decompose for parallelism — cut points so they run as concurrent loops across subagents.** The plan is a *parallelization plan*: prefer many independent points over one long chain. Minimize dependency depth; isolate a shared surface into ONE early point (e.g. the design contract) so the rest fan out against it without colliding. Each point's **Consumes/Produces** makes the graph a real pipeline; mark which run in parallel. A point that forces everything else to wait is a smell — split the bottleneck.

**Group into phases/waves when the work is staged or wide.** *Tie-breaker (like the Step-2 gate):* ≥2 points runnable in parallel, OR any quality boundary / phase line, OR multi-agent execution → use waves with a quality bar between them. Otherwise a flat ordered list is fine — don't manufacture waves. A point gated on an open `Q-xx` is **Deferred** — list it as such with the blocking question, NOT as an active point; don't plan work behind an unanswered external dependency. When execution will be multi-agent or phased, capture the waves in `execution-strategy.md` (Step 4 depth artifact).

**Fan-out across N near-identical targets** (e.g. migrate 30 white-label apps): model it as ONE parameterized point with the per-target checklist + a worked example, not N copies and not one vague point — and usually Deferred behind the "who-owns-the-cutover/cadence" question. Note the cardinality explicitly. Its *acceptance* is "the worked example passes + the checklist covers the variance axes" (verifiable now); the "all N migrated" rollup is tracked on the board, not as the point's code-acceptance.

**Define the universal per-point acceptance once** (`plan.md` §6.1): the bar EVERY point must clear. Beyond the generics (tests, grounding, contract conformance, no-regression, board hygiene), **promote the load-bearing structural invariants from `design-contract.md` / Step 5 into §6.1** — the domain-specific gates that actually catch drift (e.g. "core compiles with zero deps", "concurrency-clean under the language's strict mode", "self-documenting: no explanatory inline comments"). Each point *references* §6.1 and adds only point-specific criteria. Make those **exhaustive and mechanically verifiable** — where a finite set exists (error cases, states, endpoints), cover EVERY case (table-driven); prefer criteria a grep or a reviewer can check over aspirational prose. Never restate the §6.1 bar N times (that's drift waiting to happen).

## Step 6.5 — Validate the plan (self-consistency lint)

Once the briefings are drafted, **lint the wired plan before handoff** — catch a broken pipeline now, not mid-execution. This is a reasoning check (read what you wrote; no script, no new artifacts), distinct from the Step 6 checkpoint: that validated the *cut* with the user, this validates the *wiring*. Re-run it whenever the decomposition changes (incl. on Resume).

- **Pipeline wired** — every point's `Consumes` is satisfied by an upstream `Produces` (or by existing code in `reference.md`): no dangling input. Every `Produces` is consumed downstream or is the deliverable: no dead output (a `Produces` nobody needs usually means a missing point or an over-built one).
- **Graph is a DAG** — no dependency cycles; it topologically orders into the waves. No orphan/unreachable point (unless a deliberate parallel track).
- **Parallel-safe** — points that `Runs-alongside` in the same wave have **disjoint `Touches`** (else flag them for isolated worktrees or serialize).
- **Every point loop-ready** — passes its DoR: single responsibility, runnable done-signal + budget, no open user-owned decision inside it.
- **Deferral & questions sound** — every Deferred point names its blocking `Q-xx`; every `Q-xx` has an owner + what it Determines; no user-owned doubt left silent (Decision ownership).
- **Depth artifacts coherent** (when they exist) — `design-contract.md`: every section maps to ≥1 implementing point, every contract-implementing point cites its section; `foundations.md`: every new abstraction in the points has a grounding row.

A plan that fails the lint is **not ready to tackle**: fix it, or surface the unresolvable item (e.g. a `Q-xx` with no owner) to the user. Report the lint result in the handoff ("pipeline wired ✓, 0 orphans, 2 parallel pairs worktree-flagged").

## Step 7 — Compose with available skills (optional, planning aids only)

Detect what's installed; use it to PLAN, not execute. If absent, plan with your own judgment — these are not required:
- **superpowers** (if present) → `brainstorming` to refine a point's design, `writing-plans` to draft its step breakdown; store depth in `specs/`/`plans/` and link it from the point. (`executing-plans` / `subagent-driven-development` are for *later*, outside Tackle.)
- **karpathy-guidelines** (if present) → applies throughout (think-before-coding, simplicity, surgical changes, goal-driven).
- **solid** / `ramziddin/solid-skills` (if present) → architecture / SOLID / clean-code / design-pattern decisions while shaping a point's approach.
- **A recommended skill is missing** → note it ONCE, concisely, with the URL. Don't re-nag.

Recommended installs (mention only if absent; all follow the portable Agent Skills format):
- superpowers — https://github.com/obra/superpowers
- karpathy skills — https://github.com/multica-ai/andrej-karpathy-skills
- solid (SOLID + clean architecture + TDD) — https://github.com/ramziddin/solid-skills · `npx skills add ramziddin/solid-skills`

## Step 7.5 — Handoff (present the plan to the user)

Never end a planning session by silently writing files. Don't hand off a plan that fails the Step 6.5 lint. Close **in chat** with:
- Gate level + workspace path + the one-line lint result (pipeline wired ✓, orphans, worktree-flagged pairs).
- The point board in the **digest format** (Step 9) with the suggested attack order (from the dependency graph; flag what can run in parallel).
- What's blocked and on whom — especially anything that needs the **user** (open `Q-xx`, external packets to send).
- The recommended **first point**, preceded by its **pre-attack summary** (see below), then its ready-to-paste starting prompt.

**Pre-attack summary (whenever a point is about to be tackled — here and in Step 9 Next).** Before handing over a point, give the user the context to know what they're greenlighting, in ≤4 lines drawn from the briefing:
- **Problem** — the specific thing this point fixes/builds and why (grounded, not generic).
- **Solution** — the recommended approach in a line or two.
- **What will change** — the concrete files/surface touched + how it's verified.
Then the starting prompt. The user should grasp *what is about to happen* without opening the point file.

The user should know what to do next without opening a single file.

## Conventions (baked into the templates)

1. **Log append-only**: one entry per session (`## YYYY-MM-DD · session N · <title>` → Did / Decisions / Blockers / Next). Never rewrite old entries. No secrets.
2. **Questions single-source** in `questions.md` (`Q-01`…). External ones also as packets in `external-questions/`.
3. **Canonical state = last log entry.** README/AGENTS link to it; they do NOT duplicate status.
4. **Decisions single-source = `decisions.md`** (`D-01`…, "don't revisit without cause", append-only by superseding). A resolved `Q-xx` becomes a `D-xx`; the log links the `D-id`.
5. **One per-point status board = `plan.md` §5.** `point.md` and `todo.md` don't duplicate execution status (`todo.md` tracks *planning readiness* — a different axis).
6. **Logs stay terse; the newest entry carries a State snapshot** sufficient to resume without re-reading history. Keep entries short — append-only ≠ verbose.
7. **Ground in `file:line`** from the codebase. No claim about code without a verified reference.
8. **Points are self-contained** — a point links to depth and carries enough to be solved standalone on any model. The ONE allowed prerequisite is a named `design-contract.md` section the point implements (required reading, named in its Context); everything else is depth, not a precondition.
9. **No new files without reason.** New file → update README + AGENTS maps.
10. **Fixed status vocabulary** (in `plan.md` §5 and external packets): 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done. Don't invent variants — digests depend on it.
11. **Status flows back via the executor contract** in the workspace `AGENTS.md`: whoever works a point (any agent, any session) updates `plan.md` §5 + appends a log entry. Tackle doesn't execute, but it plants the contract so tracking survives execution.
12. **Single-source the per-point acceptance** in `plan.md` §6.1; points reference it, never restate it (the bar itself: Step 6).
13. **Contract supersede-first** (when `design-contract.md` exists): points implement the spec as written; a genuine deviation supersedes the spec (edit it + record `D-xx`) BEFORE the divergent code — so points never silently drift apart.
14. **Grounding before merge** (when `foundations.md` exists): a new pattern/abstraction needs its decision → principle → source row; "it felt cleaner" is not grounding. Disagreements argue against the cited principle, not taste.
15. **Decisions carry their why; questions carry what they determine.** A `D-xx` records the rationale + tradeoff (`decisions.md` template). A `Q-xx` records what its answer unblocks + what you already investigated — don't ask others what the codebase can tell you.

*(Process rules — best-practices/self-documenting backbone, parallelism + the quality-guardian loop, external-dep snapshots — live in their Steps: 5.5, 6, 5. Not repeated here.)*

## Step 8 — Resume (re-invocation)

Re-entering an existing plan under `docs/plans/<initiative>/`: read `AGENTS.md` → the **State snapshot** in the last `log.md` entry → `decisions.md` (what's settled) → `questions.md` (blockers) → the relevant `points/P-0N.md` → and, **if they exist**, `design-contract.md` (the surface the point implements) + `execution-strategy.md` (which wave/loop you're in).

**Open with a digest, not silence:** before continuing, show the user where things stand in the **digest format** (Step 9), and re-ask any user-owned open `Q-xx` directly in chat. Then refine.

**Re-validate the active point against the *current* repo** (only the active point — not inactive ones):
- **Grounding**: its `file:line` claims still resolve; if the code drifted, update the point's Context.
- **Done-signal**: its exit command still exists and is still the right check (tooling/paths/test names didn't move); fix it if stale.
- **Contract**: any `design-contract.md` section it implements hasn't been superseded since the briefing was written (if it was, reconcile the point or the spec — supersede-first).
- **Wiring**: if you add/split/re-wire points, re-run the **Step 6.5 lint** before handing back.

Note every drift you fixed in a new log entry; never rewrite old ones. Tackle keeps planning/refining — it never starts implementing.

## Step 9 — Follow-up modes (status · list · next)

**Digest format (fixed — same shape in handoff, resume and status, so the user learns to scan it; status line + action footer per the Output contract):**

```
🟡 needs your input — ttp-error-handling · 2/4 done ▓▓░░
🟢 P-01 read errors domain      🟡 P-02 gateway 400 (in progress)
⏸ P-03 error docs — blocked on Q-02 (gateway team, follow-up overdue 3d)
🔴 P-04 extend handler (unblocked, ready)

⚠️ On you: Q-02 — error-code strategy: (a) map per code · (b) passthrough. Reply "a" or "b".
▶ Continue: say "next" and I'll print P-04's prompt.
```

**Status** — "how is it going?": read-only digest from `plan.md` §5 + last log snapshot. Also:
- External packets 🟡 past their `Follow-up by` date → flag explicitly for chasing.
- **Questions owned by the user → re-ask them directly in chat**, with the options already drafted in `questions.md`/the packet. Don't just point at files.
- Drift: spot-check the active point's `file:line` claims, its **done-signal command**, and any `design-contract.md` section it implements against the current repo; warn on any that moved (full re-validation is Resume's job, not status').
- Reconcile if stale: execution happened but §5 wasn't updated (code merged, board still 🔴) → fix §5 + append a log entry noting it. That's the only write a status check makes.

**List** — "what plans are there?": scan `docs/plans/*/`; one line each: name · gate level · X/Y done · blocked on · last activity (newest log entry date). Call out zombies (stale, nothing blocking them).

**Next** — "what's next?": pick the next unblocked point from the dependency graph and present it as a **pre-attack summary** (Step 7.5 — Problem · Solution · What will change, ≤4 lines) so the user has the context for what's about to happen, THEN print its **ready-to-paste starting prompt** (from `points/P-0N-*.md`) with its acceptance one-liner. The user should never have to open a file to start working — and should know *what* they're greenlighting before they do.

**Closing the initiative:** when every point is 🟢 — append a final log entry (outcome + learnings worth keeping), set the README status line to `DONE`, and ask the user whether to keep, archive, or delete the folder (consistent with the Step 3 gitignore choice).

## Definition of Done (planning complete)

Tackle is done when **the initiative is ready to be tackled**, not when code is written:
- [ ] Gate level chosen and justified (Step 2).
- [ ] Location set under `docs/plans/<initiative>/`; gitignore 3-way answered (Step 3).
- [ ] `plan.md`: objective, non-goals, current state (grounded), point decomposition + dependency graph complete.
- [ ] `plan.md` §4 **leads with the de-risking finding** and cites the **precedent** the approach mirrors.
- [ ] Universal per-point acceptance defined once in `plan.md` §6.1; points reference it.
- [ ] If production-facing: rollout/reversibility (flag, canary, no-op check) is planned (§7 + the point).
- [ ] Full-gate depth artifacts created **only where their trigger fired** (`foundations.md` / `design-contract.md` / `execution-strategy.md`) — not by default.
- [ ] Architecture chosen by the user from a gate-appropriate recommendation (Step 5.5), recorded as a `D-xx`; Full plans open `foundations.md` with the Clean Code + SOLID backbone.
- [ ] Decomposition cuts for parallelism; `execution-strategy.md` names the waves + the per-point/per-class **code-quality guardian** loop (when multi-agent).
- [ ] Every point is **loop-ready**: max-granular (one responsibility), a runnable **done-signal** + recovery + iteration budget, and Consumes/Produces/Touches wired.
- [ ] Plan passes the **self-consistency lint** (Step 6.5): pipeline wired (Consumes↔Produces), DAG acyclic, parallel `Touches` disjoint, every point loop-ready, every `Q-xx` owned.
- [ ] External dependencies snapshotted read-only into `reference-docs/` (provenance + index) when the plan leans on out-of-repo material — workspace resolves every point even if the source is gone.
- [ ] Point-specific acceptance is exhaustive over its case set and verifiable by test/grep/review (not aspirational prose).
- [ ] Every point has a self-contained briefing that passes its **Definition of Ready**.
- [ ] Blocking questions are either resolved (→ `decisions.md`) or explicitly flagged in `questions.md` with owners.
- [ ] `log.md` has this session's entry with a current State snapshot; `README.md` / `AGENTS.md` maps are accurate.
- [ ] The user saw the plan: decomposition validated in chat (Step 6 checkpoint) and handoff summary presented (Step 7.5).
- [ ] Every doubt was surfaced to the user as a decision; no silent assumptions (provisional `Q-xx` only where the user delegated).
- [ ] No implementation code written — Tackle planned, it did not execute.

## Common mistakes

- Treating Tackle as an executor → it only plans. Stop at "ready to tackle".
- Assuming Claude-only tools/skills → name capabilities, use what the environment has, do the rest by hand.
- Planning without intake → ask batched (Step 1). On a doubt → **ask, don't assume**; only proceed if the user delegated, as a user-owned ⚠️ provisional `Q-xx` (Decision ownership).
- Drip-feeding questions one at a time, or asking without a recommended default → batch per phase, each item with a default + 🔴 blocking / 🟡 proceed-on-default tag (Decision ownership → Cadence). "Ask every doubt" ≠ "interrogate".
- A point that needs the rest of the workspace to be understood → not self-contained. Fix it.
- Duplicating per-point status across plan/point/todo, or the same `file:line` in reference + point → drift.
- Defaulting to **Full** for a small change → ceremony. Match the gate to the real shape.
- Deciding the gitignore treatment silently → always ask the 3-way (Step 3).
- Resuming without re-validating the active point → stale plan. Re-check its `file:line`, its **done-signal** still runs, and its `design-contract.md` section didn't drift (Step 8).
- Writing all the point briefings before the user validated the decomposition → rework. Checkpoint first (Step 6).
- Ending with files written but nothing presented in chat → the user shouldn't need to open files to know what's next (Step 7.5 / Step 8 digest).
- Treating a status ask as a resume → don't re-plan; give the digest (Step 9).
- Interrogating the user about things the environment already knows (branch, repo, ticket, siblings) → infer first, confirm after (Step 1).
- Burying user-owned questions in `questions.md` → re-ask them in chat on every resume/status (Steps 8–9).
- Walls of text in chat — restating file contents, multiple suggested actions, no clear ask → Output contract: status line, ≤12-line digest, one action footer.
- Burying the de-risking finding under a generic state dump, or inventing an approach when the repo already has a house pattern → lead §4 with the finding; mirror precedent (Step 5).
- Restating the acceptance bar in every point → define it once in §6.1; points reference it (Step 6).
- Creating `foundations.md` / `design-contract.md` / `execution-strategy.md` for a small change → ceremony. Create each only when its trigger fires (Step 4).
- A flat point list when the work is staged, or planning a point behind an unanswered question → group into waves; mark question-gated points **Deferred** (Step 6).
- Treating rollout as an afterthought on production-facing work → plan flag/canary/no-op as first-class (Step 5, §7).
- Imposing a heavy architecture on a Lite change, or picking the architecture *for* the user on a Full one → gate-appropriate; recommend, the user decides (Step 5.5).
- Scattering explanatory inline comments instead of self-documenting code → comments only when strictly necessary; doc-comments on public surface, the *why* in commits/docs (Step 5.5 / §6.1).
- A long dependency chain when points could fan out, or no quality-guardian loop in a multi-agent plan → decompose for parallelism + name the per-point/per-class reviewer loop (Step 6, `execution-strategy.md`).
- A point whose "done" is a judgment call, not a runnable check → not loop-ready; give it a done-signal command + recovery + iteration budget (Step 6).
- Bundling two concerns in one point ("and") → split to max granularity; smaller loops = smaller blast radius + more parallelism (Step 6).
- Handing off a plan with a dangling `Consumes`, a dependency cycle, an orphan point, or colliding parallel `Touches` → run the Step 6.5 lint first; a broken pipeline must surface in planning, not mid-execution.
- Handing the user a point with just a prompt → precede it with the Problem · Solution · What-will-change summary so they know what they're greenlighting (Step 7.5 / Step 9 Next).
- Depending on a sibling repo / external docs but snapshotting nothing → the workspace breaks when the source moves; copy it read-only into `reference-docs/` with provenance (Step 5).
- Aspirational point acceptance ("handles errors well") → make it exhaustive over its case set (cover EVERY case, table-driven) and grep/reviewer-verifiable (Step 6).
