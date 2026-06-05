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

Applies to **every** Tackle chat response, in every mode. The user must never have to dig through prose to learn whether action is needed:

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

## Step 1 — Intake (infer first, then ASK to contextualize)

**Infer before asking — turn the interrogation into a confirmation.** First detect what the environment already tells you: ticket ID from the branch name (`feature/MBTX-4488` → MBTX-4488), repo from the working directory, sibling plans under `docs/plans/`, ticket content via your issue-tracker integration if one is available. Present what you inferred as *"this is what I already know — confirm or correct"*, and ask — **one batched set of questions, not drip-fed** — only the real gaps. Never silently assume what you didn't verify. Cover at least:
- **The explicit requirement** — the ask in the user's words; ticket ID / link if any.
- **Documentation** — relevant docs, specs, design notes, API/vendor docs, links, files to read.
- **Scope hints** — what's in, what's explicitly out, deadlines, target validation, related/sibling work.
- **Decision owners & external deps** — who decides open questions, which teams to ask.
- **Codebase** — confirm the repo/path Tackle is running against.

Read what they point you to. Record what was gathered in the first `log.md` entry; it feeds `plan.md` and `reference.md`.

If the intake surfaces questions that need another team, note them as draft Qs and create
`external-questions/` packets as soon as they become concrete.

**Thin / deferred answers** ("just figure it out", partial replies): never block on intake. Proceed with what you have, recover the rest from the codebase, and record every gap as a `Q-xx` in `questions.md` — mark the ones you proceeded on as **assumptions**. Surface the gaps; don't silently invent answers.

**If the user says "just figure it out" or gives thin answers**, still record three things:
  1. What you assumed.
  2. What you couldn't verify.
  3. The risk of each assumption.
Each becomes a `Q-xx` in `questions.md`; mark them as **assumptions** so they're visible.

## Step 2 — Size the initiative (gate)

Do NOT scaffold a full workspace for everything. Pick a level:

| Level | When | Examples | Produces |
|---|---|---|---|
| **None** | Single obvious change, <~3 steps, no unknowns | typo, rename a local, bump a constant | No workspace. Just plan inline. |
| **Lite** | Single-session, bounded scope, a few unknowns | add one validation to an existing endpoint, plumb a field already wired | `plan.md` + `log.md` + `todo.md` only (`references/lite-plan.tmpl.md`) |
| **Full** | Multi-session OR multi-track OR multi-team OR high uncertainty OR handoff expected | introduce a new subsystem, multi-module refactor, feature spanning sessions | Full core + `points/` + appendices |

When unsure between Lite and Full, start **Lite**; it upgrades by adding `README.md` / `AGENTS.md` / `reference.md` / `points/`.

**Bigger workspace ≠ better plan.** Over-sizing burns effort and buries the work in ceremony; under-sizing loses context across sessions. Match the level to the real shape — don't default to Full because it feels thorough. If **None**: stop here.

**Tie-breaker:** touches ≥2 modules OR changes the public API → **Full**. Confined to one file with no public surface change → **Lite**.

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

**Optional:** `external-questions/` — packets to send to other teams → `references/external-question.tmpl.md` (create only when a question goes external).

If using superpowers for depth, also create `specs/` and `plans/` as needed (not scaffolded by
default — create them when you start using `brainstorming` / `writing-plans`).

**Appendices (free, descriptive names — NOT numbered):** add only when needed (`error-catalog.md`, `design-strategy.md`). When you add one, update the `README.md` and `AGENTS.md` file maps.

## Step 5 — Briefing (ground it in the codebase)

Investigate the actual repo and fill `plan.md` / `reference.md` from it, not from assumptions:
- **Objective + expected result**: observable outcome.
- **Non-goals**: explicit out-of-scope — prevents scope creep.
- **Current state**: every claim about code cites `file:line`, verified with your code-search / find-references tools — not memory.
- **Domain invariants / constraints**: consult the authoritative source for the domain (spec, domain MCP, canonical constants) if your environment has one; else use the repo's own constants and annotate.
- **Boundary**: `reference.md` holds facts shared by ≥2 points. Most Context in a point will simply link to `reference.md`; a point only needs unique Context when it touches code no other point touches.

## Step 6 — Decompose into points (the heart)

Break the initiative into **independent points** (work units) with a dependency graph in `plan.md`. IDs are zero-padded: `P-01`, `P-02`…

**Checkpoint — validate before writing briefings:** present the point table + dependency graph **in chat** and get the user's OK before writing the `points/*.md` files. Redoing a table is cheap; redoing N briefings is not. Adjust the cut on feedback, then write.

For each point write `points/P-0N-<slug>.md` from `references/point.tmpl.md` so a cold agent can resolve it **from that file alone**. Each point MUST include: Goal · grounded Context (`file:line`) · Non-goals · **Recommended approach** · **Alternatives / fallbacks** · **Recommended starting prompt** (ready to paste in a fresh session, on any model) · Acceptance · Verification · Dependencies · linked open questions · a **Definition of Ready** self-check. A point links to deeper artifacts instead of duplicating them. Per-point execution status lives only in `plan.md` §5.

**Point size rule**: a point should be completable in one focused session (1–3 hours of work).
If it's bigger, split. If it's smaller than 30 min, merge with a sibling.

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

Never end a planning session by silently writing files. Close **in chat** with:
- Gate level + workspace path.
- The point board in the **digest format** (Step 9) with the suggested attack order (from the dependency graph; flag what can run in parallel).
- What's blocked and on whom — especially anything that needs the **user** (open `Q-xx`, external packets to send).
- The recommended **first point** and its ready-to-paste starting prompt.

