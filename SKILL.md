---
name: Tackle
description: Use when starting a non-trivial, multi-session or multi-track initiative (Jira ticket, feature, refactor, investigation, bug with unknowns) that needs a durable action plan broken into self-contained points, before writing implementation code. Triggers include "plan de acción", "armá/armar un plan", "plan this out", "tackle this", "iniciativa". Also use when resuming such an initiative from an existing plan folder under docs/plans/, or when asked how an existing initiative is going ("cómo viene", "status", "seguimiento", progress check), which initiatives exist ("qué planes hay"), what the next point to work on is ("qué sigue"), or when migrating an old plan to the current methodology ("migrar/actualizar/modernizar el plan").
---

# Tackle

## Overview

Tackle turns an initiative into a **durable action plan**, broken into self-contained **points** that can be attacked across different sessions and agents. It produces a workspace of grounded markdown artifacts under `docs/plans/<initiative>/` that survives session and agent handoffs.

**Scope — Tackle plans and can execute the plan it produces.** It never writes implementation code on its own. Each point's `.md` carries *all* the info needed to resolve that point in a fresh session — context, approach, recommended prompt, and alternatives. The optional `/tackle-implement` and `/tackle-next` modes drive execution by spawning the point team defined in `team.md`, running each point's done-signal, and advancing the board.

**Runs on the codebase.** Tackle is designed to run from inside the target repository. If you are not inside a repo, stop and ask for the codebase path before proceeding. Once confirmed, ground every claim in real `file:line`.

**Model- and harness-agnostic.** Works with any agent/model/IDE; follows the open Agent Skills format (this `SKILL.md` + `references/`). Instructions name *capabilities* (code search, go-to-def/find-refs, file I/O, ask-the-user), not vendor tools — do by hand what your environment lacks. Other skills named below are **optional aids**, used only if present.

**Language:** all workspace artifacts are written in **English**, regardless of the conversation language.

**Routing — what the user says → what runs:**

| The user says (any language) | Mode |
|---|---|
| `/tackle-init [preset]` | **Init** → create `docs/plans/<initiative>/` and the plan-local customization tree: `presets/<preset>/` and `overrides/` |
| `/tackle-constitution` | **Constitution** → produce `docs/plans/<initiative>/constitution.md` |
| `/tackle-specify` | **Specify** → produce `docs/plans/<initiative>/spec.md` |
| `/tackle-plan` or `tackle this` / `plan de acción` / `armá/armar un plan` / `plan this out` / `iniciativa` | **Plan** → Steps 1–7 |
| `/tackle-tasks` | **Tasks** → produce `docs/plans/<initiative>/tasks.md` |
| `/tackle-implement` | **Implement** → execute the plan point-by-point in dependency order |
| `/tackle-next` | **Execute next** → execute exactly one ready point and stop |
| `/tackle-checklist` | **Checklist** → produce `docs/plans/<initiative>/checklist.md` |
| `resume / retomá <initiative>` | **Resume** → Step 8 |
| `how is <initiative> going?` / `status` / `seguimiento` | **Status** → Step 9 |
| `what plans are there?` / `qué iniciativas hay` | **List** → Step 9 |
| `give me the next point` / `qué sigue` | **Next** → Step 9 |
| `migrate / upgrade / modernizá <initiative>` | **Migrate** → Step 8.5 |
| `mejorá este plan` / `improve this plan` / `tackle-upgrade <initiative>` | **Improve** → Step 10 |

If the initiative is ambiguous (several under `docs/plans/`), show the List and ask which.

### SDD phase entry points (optional)

These phases can be used standalone or chained. `/tackle-plan` is still the standalone default path.

| Phase | Trigger | Output | Stops after |
|---|---|---|---|
| Init | `/tackle-init [preset]` | `docs/plans/<initiative>/presets/<preset>/`, `docs/plans/<initiative>/overrides/` | Workspace skeleton only; no content yet. |
| Constitution | `/tackle-constitution` | `docs/plans/<initiative>/constitution.md` | Principles and constraints; no spec or points. |
| Specify | `/tackle-specify` | `docs/plans/<initiative>/spec.md` | Requirements and acceptance; no points. |
| Plan | `/tackle-plan` | Full workspace (`plan.md`, `points/`, etc.) | Complete decomposed plan. |
| Tasks | `/tackle-tasks` | `docs/plans/<initiative>/tasks.md` | Flattened checklist from `plan.md` §5. |
| Implement | `/tackle-implement` | Updated `board.md` + `log.md` | All ready points are done or one is blocked. |
| Execute next | `/tackle-next` | Updated `board.md` + `log.md` | Exactly one ready point. |
| Checklist | `/tackle-checklist` | `docs/plans/<initiative>/checklist.md` | Checklist from selected source. |

### Template-resolution stack

Tackle resolves templates and presets in this order, first match wins:

```
docs/plans/<initiative>/overrides/     ← plan-local overrides
  > docs/plans/<initiative>/presets/<preset>/  ← chosen preset
  > references/sdd/                    ← SDD phase templates
  > references/                        ← base templates
```

In short: **overrides > presets > sdd > core**.

* **Presets** live in `references/presets/<preset>/` and are copied into `docs/plans/<initiative>/presets/<preset>/` by `/tackle-init`.
* **Overrides** live in `docs/plans/<initiative>/overrides/` and are empty by default; drop files here to replace any template or preset file for this initiative only.
* **Nothing Tackle-related is installed at the repo root.** All customization is visible inside `docs/plans/<initiative>/`.

### Execution loop (`/tackle-implement` and `/tackle-next`)

Tackle 2.0 can execute the plan it produces, not just plan it:

1. Read `docs/plans/<initiative>/board.md` for the dependency graph and current status.
2. Pick the next ready point in dependency order.
3. Render `references/sdd/implement.tmpl.md` (or the override/preset equivalent) with the point's context.
4. Run the point's done-signal.
5. If green → mark 🟢, append a `log.md` entry, continue to the next ready point (`/tackle-implement`) or stop (`/tackle-next`).
6. If red → recover and retry up to the point's loop budget (default from `AGENTS.md`). If still red, mark ⏸ blocked, append `log.md`, and stop.

The execution team size is Solo/Pair/Pod/Squad per `team.md`. The workspace (`board.md`, `log.md`) is the state machine; chat history is not.

### Init mode

Triggered by `/tackle-init [preset]`.

1. Confirm the initiative name (or ask if ambiguous).
2. Create `docs/plans/<initiative>/` if it does not exist.
3. Copy `references/presets/<preset>/` into `docs/plans/<initiative>/presets/<preset>/`.
4. Create `docs/plans/<initiative>/overrides/`.
5. If the requested preset is missing, fall back to `references/presets/default/`.

### Constitution phase

Triggered by `/tackle-constitution`.

1. Confirm the initiative name (or ask if ambiguous).
2. Create `docs/plans/<initiative>/` if it does not exist.
3. Render `references/sdd/constitution.tmpl.md` to `docs/plans/<initiative>/constitution.md`.
4. Fill the placeholders with the user: project name, date, purpose, principles, quality bar, non-goals, conflict resolution.
5. Stop — the Constitution phase produces only `constitution.md`. No spec, no points, no execution.

