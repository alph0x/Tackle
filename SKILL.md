---
name: tackle
description: Use for durable planning and explicit point-by-point execution of multi-session work, including migration, verification, status queries and retrospectives.
---

# Tackle

**Tackle 8.0.0** is a model-agnostic planning and execution method. It keeps the install artifact Markdown-only: `SKILL.md` plus `references/`.

## Public surface

Tackle has two primary actions and one read-only query:

| Surface | Use | Result |
|---|---|---|
| **PLAN** | `/tackle-plan` | Intake, specification, contract, decomposition, readiness and handoff. It prepares; it does not execute source work. |
| **RUN** | `/tackle-run`, `/tackle-run --one`, or `/tackle-run <P-id>` | Explicitly authorized implementation, target and surrounding checks, bounded correction, integration and close or block. |
| **STATUS** | `/tackle-status [<workspace>]` | Read-only status, list, next and unqualified resume queries. `--handoff` writes only its requested projection. |

`/tackle-init` forwards to PLAN scaffolding. `/tackle-verify` is internal PLAN validation or an explicitly requested diagnosis. `/tackle-judge` is an explicit post-work audit. `/tackle-retro` is optional learning review. A diagnostic question, `status`, `next`, or plain `resume` never authorizes a fix or source, board or log write; only an explicit resume request that also states execution intent can enter RUN.

During 8.x, legacy routes forward to the one applicable protocol while preserving intent: `implement` → RUN, `ground`/`trace`/`drill` → PLAN validation, `pulse`/`list`/`next`/`resume` → STATUS, and `handoff` → STATUS `--handoff`. They are compatibility aliases, not additional primary commands, and retire in 9.0 with this forwarding guidance retained for migration.

## PLAN and RUN

Resolve relative links from this file; locate missing references before retrying.
Select the route once with [`intake-and-gate.md`](references/guides/intake-and-gate.md). **None** uses its bounded preflight, edit and
receipt without a workspace. **Lite** uses only [`lite-plan.tmpl.md`](references/lite-plan.tmpl.md):
it contains the complete preparation, execution, minimal plan/log/usage and closure procedure.
Follow that path instead of the Full map below. Open another guide only for a missing capability.
**Full** uses the detailed PLAN/RUN guides. All routes retain the core conventions. Lite/Full completion requires accessible final evidence
and verified mandatory coverage; otherwise block the affected scope. Unknown telemetry stays non-gating.

Full PLAN reads the repository and named inputs, records requirements and decisions, builds self-contained Points, checks both positive and negative acceptance cases, validates dependencies and scope, and produces a handoff. A Point states its purpose, requirements, grounded surfaces, write limits, interfaces, errors, invariants, cases, non-goals, approach, alternatives, target/surround checks, recovery and evidence. Exact bytes, order, schema, paths, standard streams and exits apply only when specified; otherwise valid semantic equivalents remain valid.

Full RUN starts only after explicit execution intent and a current Ready Point, or the bounded None preflight. It reads the current contract, dependency outputs, environment, board and log where applicable, freezes protected expectations, writes only declared Touches, and records actual observations. The target check is followed by surrounding and affected integration checks, then global acceptance before initiative close. One persistent pool permits at most three failed correction-validation cycles per Point; two identical no-progress observations stop sooner. Non-implementation, contract, validator, environment, capability and unresolved causes stop with an evidence packet rather than a silent replan or model upgrade.

Mechanical execution, focused semantic review and adversarial audit are separate capabilities. The same agent may report a command observation but cannot call its own review independent. Missing isolation is unavailable evidence, never an invented grade. Historical E0–E3 grades remain readable; new evidence records provenance and independence. Unknown telemetry is `n/a`, never zero. Board is canonical current state; log is append-only history; interrupted work is `observe-incomplete`; completed, blocked, skipped and unverifiable remain distinct.

## Migration and distribution

Migrate only a selected active 7.3 workspace, on a disposable copy first. Preserve contracts, evidence, statuses, log bytes and usage bytes; compile only remaining unstarted work; mark readiness pending until checked; adopt at a Point boundary; keep an interrupted Point on its pinned procedure until that boundary. Rollback restores the copy checkpoint and leaves neighboring files intact. Closed or unrelated workspaces are not automatically migrated. See [`migrate.md`](references/guides/migrate.md) for the 7.3 → 8.0 checklist.

Ordinary invocation performs no network access or installation-tree mutation. Release remains a separately authorized owner action after the eight self-lint gates, catalog/workspace sweep and behavioral evidence. Public docs and examples must not leak `docs/plans/` state; profiles are written only by retro after confirmation, and seeds are deliberate writes.

## Core conventions

1. **Authority order** — user > specification/contract > protected tests/acceptance > current implementation; surface contradictions instead of hiding them.
2. **Grounding** — every claim relies on a verified `file:line` citation or an explicitly historical reference; stale citations are re-anchored before use.
3. **Scope** — write only declared Point Touches and authorized workspace artifacts; preserve unrelated edits and neighboring files.
4. **Plan contract** — every Point carries observable purpose, stable requirements, interfaces, cases, constraints, non-goals, approach, checks and recovery, omitting only inapplicable fields.
5. **One responsibility** — one Point has one responsibility and an observable acceptance target,
   runnable where honest and otherwise covered by the named REVIEW rubric and actual reviewer;
   declared semantic alternatives remain valid when exact output is unspecified.
6. **Run discipline** — explicit intent precedes mutation; follow the current procedure, classify failures, and use the shared three-cycle correction budget. Apply [code-style rules](references/guides/design-and-contract.md#code-style).
7. **Evidence and independence** — capture actual command, cwd, runtime, actor, revisions, output, exit/timeout/signal and artifact hashes during execution; reconstructed prose is not raw evidence. A wrapper PASS cannot hide a child failure, and unavailable independent review stays unavailable.
8. **State and independence** — board is current status; log is append-only history; questions and decisions have their own files; interrupted roles record `observe-incomplete`. Mechanical observation, semantic review and adversarial audit are distinct; unavailable isolation stays unavailable and grades are derived from evidence.
9. **Decision ownership and scaffold consent** — the user owns product and contract decisions; reversible technical choices are delegated within the Point's freedom, while a changed acceptance or contract requires a superseding decision first. PLAN asks about gitignore for `docs/plans/` and applies the same decision to `docs/seeds/`.
10. **Learning consent** — retro may propose cause-based lessons and archetypes, but profile writes require separate explicit confirmation; seeds are deliberate, and evolution may be paused or stopped.
11. **Harness agnosticism** — use generic capabilities and report actual model, effort, tools and telemetry; never fabricate a binding or assume a vendor mechanism.

## Output

Open with one status line. Close with `⚠️ On you: ...` and `▶ Continue: ...`. Keep a digest to 12 lines and point to files rather than pasting them.

## Full guide map and explicit queries

PLAN: [`intake-and-gate.md`](references/guides/intake-and-gate.md), [`scaffold.md`](references/guides/scaffold.md), [`design-and-contract.md`](references/guides/design-and-contract.md), [`decompose-and-lint.md`](references/guides/decompose-and-lint.md), [`verify.md`](references/guides/verify.md). RUN: [`run.md`](references/guides/run.md). STATUS: [`status.md`](references/guides/status.md). Explicit audit: [`judge.md`](references/guides/judge.md). Optional learning: [`retro.md`](references/guides/retro.md). Migration: [`migrate.md`](references/guides/migrate.md). Release checks: [`lint-spec.md`](references/guides/lint-spec.md). Updates are owner-controlled: [`update.md`](references/guides/update.md).