The user should know what to do next without opening a single file.

## Conventions (baked into the templates)

1. **Log append-only**: one entry per session (`## YYYY-MM-DD · session N · <title>` → Did / Decisions / Blockers / Next). Never rewrite old entries. No secrets.
2. **Questions single-source** in `questions.md` (`Q-01`…). External ones also as packets in `external-questions/`.
3. **Canonical state = last log entry.** README/AGENTS link to it; they do NOT duplicate status.
4. **Decisions single-source = `decisions.md`** (`D-01`…, "don't revisit without cause", append-only by superseding). A resolved `Q-xx` becomes a `D-xx`; the log links the `D-id`.
5. **One per-point status board = `plan.md` §5.** `point.md` and `todo.md` don't duplicate execution status (`todo.md` tracks *planning readiness* — a different axis).
6. **Logs stay terse; the newest entry carries a State snapshot** sufficient to resume without re-reading history. Keep entries short — append-only ≠ verbose.
7. **Ground in `file:line`** from the codebase. No claim about code without a verified reference.
8. **Points are self-contained.** A point links to depth, but carries enough to be solved standalone on any model.
9. **No new files without reason.** New file → update README + AGENTS maps.
10. **Fixed status vocabulary** (in `plan.md` §5 and external packets): 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done. Don't invent variants — digests depend on it.
11. **Status flows back via the executor contract** in the workspace `AGENTS.md`: whoever works a point (any agent, any session) updates `plan.md` §5 + appends a log entry. Tackle doesn't execute, but it plants the contract so tracking survives execution.

## Step 8 — Resume (re-invocation)

Re-entering an existing plan under `docs/plans/<initiative>/`: read `AGENTS.md` → the **State snapshot** in the last `log.md` entry → `decisions.md` (what's settled) → `questions.md` (blockers) → the relevant `points/P-0N.md`.

**Open with a digest, not silence:** before continuing, show the user where things stand in the **digest format** (Step 9), and re-ask any user-owned open `Q-xx` directly in chat. Then refine.

**Re-validate before continuing** the active point: re-check ONLY the active point's grounded
`file:line` claims against the *current* code — the repo may have drifted since planning.
If it drifted, update that point's Context and note the drift in a new log entry. Don't
re-verify inactive points. Append a new log entry as you work; never rewrite old ones.
Tackle keeps planning/refining points — it never starts implementing.

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
- Drift: spot-check the active point's `file:line` claims against the current repo; warn if it moved.
- Reconcile if stale: execution happened but §5 wasn't updated (code merged, board still 🔴) → fix §5 + append a log entry noting it. That's the only write a status check makes.

**List** — "what plans are there?": scan `docs/plans/*/`; one line each: name · gate level · X/Y done · blocked on · last activity (newest log entry date). Call out zombies (stale, nothing blocking them).

**Next** — "what's next?": pick the next unblocked point from the dependency graph and print its **ready-to-paste starting prompt** (from `points/P-0N-*.md`) right in the chat, with its acceptance one-liner. The user should never have to open a file to start working.

**Closing the initiative:** when every point is 🟢 — append a final log entry (outcome + learnings worth keeping), set the README status line to `DONE`, and ask the user whether to keep, archive, or delete the folder (consistent with the Step 3 gitignore choice).

## Definition of Done (planning complete)

Tackle is done when **the initiative is ready to be tackled**, not when code is written:
- [ ] Gate level chosen and justified (Step 2).
- [ ] Location set under `docs/plans/<initiative>/`; gitignore 3-way answered (Step 3).
- [ ] `plan.md`: objective, non-goals, current state (grounded), point decomposition + dependency graph complete.
- [ ] Every point has a self-contained briefing that passes its **Definition of Ready**.
- [ ] Blocking questions are either resolved (→ `decisions.md`) or explicitly flagged in `questions.md` with owners.
- [ ] `log.md` has this session's entry with a current State snapshot; `README.md` / `AGENTS.md` maps are accurate.
- [ ] The user saw the plan: decomposition validated in chat (Step 6 checkpoint) and handoff summary presented (Step 7.5).
- [ ] No implementation code written — Tackle planned, it did not execute.

## Common mistakes

- Treating Tackle as an executor → it only plans. Stop at "ready to tackle".
- Assuming Claude-only tools/skills → name capabilities, use what the environment has, do the rest by hand.
- Planning without intake, or blocking on thin intake → ask batched (Step 1); on gaps, proceed + record assumptions as `Q-xx`.
- A point that needs the rest of the workspace to be understood → not self-contained. Fix it.
- Duplicating per-point status across plan/point/todo, or the same `file:line` in reference + point → drift.
- Defaulting to **Full** for a small change → ceremony. Match the gate to the real shape.
- Deciding the gitignore treatment silently → always ask the 3-way (Step 3).
- Resuming without re-validating grounded claims → stale plan. Re-check `file:line` first.
- Writing all the point briefings before the user validated the decomposition → rework. Checkpoint first (Step 6).
- Ending with files written but nothing presented in chat → the user shouldn't need to open files to know what's next (Step 7.5 / Step 8 digest).
- Treating a status ask as a resume → don't re-plan; give the digest (Step 9).
- Interrogating the user about things the environment already knows (branch, repo, ticket, siblings) → infer first, confirm after (Step 1).
- Burying user-owned questions in `questions.md` → re-ask them in chat on every resume/status (Steps 8–9).
- Walls of text in chat — restating file contents, multiple suggested actions, no clear ask → Output contract: status line, ≤12-line digest, one action footer.