### Specify mode

Triggered by `/tackle-specify` or `tackle-specify`.

1. Confirm the initiative name (or ask if ambiguous).
2. Create `docs/plans/<initiative>/` if it does not exist.
3. Render `references/sdd/specify.tmpl.md` to `docs/plans/<initiative>/spec.md`.
4. Fill the placeholders with the user: what is being built, why it matters, non-goals, user stories, acceptance criteria, open questions, and references.
5. Stop — the Specify phase produces only `spec.md`. No points, no depth artifacts, no execution.


If the user points at a folder that is **not** under `docs/plans/` (e.g. a loose markdown file, a Jira-export, a previous initiative's notes), the Improve mode treats it as an unstructured plan and converts it into a Tackle workspace under `docs/plans/<initiative>/` (Mode B below).

**Two-step Improve contract:** Improve is a migration, not a re-plan. It upgrades the *structure* and applies the current methodology's hard-won rules; it does NOT re-litigate closed decisions or throw away settled design. If the source is rotten beyond repair (archaeology, no coherent decomposition, structural drift across every point), flag it and recommend a fresh **Create** instead.


## Step 10 — Improve / upgrade an existing plan (new-mode migration)

Triggered by "mejorá este plan" / "improve this plan" / "tackle-upgrade <initiative>".

### 10.1 Detect the source

Inspect the path the user gave. Ask if unclear.

| What is there | Mode | Action |
|---|---|---|
| `docs/plans/<initiative>/` exists with `AGENTS.md` and a **Tackle** `Methodology:` stamp (any version whose core structure is intact: `plan.md` §6.1, done-signals, `Depends-on`+`Touches`) | **Mode A — Tackle-to-Tackle upgrade** | Diff the stamp vs current `SKILL.md`; apply only the rules introduced since that stamp (Step 5.75, Q-guard, skeleton-board-first, contract-churn guard, etc.); re-lint; bump stamp. |
| `docs/plans/<initiative>/` exists but has **no** `Methodology:` stamp, or its structure is missing `plan.md` §6.1 / done-signals / `Depends-on`+`Touches` (pre-Tackle or Tackle archaeology) | **Mode A' — Old Tackle recovery** | Run **Step 8.5** to rebuild the base Tackle shape from the existing material, preserving history; then run **Mode A** to bring it to the current version. |
| Any other folder/file (loose markdown, Jira export, Miro/Notion dump, `TODO.md`, `PLAN.md`, branch notes) | **Mode B — Unstructured → Tackle** | Ingest, infer the objective, extract decisions/questions, create a Full or Lite Tackle workspace. |
| Nothing / empty path | **Stop** | Ask for the source. |

### 10.2 Mode A — Tackle-to-Tackle upgrade

1. **Read the workspace in resume order** (Step 8).
2. **Diff methodology**: compare the workspace's `Methodology:` stamp against the current `SKILL.md`. List the rules introduced since that stamp that the plan does NOT yet satisfy. Examples: Step 5.75 contract-stabilization, Step 6 skeleton-board-first, Step 6.5 Q-guard / contract-churn guard, intake anchor (Step 1.5).
3. **Apply non-breaking structure changes only**:
   - Add missing artifacts if their trigger now fires.
   - Split or merge points only where the current methodology identifies a structural smell AND the user confirms (or delegated). Do NOT re-plan the cut because it "looks nicer".
   - Update every point's `Context` to cite the contract section it implements (Step 5.75 reference-only rule) if it currently inlines spec.
   - Re-run the **Step 6.5 lint** with the new guards (Q-guard, contract-churn guard).
4. **Record**: new `log.md` entry "Upgraded to Tackle 2.0"; bump `Methodology:` stamp in `AGENTS.md` (and `plan.md` header for Lite) to **Tackle 2.0**; add a `D-xx` if a structural choice was required.
5. **Handoff**: digest + what changed + what was preserved + lint result.

### 10.3 Mode A' — Old Tackle migration

Run **Step 8.5** first. Then run **Mode A** on the result.

### 10.4 Mode B — Unstructured → Tackle

Treat the source as raw material, not as a plan to preserve verbatim.

1. **Ingest**: read every file the user points to. Extract:
   - Objective (what result is wanted).
   - Non-goals (what is explicitly out).
   - Decisions already made (become provisional `D-xx` candidates — confirm before locking).
   - Open questions (become `Q-xx`).
   - Existing decomposition, if any (tasks, epics, bullet lists).
   - External references (become `reference-docs/` snapshots).
2. **Run Step 1.5 intake anchor**: problem, observable result, top 2 non-goals, highest-shape decision.
3. **Run Step 2 gate sizing**: Full vs Lite vs None. Default to Full if the source has ≥2 tracks, external deps, or handoff intent.
4. **If Full and a design contract is implied but missing**: run Step 5.75 — draft the contract BEFORE decomposition. If the source is too fuzzy to stabilize, do NOT decompose yet; surface the blocking questions and stop.
5. **Decompose** (Step 6 skeleton board first) from the extracted tasks, splitting merged concerns and merging dangling deps.
6. **Lint + handoff**.

### 10.5 Stop conditions

- If the source plan has already started execution (code exists, PRs merged), Improve becomes **Resume + migrate board hygiene only**; do not restructure executed work.
- If the source is archaeological (no living grounding, every `file:line` dead, decomposition nonsensical), stop and recommend a fresh **Create**.
- If the user wants a better plan because the current one is *wrong* (not just old), that is **Create** with preserved decisions, not **Improve**.

## Step 11 — Versioning and release notes (optional)

When the methodology itself changes, record the change so agents and users know what changed between Tackle versions.

Tackle does not require a `CHANGELOG.md`, but if the workspace lives in a repo that is shared (like this skill repo), add a short entry under `references/CHANGELOG.md` or similar:

```
## Tackle 2.0
- SDD phase entry points: `/tackle-init`, `/tackle-constitution`, `/tackle-specify`, `/tackle-tasks`, `/tackle-implement`, `/tackle-next`, `/tackle-checklist`.
- Plan execution: `/tackle-implement` and `/tackle-next` run points point-by-point.
- Template-resolution stack: overrides > presets > sdd > core.
- Visible plan-local customization: `presets/` and `overrides/` inside `docs/plans/<initiative>/`.
- New depth artifacts: `team.md` (execution team protocol) and `board.md` (canonical status board).

## Tackle 1.5
- Step 5.75: stabilize design contract before decomposition.
- Step 6: skeleton-board-first checkpoint.
- Step 6.5: Q-guard + contract-churn guard.
- Step 10: Improve / upgrade mode (Tackle-to-Tackle and unstructured → Tackle).
```

Bump the default `Methodology:` stamp written by new workspaces to **Tackle 2.0**.

## Output contract (chat = signal; files = depth)

Applies to every Tackle chat response that presents a plan or its state (Create/Resume/Status/List/Next). A **None**-gate inline answer or a one-line clarification is exempt from the full status-line/footer — keep those terse. The user must never have to dig through prose to learn whether action is needed:

1. **Open with one status line**: `🟢 on track — nothing on you` · `🟡 needs your input` · `🔴 blocked`. (This 3-state line answers *"is it on me?"* — a different axis from the board's 4-state lifecycle `🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done`, Convention 10. Same palette, different question; don't conflate the two 🔴/🟢 senses.)
2. **Close with the action footer** — the only two questions the user actually has:
   ```
   ⚠️ On you: <what only the user can decide/do — options ready if it's a choice, else an open prompt ("reply with X, or 'you pick'")> — or "✅ nothing on you"
   ▶ Continue: <ONE literal next thing to say — e.g. say "next" and I'll print P-04's prompt>
   ```
3. **Hard caps**: digest ≤ 12 lines; handoff ≤ one screen. Don't paste file contents into chat — point to them.
4. **Group blockers by owner — you / other teams / me — in that order.** The user's first question is "is it on me?".
5. **One recommended next action, singular.** Alternatives live in the files; offer them only if asked.
6. **Progressive disclosure**: compact first, then offer depth ("want the full board / the point detail?") — never dump it unprompted.

## Decision ownership — the user decides every doubt (no exceptions)

**Tackle assumes nothing.** Every doubt that surfaces while planning — scope, architecture, naming, a tradeoff, an ambiguous requirement, a gap in the codebase — goes to the user as a decision. **Recommend** (mark your pick, give options + a one-line why), but the user decides; this is the one rule with no exception. *Infer* (from branch/repo/code) to turn a question into a fast confirmation — that's not assuming, it's grounding, and you still confirm. The only time you proceed without a live answer is when the user **explicitly delegated** it ("just figure it out") or is unavailable; even then you don't bake a silent assumption — you record it as a **user-owned open `Q-xx`**, surface it, and let them overturn it later. A planning choice the user never saw is a bug.

**Delegation/absence degrades EVERY mandatory choice — it never blocks.** Under "just figure it out" or an absent user, the otherwise-required user decisions — the gate (Step 2), gitignore (Step 3), rollout (Step 5), architecture (Step 5.5), the decomposition checkpoint (Step 6) — each become a ⚠️ provisional `Q-xx` with your recommended default; you proceed and surface them all on handoff. Never stall on a checkpoint or a "the user decides" gate that the user already told you to drive.

**Classify each doubt (one tree):** user-owned + you can default → 🟡 **provisional** (proceed, record). User-owned + you genuinely can't default → it blocks *what it gates*: one point → mark that point **Deferred** (name the `Q-xx`); the whole cut/phase → 🔴 **phase-gating** (stop the batch). Under delegation/absence, the "can't default" branch collapses to 🟡 (you always have a recommended default). External-team-owned → **Deferred** point + an `external-questions/` packet. (At gate **None** there's no batch — its one doubt is handled inline, Step 2.)

**Cadence — batch doubts, don't drip-feed.** Surfacing every doubt does NOT mean a stream of one-off questions (that's its own failure mode). Collect the doubts a phase raises — intake, architecture, decomposition — and ask them in **ONE consolidated round**: a form via your environment's structured-ask facility if it has one, else a compact numbered list (blocking items first, defaults inline). This batch is the one response **exempt from the ≤12-line digest cap** — it's the work, not a digest. Rules:
- **Every item carries a recommended default + a one-line why** — so the user can rubber-stamp ("take the defaults") or override only the ones they care about. N questions become one low-effort review, not an interrogation.
- **Tag each: 🔴 blocking** (can't proceed without it — gates the phase) vs **🟡 proceed-on-default** (you move on the recommendation now, recorded as a ⚠️ provisional `Q-xx`, confirmed later). Only the 🔴 ones stop you.
- **Lead with the few that change the plan's shape**; bundle the rest as "defaults I'll take unless you object."
- **Never drip-feed inside a phase** (ask → wait → ask → wait), and **never re-ask a closed `D-xx`** without cause. But a *blocking* doubt that surfaces after a phase's batch closed re-opens a **minimal** batch — that's not drip-feeding (drip-feeding is asking serially what you could have batched).
Surface the batch as ONE footer action (Output contract).

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

Doubts during intake follow *Decision ownership*: recover what the codebase can answer, raise the rest to the user. Only on explicit delegation do you proceed provisionally — recording each gap as a ⚠️ provisional `Q-xx` (what you chose, what you couldn't verify, the risk), overturnable, never a silent assumption.

### Step 1.5 — Anchor the intake before sizing

Before choosing a gate (Step 2), lock the shape of the problem in one screen. Write it into the first `log.md` entry and do not proceed until these four items are filled — even if the answer is provisional:

1. **Problem in one sentence** — the specific pain or gap, in user outcome terms.
2. **Observable result** — what changes for the integrator/user when this is done.
3. **Top 2 non-goals** — the things this initiative explicitly does NOT do; name the anti-patterns from this repo you are refusing to carry over.
4. **Highest-shape decision** — the single open question whose answer changes the cut of the plan the most; if it is unresolved, every point that touches it is Deferred until it is decided (see Step 6.5 Q-guard).

This anchor is the cheapest place to catch scope drift. If you cannot fill (1) and (2), you are still diagnosing, not planning — stop and clarify instead of scaffolding artifacts.

## Step 2 — Size the initiative (gate)

Do NOT scaffold a full workspace for everything. Pick a level:

| Level | When | Examples | Produces |
|---|---|---|---|
| **None** | Single obvious change, <~3 steps, no unknowns | typo, rename a local, bump a constant | No workspace. Just plan inline. |
| **Lite** | Single-session, bounded scope, a few unknowns | add one validation to an existing endpoint, plumb a field already wired | `plan.md` + `log.md` + `todo.md` only (`references/lite-plan.tmpl.md`) |
| **Full** | Multi-session OR multi-track OR multi-team OR high uncertainty OR handoff expected | introduce a new subsystem, multi-module refactor, feature spanning sessions | Full core + `points/` + appendices |

**Decide by the tie-breaker, not by vibe:** touches ≥2 modules OR changes the public API OR spans sessions/teams OR a handoff is expected OR **needs a canary/coexistence rollout** → **Full**; confined to one file with no public surface change → **Lite**. A production-behavior change is Lite only if its rollback is a single revert; if it needs a flag-coexistence/canary plan (a durable rollout decision), it's **Full** (that decision needs a `D-xx` home Lite doesn't have). Only when the tie-breaker genuinely doesn't settle it, start **Lite** (upgrades cleanly by adding `README.md` / `AGENTS.md` / `reference.md` / `points/`).

**Bigger workspace ≠ better plan** — match the level to the real shape; don't default to Full because it feels thorough (over-sizing buries the work in ceremony, under-sizing loses context across sessions).

**The gate scales ceremony, not principles** — but it scales *both* artifacts AND process. Full/Lite carry Decision ownership, self-documenting code, a done-signal, rollout-if-production. **None has a hard ceremony floor:** state the change + its one done-signal + any single real doubt, inline, in ≤3 lines — **skip** the gate structured-ask, the gitignore 3-way (no workspace), and batching (no phases). A one-line constant bump must not cost five ceremony beats.

Present the level as a one-tap choice with your recommendation marked and a one-line justification (use your environment's structured-ask facility if present; plain question otherwise). Same for the gitignore 3-way in Step 3.

## Step 3 — Location & gitignore

Plans live under **`docs/plans/<initiative>/`** in the repo. Name `<initiative>` after the ticket (`MBTX-4488/`) or a slug (`error-handling/`); provisional slug if unassigned, rename later. Create `docs/plans/` if missing.

(Skip this step for **None** — no workspace, nothing to ignore.) Then ASK the user how to treat plans in version control (3-way, never decide silently):
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

**Optional:** `external-questions/` — packets to other teams → `references/external-question.tmpl.md` (when a question goes external). · `reference-docs/` — read-only snapshots of external material → `references/reference-docs-README.tmpl.md` (when the plan depends on anything outside this repo; see Step 5 for the why).

**Depth artifacts (Full only — create each ONLY when its trigger fires; never by default, they're ceremony otherwise):**
- `foundations.md` — grounding table (decision → principle → source) → `references/foundations.tmpl.md`. **When:** the initiative introduces non-trivial architecture (new subsystem, layering, a set of patterns).
- `design-contract.md` (a.k.a. `api-spec.md`) — the authoritative public surface points implement → `references/design-contract.tmpl.md`. **When:** points could each get a shared surface *wrong independently* — i.e. conformance drift is the risk (API, wire format, state machine, error taxonomy). That's what makes it **normative** and a point's "required reading" (Convention 8). Contrast `reference.md`, which holds *descriptive* shared facts (what the code is); if you only need to point at shared context, that's `reference.md` and an ordinary `Depends-on`, not a contract.
- `execution-strategy.md` — waves + inter-wave quality gate + deferral → `references/execution-strategy.tmpl.md`. **When:** execution will be multi-agent/parallel or phased. (Still planning, not executing — it plans the attack.)
- `team.md` — execution team roles and protocol → `references/team.tmpl.md`. **When:** points will be executed by multi-agent teams (Pair/Pod/Squad) so every agent knows the rules.
- `board.md` — canonical status board derived from `plan.md` §5 → `references/board.tmpl.md`. **When:** the plan will be executed with `/tackle-implement` or `/tackle-next`; it is the state machine for execution.

If using superpowers for depth, also create `specs/` and `plans/` as needed (not scaffolded by
default — create them when you start using `brainstorming` / `writing-plans`).

**Appendices (free, descriptive names):** add only when needed (`error-catalog.md`, `design-strategy.md`). When you add one, update the `README.md` and `AGENTS.md` file maps.

**Large multi-domain initiative:** if one `reference.md` would be a wall, split it into a **numbered, feature-sliced set** (`00-architecture.md`, `01-foundation.md`, `02-<domain>.md`…) for a deterministic reading order; slices map onto point cuts. Only when the domain is genuinely broad — otherwise one `reference.md`.

## Step 5 — Briefing (ground it in the codebase)

Investigate the actual repo and fill `plan.md` / `reference.md` from it, not from assumptions:
- **Lead with the de-risking finding.** Actively hunt for the ONE verified fact that reshapes the risk profile — and put it first in `plan.md` §4. Usually it makes the work *safer/smaller* ("the old path is dormant → adoption, not hot replacement → low regression risk by construction"), but it may instead *raise* the risk ("this is the hot path for 30 targets → every change needs a parity gate") — surface it either way. Finding it is the highest-leverage move in planning; don't bury it under a generic state dump.
- **Anchor the approach to precedent.** Find the existing **house pattern** in this repo (the convention sibling modules already follow) and/or a **proven reference architecture** (in-house module, external project) this design should mirror — cite it `file:line`. Default to mirroring precedent over inventing; deviating from it is a decision (`D-xx`), not a default.
- **Objective + expected result**: observable outcome.
- **Non-goals**: explicit out-of-scope — prevents scope creep. Name the specific anti-patterns (from this codebase) you're deliberately NOT carrying over.
- **Current state**: every claim about code cites `file:line`, verified with your code-search / find-references tools — not memory.
- **Domain invariants / constraints**: consult the authoritative source for the domain (spec, domain MCP, canonical constants) if your environment has one; else use the repo's own constants and annotate. Phrase invariants so they're **structural and verifiable** (a check, not prose) — they become per-point acceptance.
- **Quality-dimensions pass — name them, don't hope you remember them.** Walk the **quality-dimensions catalog** (Step 6) at the *initiative* level: which axes does this initiative's surface fire — **Security**, **Performance**, **Concurrency**, **Correctness**, or an open one (data-integrity, a11y, observability…)? *(Architecture and Conventions & Style are the always-on backbone — they're §6.1 by default, not part of this pass.)* **Also discover this repo's quality tooling once** — test runner, linters, strict-concurrency/race flags, any bench or security/secret-scan harness, the CI gates — and record it in `reference.md`, so each fired axis maps to a mechanism that already exists (or surfaces that one is *missing*, itself a finding). Rollout/reversibility (next bullet) is the axis already promoted to first-class — these are its siblings. Decide each *now*, repo open: an axis that fires for *every* point → promote it into `plan.md` §6.1 as a universal invariant (Step 6); one that fires for *specific* points is derived in those points' Acceptance, not here; one that *doesn't* fire but a reader would expect it to (e.g. an auth-touching initiative that deliberately skips rate-limiting) → record a one-line **non-goal**. Don't paper over axes nobody would expect to fire. **Gate-appropriate:** None/Lite walk only what the change plausibly touches — don't threat-model a constant bump.
- **Rollout / reversibility (if it touches a production path)**: plan how it ships safely as a first-class concern, not an afterthought — enablement flag default-off, canary target, coexistence with the old path, and the **no-op/parity check** that proves flag-off changes nothing. Record it in `plan.md` §7; make the parity check **universal acceptance** (§6.1) when the old/new paths coexist for the whole initiative, or point-level when one point owns the cutover.
- **Boundary**: `reference.md` holds facts shared by ≥2 points. Most Context in a point will simply link to `reference.md`; a point only needs unique Context when it touches code no other point touches.
- **Snapshot external dependencies into `reference-docs/` (read-only).** When the plan leans on material outside this repo — a sibling repo's source, vendor/API docs, diagrams, a prior initiative's rules or resolved external Q&A — copy it into `reference-docs/` so the workspace survives the source moving or going unavailable (Tackle's durability promise depends on this). Add a `reference-docs/README.md` (`references/reference-docs-README.tmpl.md`) with **provenance** (source · branch · date), a **never-edit/re-snapshot** rule, and an **index** (folder → contents → which point/spec uses it). `reference.md` still lists the *live* paths — prefer them when both exist; the snapshot is the fallback.

## Step 5.5 — Architecture (recommend; the user decides) — gate-appropriate

**The backbone is always Clean Code + SOLID and the best referents of software design** — grounded in `foundations.md`, never "it felt cleaner". The *shape* on top of that is a choice scaled to the gate:
- **None / Lite** → no new architecture: follow the existing structure of the file/module you're touching. Don't impose a paradigm on a bounded change.
- **Full** → **recommend** one architecture matched to the initiative (e.g. hexagonal/ports-&-adapters, layered/clean, MVVM, event-driven…), justified from what Step 5 found — and **present it as the user's choice** (one-tap structured ask: the recommendation marked, 1–2 line rationale, the realistic alternatives). The user decides; Tackle proposes. **Default the recommendation to the house pattern** you anchored to in Step 5 — deviating from precedent must earn it.

Record the chosen architecture as a `D-xx` (with its why) and open `foundations.md` with it. The point decomposition (Step 6) then follows the architecture's seams — the layers/ports/boundaries become natural point cuts.

## Step 5.75 — Stabilize the design contract before decomposition (Full-gate hard gate)

When a `design-contract.md`/`api-spec.md` exists, **do not write point briefings until the contract survives one full planning session unchanged**. The contract is the single source of truth for every public surface, state, error, and wire shape. If it keeps changing while points are being drafted, the points become a propagation chore, not an execution plan.

**Process:**
1. Draft the contract as a depth artifact (Step 4) *before* the skeleton board (Step 6).
2. Walk it with the user (or their delegate) and reconcile the highest-shape decisions (Step 1.5) *inside the contract*.
3. Land all overturnable decisions as `D-xx` — or mark them provisional and keep the affected sections out of the contract until they land.
4. Only when the contract has no open user-owned question that changes a section may you proceed to Step 6.

**Contract churn rule:** if a contract section changes after any `points/*.md` exists, every point referencing that section is stale. The Step 6.5 lint fails until the references are reconciled. Do not treat this as normal iteration; it signals that decomposition happened too early.

**Reference-only points:** a point MUST cite the contract section it implements (`api-spec.md §X`) in its Context and MUST NOT inline the spec. If the contract says it, the point links to it. If the point needs to say it differently, the contract is superseded first (AGENTS rule 7 / Convention 13).

## Step 6 — Decompose into points (the heart)

Break the initiative into **independent points** (work units) with a dependency graph in `plan.md`. IDs are zero-padded: `P-01`, `P-02`…

**Prerequisite (Full):** Step 5.75 is satisfied — the design contract is stable and every overturnable decision is landed or explicitly out-of-contract. If the contract is still churning, go back to Step 5.75.

**Checkpoint — skeleton board first:** before writing any `points/*.md` briefing, present only a skeleton table in chat: `P-0N` · one-line **What** · **Depends-on** · **Touches** · the shape of the done-signal (command vs review-gate). No approach, no alternatives, no prompts. Get the user's OK on the cut and the dependency graph. Redoing a skeleton is cheap; redoing N briefings is not. Only after the cut is approved do you flesh out the points. (Absent/delegated user: don't stall — write the briefings, record the cut as a provisional `Q-xx` "validate decomposition," and surface it on handoff.)

For each point write `points/P-0N-<slug>.md` from `references/point.tmpl.md` so a cold agent can resolve it **from that file alone**. Each point MUST include: Goal (single responsibility) · **Depends-on** (the edge + what it needs from upstream) · **Touches** (write scope) · grounded Context (`file:line`) · Non-goals · **Recommended approach** · **Alternatives / fallbacks** · **Recommended starting prompt** · **Acceptance** (which carries the runnable **done-signal** + recovery) · linked open questions · a **Definition of Ready** self-check. **A point is verified by exactly two things: its done-signal command and `plan.md` §6.1** — no separate "verification" surface. A point links to deeper artifacts instead of duplicating them. Per-point execution status lives only in `plan.md` §5.

**Engineer each point as a loop (loop engineering).** Plan so execution can be a tight autonomous loop: *do → run the done-signal → green = next · red = recover → escalate if stuck*. So every point carries an explicit **done-signal command** (a pass/fail exit, no human judgment) and a **recovery hint**; it self-corrects up to the workspace iteration budget (`AGENTS.md` default), then STOPS and asks (Decision ownership). Its `Depends-on` + `Touches` place it in the pipeline so independent points run as concurrent loops. First try to sharpen a fuzzy point until it HAS a runnable done-signal — most "untestable" points are just under-specified.

**Judgment/investigation points** (research "which library", error-copy/UX polish, a design spike) genuinely can't end in a `command → exit 0`. Do NOT manufacture a fake green check (`test -f research.md` proves nothing). Their done-signal is **an artifact + an acceptance rubric, checked by a human or a reviewer agent** — e.g. "`decisions.md` has a `D-xx` choosing the library with the comparison matrix filled," "the error copy meets the rubric in Acceptance." State it as such and mark the point's exit as review-gated, not command-gated. This is the same non-command acceptance the fan-out point uses — generalized; honesty beats a green that lies.

**Point size — max granularity, one verifiable done-signal.** A point is the *smallest* change with ONE responsibility that ends in its own machine-checkable done-signal. Default to splitting — and the split that's easy to miss is a **pure/port-free core vs its effectful shell** (functional core / imperative shell): the pure part has its own done-signal with no doubles or deps, so it's its own earlier, more-parallel point. Floor: if a candidate has no done-signal runnable *without* finishing another point, merge them — and if two points always ship together and a reviewer would review them as one, merge them too. Granularity serves parallelism and clean recovery, not itself; don't shatter a small plan into a swarm of trivial 30-min points. ~30 min–3 h, but responsibility + done-signal beats the clock.

**Decompose for parallelism — cut points so they run as concurrent loops across subagents.** The plan is a *parallelization plan*: prefer many independent points over one long chain. Minimize dependency depth; isolate a shared surface into ONE early point (e.g. the design contract) so the rest fan out against it without colliding. The dependency graph (`plan.md` §5) + each point's **Touches** are the pipeline — anything in a wave not on your `Depends-on` chain runs alongside you. A point that forces everything else to wait is a smell — split the bottleneck.

**Group into phases/waves when the work is staged or wide.** *Tie-breaker (like the Step-2 gate):* ≥2 points runnable in parallel, OR any quality boundary / phase line, OR multi-agent execution → use waves with a quality bar between them. Otherwise a flat ordered list is fine — don't manufacture waves. A point gated on an open `Q-xx` is **Deferred** — list it as such with the blocking question, NOT as an active point; don't plan work behind an unanswered external dependency. When execution will be multi-agent or phased, capture the waves in `execution-strategy.md` (Step 4 depth artifact).

**Fan-out across N near-identical targets** (e.g. migrate 30 white-label apps): model it as ONE parameterized point with the per-target checklist + a worked example, not N copies and not one vague point — and usually Deferred behind the "who-owns-the-cutover/cadence" question. Note the cardinality explicitly. Its *acceptance* is "the worked example passes + the checklist covers the variance axes" (verifiable now); the "all N migrated" rollup is tracked on the board, not as the point's code-acceptance.

**Define the universal per-point acceptance once** (`plan.md` §6.1): the bar EVERY point must clear. Beyond the generics (tests, grounding, contract conformance, no-regression, board hygiene), **promote the load-bearing structural invariants from `design-contract.md` / Step 5 into §6.1** — the domain-specific gates that actually catch drift (e.g. "core compiles with zero deps", "concurrency-clean under the language's strict mode", "no unauthenticated path reaches the handler", "stays within the p99 latency budget", "self-documenting: no explanatory inline comments") — including the **quality-dimension axes** the Step 5 pass found firing for *every* point. §6.1 is the always-on **backbone** (Architecture via grounding, Conventions & Style via self-documenting, plus tests + no-regression); an axis that fires only for *specific* points lives in those points' Acceptance (see the catalog below), not here — don't impose one point's gate on all. Each point *references* §6.1 and adds only point-specific criteria. Make those **exhaustive and mechanically verifiable** — where a finite set exists (error cases, states, endpoints), cover EVERY case (table-driven); prefer criteria a grep or a reviewer can check over aspirational prose. Never restate the §6.1 bar N times (that's drift waiting to happen).

**Quality-dimensions catalog — the axes a reviewer grades, and the *runnable check* each becomes in THIS repo.** Open list (extend it for the domain — e.g. data-integrity, a11y, i18n, observability). The catalog's point is **teeth**: a fired axis does NOT become prose ("consider security"), it becomes a **done-signal fragment** — a command/test that fails red — mapped to the tooling the Step 5 pass found in this repo (`reference.md`). It falls back to a **review-gate** (artifact + rubric, the judgment-point exit below — never a fake green) *only* when no honest command exists. **Architecture** and **Conventions & Style** are the always-on backbone (§6.1, not walked in the Step 5 pass); the rest are **contextual — a point fires them by what it Touches**, and each maps *differently* per point AND per repo (that's the mutation):

| Axis | Fires when the point Touches… | Verified by — a done-signal fragment in *this repo's* tooling (review-gate only if no honest command) |
|---|---|---|
| **Architecture** | *(backbone — §6.1, not in the Step 5 pass)* | the repo's arch/dependency lint or module-boundary test (depcruise, ArchUnit…); else grounded review vs `foundations.md` |
| **Conventions & Style** | *(backbone — §6.1, not in the Step 5 pass)* | the repo's linter/formatter green + the self-documenting grep (no inline comments); else style review |
| **Security** | authz, external input, secrets, paths, queries, crypto | authz test over the route table (count-asserted) · the repo's secret-scan/SAST green · a parameterized-query lint; else a security review-gate |
| **Performance** | a hot path, a loop over N, I/O in a request, alloc in a tight loop | a threshold in the repo's bench harness · a query-count assertion (no N+1); else a perf review-gate — and flag if the repo has no bench harness |
| **Concurrency** *(Threading)* | shared mutable state, async, parallel access, locks | the language's strict-concurrency/race flag + a concurrent/stress test; else a concurrency review-gate |
| **Correctness** *(Bugs)* | a finite case-set (errors, states, endpoints), boundary/edge inputs | a count-asserted table test over EVERY case · property/fuzz over malformed input |

**Derive each point's quality checks from its `Touches`, and fold them into its done-signal — not a side note.** As you write a point, read its `Touches`/Goal against the catalog; every axis it fires becomes a runnable fragment of that point's **done-signal**, wired to the repo's own tooling (from `reference.md`) — e.g. a point touching `POST /orders` adds an authz test to its suite; a point touching the scheduler runs under the strict-concurrency flag. Only when no honest command exists does the axis become a **review-gated** criterion instead (the judgment-point exit, below — never a fake green). This is what makes the dimension **part of what's implemented**: it's in the gate the loop checks, mutated to this point and this repo, not a generic checklist. **An axis lives in exactly ONE place:** §6.1 if it fires for *every* point (firing points inherit it, don't restate it — Convention 12), else the firing point's done-signal/Acceptance. A point that fires *no* contextual axis just leans on §6.1 — that's fine, don't manufacture one.

## Step 6.5 — Validate the plan (self-consistency lint)

Once the briefings are drafted, **lint the wired plan before handoff** — catch a broken pipeline now, not mid-execution. This is a reasoning check (read what you wrote; no script, no new artifacts), distinct from the Step 6 checkpoint: that validated the *cut* with the user, this validates the *wiring*. Re-run it whenever the decomposition changes (incl. on Resume).

- **Pipeline wired** — every point's `Depends-on` resolves to a real upstream point (or existing code in `reference.md`) that provides what this point needs: no dangling dependency, no point whose output nobody needs (a dead-end usually means a missing or over-built point).
- **Graph is a DAG** — no dependency cycles; it topologically orders into the waves. No orphan/unreachable point (unless a deliberate parallel track).
- **Parallel-safe** — points in the same wave have **disjoint `Touches`** (else flag for isolated worktrees or serialize).
- **Every point loop-ready** — passes its DoR: single responsibility, runnable done-signal, no open user-owned decision inside it.
- **Contract churn guard** — if `design-contract.md`/`api-spec.md` sections changed since the last `log.md` entry, every point citing those sections must have been reconciled; otherwise the plan is **not ready to tackle**. A contract that is still mutating means decomposition happened too early (return to Step 5.75). Report churn explicitly: which sections moved and which points reference them.
- **Quality dimensions derived** — every point's *fired* axes (from its `Touches`, per the catalog) are folded into its done-signal (or review-gated if no honest command exists), wired to the repo tooling in `reference.md`; a point that fires none just leans on §6.1 (expected, not a gap); initiative-wide axes live in §6.1, not restated per point.
- **Deferral & questions sound** — every Deferred point names its blocking `Q-xx`; every `Q-xx` has an owner + what it Determines; no user-owned doubt left silent (Decision ownership).
- **Q-guard** — an active point (not Deferred) may not depend on an unresolved user-owned `Q-xx`. If the point's `Depends-on`, `Touches`, or done-signal assumes a decision that is still open, the point is Deferred until that `Q-xx` is resolved. This prevents replanning the same point when the decision flips.
- **Depth artifacts coherent** (when they exist) — `design-contract.md`: every section maps to ≥1 implementing point, every contract-implementing point cites its section; `foundations.md`: every new abstraction in the points has a grounding row; `team.md`: team sizing matches point complexity; `board.md`: status reflects `plan.md` §5 and execution progress.

A plan that fails the lint is **not ready to tackle**: fix it, or surface the unresolvable item (e.g. a `Q-xx` with no owner) to the user. Report the lint result in the handoff ("pipeline wired ✓, 0 orphans, 2 parallel pairs worktree-flagged").

## Step 7 — Compose with available skills (optional, planning aids only)

If present, use them to **PLAN, not execute**: **superpowers** (`brainstorming` to refine a point's design, `writing-plans` for its step breakdown → store in `specs/`/`plans/`, link from the point; `executing-plans` is for later, outside Tackle) · **karpathy-guidelines** (applies throughout) · a **SOLID/clean-architecture** skill (design decisions while shaping a point). If absent, plan with your own judgment and note the gap once (don't re-nag). Install URLs: superpowers `github.com/obra/superpowers` · karpathy `github.com/multica-ai/andrej-karpathy-skills` · solid `github.com/ramziddin/solid-skills`.

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
2. **Language**: all workspace artifacts are written in **English**, regardless of the conversation language.
3. **Questions only in `questions.md`**; **closed decisions only in `decisions.md`** (`D-id`, "don't revisit without cause", append-only by superseding).
4. **Canonical state = last `log.md` entry; execution status = `board.md`.** Don't duplicate either elsewhere.
5. **Ground in code, don't infer.** Every claim carries a `file:line` verified against the repo.
6. **No new files without reason.** New file → update README + AGENTS maps.
7. **Don't touch out-of-scope** (see `plan.md` §Non-goals).
8. **Verification = the point's done-signal + `plan.md` §6.1.** A point is done when its done-signal passes and §6.1 holds. **Loop budget (default): 3 attempts, then STOP and escalate** (a point overrides this only in its own Acceptance).
9. **Contract supersede-first** (if `design-contract.md` exists): implement it as written; a genuine deviation supersedes the spec (edit it + add a `D-xx`) BEFORE the divergent code.
10. **Grounding** (if `foundations.md` exists): a new pattern/abstraction does not merge without its decision → principle → source row; "it felt cleaner" is not grounding.
11. **Fixed status vocabulary** (in `plan.md` §5 and `board.md`): 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done. Don't invent variants — digests depend on it.
12. **Single-source the per-point acceptance** in `plan.md` §6.1; points reference it, never restate it (the bar itself: Step 6).
13. **Quality loop** (multi-agent execution): a code-quality guardian runs per point before it flips 🟢 — see `execution-strategy.md` / `team.md`.
14. **Best practices are the backbone**: Clean Code + SOLID. **Self-documenting code** — no explanatory inline comments; doc-comments on the public surface only, the *why* in commit bodies / these docs.
15. **Decisions carry their why; questions carry what they determine.** A `D-xx` records the rationale + tradeoff (`decisions.md` template). A `Q-xx` records what its answer unblocks + what you already investigated — don't ask others what the codebase can tell you.

*(Process rules live in their Steps, not here: best-practices/self-documenting backbone → 5.5; parallelism → 6; the quality-guardian loop → `execution-strategy.md` / `team.md`; external-dep snapshots → 5.)*

## Step 8 — Resume (re-invocation)

Re-entering an existing plan under `docs/plans/<initiative>/`: read `AGENTS.md` → the **State snapshot** in the last `log.md` entry → `decisions.md` (what's settled) → `questions.md` (blockers) → the relevant `points/P-0N.md` → and, **if they exist**, `design-contract.md` (the surface the point implements), `execution-strategy.md` (which wave/loop you're in), `team.md` (execution protocol), and `board.md` (current status).

**Open with a digest, not silence:** before continuing, show the user where things stand in the **digest format** (Step 9), and re-ask any user-owned open `Q-xx` directly in chat. Then refine.

**Re-validate the active point against the *current* repo** (only the active point — not inactive ones):
- **Grounding**: its `file:line` claims still resolve; if the code drifted, update the point's Context.
- **Done-signal**: its exit command still exists and is still the right check (tooling/paths/test names didn't move); fix it if stale.
- **Contract**: any `design-contract.md` section it implements hasn't been superseded since the briefing was written (if it was, reconcile the point or the spec — supersede-first).
- **Wiring**: if you add/split/re-wire points, re-run the **Step 6.5 lint** before handing back.
- **Hard drift**: if the grounding is *structurally* broken (touched files renamed/deleted, the done-signal's target gone — not just shifted line numbers), patching line numbers is the wrong move — the **decomposition itself may be stale**. Flag it and offer the user a re-decompose rather than handing back a plan whose other points silently rotted.

Note every drift you fixed in a new log entry; never rewrite old ones. Tackle keeps planning/refining — it never starts implementing.

**Old-format plan?** If the workspace predates the current methodology (no `Methodology:` stamp in `AGENTS.md`, or points with no done-signal / `Depends-on`+`Touches` / no `plan.md` §6.1), don't silently plan on top of it — offer **Migrate** (Step 8.5) first. If the user declines, Resume as-is (refine existing points in their old shape) — don't mix new-methodology points into an old plan; that half-and-half drift is exactly what migration prevents.

## Step 8.5 — Migrate an old plan to the current methodology

A plan from an earlier Tackle version lacks today's structure (done-signals, §6.1 universal acceptance, `Depends-on`/`Touches`, decision-ownership markers, judgment-point gates, the depth artifacts). **Migrate the structure; preserve the history. Do NOT re-plan.**

1. **Detect the gap (structure is the truth, the stamp is a hint).** A plan is old if ANY holds: no/old `Methodology:` stamp (in `AGENTS.md`, or for a Lite plan in `plan.md`'s header), points without a done-signal, no `Depends-on`/`Touches`, no `plan.md` §6.1 — same OR-symptoms Step 8 uses. A stamp can lie; trust the structure. Note what's missing and which of today's depth-artifact triggers (Step 4) now fire for this initiative. **Migration is per-point and idempotent:** a point that already has a done-signal + `Depends-on`/`Touches` is migrated — skip it; this makes an interrupted migration safe to re-run (bump the stamp only when every remaining point is migrated).
2. **Preserve what's settled.** `log.md` stays append-only (add a migration entry — never rewrite history); `decisions.md`/`questions.md` are kept as-is; `plan.md` §5 statuses are preserved. Migration doesn't re-litigate closed decisions.
3. **Scope to forward-looking work only.** Migrate points still 🔴/🟡/⏸ — the ones that will still be executed. 🟢 **done points are history; never retrofit done-signals onto completed work** (don't re-verify them either — but if you notice in passing that a 🟢 point's grounding is gone, flag it, don't silently trust the green). A 🟡 point someone is mid-flight on: confirm before rewriting it (don't yank the rug).
4. **Re-ground (all remaining points, not just the active one).** Old plans drift — re-validate every remaining point's `file:line` against the current repo (the one time you re-check inactive points). Structural drift → offer a re-decompose (Step 8 hard-drift branch) instead of patching; if the whole decomposition is archaeology, recommend a fresh **Create**, not a migrate.
5. **Backfill the full current shape, gate-appropriate.** Create `plan.md` §6.1 + the §5 dependency graph (from the new `Depends-on` edges). For each remaining point bring it to the current `point.tmpl` shape: a runnable **done-signal** (or mark it a judgment point) — folding away the legacy "Verification" section — `Depends-on` (+ what it needs) and `Touches`, a **starting prompt** and the **Definition of Ready** if missing, and Acceptance rewritten to reference §6.1. Apply the cross-cutting rules (self-documenting, rollout-if-production). Create only the depth artifacts whose triggers now fire — and if a contract/foundations artifact newly applies, wiring the existing points to it IS real work: flag it to the user, don't smuggle a re-plan. **Lite plan?** Migrate in place into `lite-plan.tmpl` shape (done-signal + open-questions + rollout-if-prod), no `points/`/§6.1/graph; stamp goes in `plan.md`'s header.
6. **Lint + checkpoint.** Run the **Step 6.5 lint** on the migrated plan, then present the migration diff in chat (what changed · what was preserved) and get the user's OK (decision-ownership; provisional if delegated).
7. **Record it.** A `D-xx` ("migrated to Tackle <ver> methodology"), a migration `log.md` entry, and bump the `Methodology:` stamp (in `AGENTS.md`, or the `plan.md` header for Lite) — only once every remaining point is migrated. Migration writes no implementation code — it's planning.

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

**Status** — "how is it going?": read-only digest from `board.md` + last log snapshot. Also:
- External packets 🟡 past their `Follow-up by` date → flag explicitly for chasing.
- **Questions owned by the user → re-ask them directly in chat**, with the options already drafted in `questions.md`/the packet. Don't just point at files.
- Drift: spot-check the active point's `file:line` claims, its **done-signal command**, and any `design-contract.md` section it implements against the current repo; warn on any that moved (full re-validation is Resume's job, not status').
- Reconcile if stale: execution happened but `board.md` wasn't updated (code merged, board still 🔴) → fix `board.md` + append a log entry noting it. That's the only write a status check makes.

**List** — "what plans are there?": scan `docs/plans/*/`; one line each: name · gate level · X/Y done · blocked on · last activity (newest log entry date). Call out zombies (stale, nothing blocking them).

**Next** — "what's next?": pick the next unblocked point; present its **pre-attack summary** (Step 7.5), THEN its ready-to-paste starting prompt + acceptance one-liner. The user should never open a file to start — and should know what they're greenlighting first.

**Closing the initiative:** when every point is 🟢 — append a final log entry (outcome + learnings worth keeping), set the README status line to `DONE`, and ask the user whether to keep, archive, or delete the folder (consistent with the Step 3 gitignore choice).

## Definition of Done (planning complete)

- [ ] Full-gate: design contract is stable before decomposition (Step 5.75); no contract churn since the last `log.md` entry unless every affected point is reconciled.
- [ ] Intake anchor is recorded in `log.md` (Step 1.5): problem, observable result, top 2 non-goals, and highest-shape decision.
- [ ] Gate level chosen and justified (Step 2).
- [ ] Location set under `docs/plans/<initiative>/`; gitignore 3-way answered (Step 3).
- [ ] `plan.md`: objective, non-goals, current state (grounded), point decomposition + dependency graph complete.
- [ ] `plan.md` §4 **leads with the de-risking finding** and cites the **precedent** the approach mirrors.
- [ ] Universal per-point acceptance defined once in `plan.md` §6.1; points reference it.
- [ ] If production-facing: rollout/reversibility (flag, canary, no-op check) is planned (§7 + the point).
- [ ] Quality dimensions handled gate-appropriately — **Full:** Step 5 pass (incl. discovering the repo's quality tooling into `reference.md`) + per-point derivation from `Touches` (Step 6), each firing axis folded into its point's done-signal (review-gated only if no honest command) or, if initiative-wide, a §6.1 invariant; **Lite/None:** the plausible-touch walk only. Surprising skips recorded as non-goals; none skipped silently.
- [ ] Full-gate depth artifacts created **only where their trigger fired** (`foundations.md` / `design-contract.md` / `execution-strategy.md` / `team.md` / `board.md`) — not by default.
- [ ] Architecture chosen by the user from a gate-appropriate recommendation (Step 5.5), recorded as a `D-xx`; Full plans open `foundations.md` with the Clean Code + SOLID backbone.
- [ ] Decomposition cuts for parallelism; `execution-strategy.md` names the waves + the **code-quality guardian** loop (when multi-agent), and `team.md` names the team sizing.
- [ ] Every point is **loop-ready**: one responsibility, a runnable **done-signal**, `Depends-on` + `Touches` wired.
- [ ] Plan passes the **Step 6.5 lint**.
- [ ] External deps snapshotted into `reference-docs/` when the plan leans on out-of-repo material (Step 5).
- [ ] Every point has a self-contained briefing that passes its **Definition of Ready**.
- [ ] Blocking questions are either resolved (→ `decisions.md`) or explicitly flagged in `questions.md` with owners.
- [ ] `log.md` has this session's entry with a current State snapshot; `README.md` / `AGENTS.md` maps are accurate.
- [ ] The user saw the plan: decomposition validated in chat (Step 6 checkpoint) and handoff summary presented (Step 7.5).
- [ ] Every doubt was surfaced to the user as a decision; no silent assumptions (provisional `Q-xx` only where the user delegated).
- [ ] No implementation code written — Tackle planned, it did not execute.

## Common mistakes (each → its home rule)

A scan-list of failure modes; the rule lives in the cited home, not here.
- Flat list when staged · no parallelism · bundling two concerns ("and") · non-runnable done-signal · aspirational acceptance · restating the §6.1 bar per point · writing full point briefings before the skeleton board is approved · decomposing while the design contract is still churning → Step 6 (and Step 5.75).
- Silent assumptions · drip-feeding or un-defaulted questions · interrogating about inferable facts → Decision ownership + Cadence.
- Over-sizing the gate · heavy architecture on Lite · picking the architecture *for* the user → Step 2, Step 5.5.
- Gitignore decided silently → Step 3. · Depth artifacts by default → Step 4.
- Burying the de-risking finding · inventing when a house pattern exists · rollout as afterthought · skipping a quality dimension (security/perf/concurrency/correctness) silently, or letting it stay prose instead of folding it into the firing point's done-signal / §6.1 (or a review-gate when no honest command exists) → Step 5 pass + Step 6 catalog. · no `reference-docs/` snapshot → Step 5.
- Flat list when staged · no parallelism · bundling two concerns ("and") · non-runnable done-signal · aspirational acceptance · restating the §6.1 bar per point · writing full point briefings before the skeleton board is approved → Step 6.
- Dangling dependency · cycle · orphan · colliding parallel `Touches` → run the Step 6.5 lint.
- Files written but nothing in chat · point handed off without its pre-attack summary → Step 7.5 / Step 9.
- Duplicating status / `file:line` across files · point not self-contained → Conventions 5, 7, 8.
- Resuming without re-validating the active point (file:line, done-signal, contract drift) → Step 8.
- Planning on top of an old-format plan, or re-planning it from scratch instead of migrating → offer Migrate (Step 8.5): upgrade structure, preserve history, forward-looking points only.
- Treating a status ask as a re-plan · walls of text, no clear ask → Step 9 / Output contract.
