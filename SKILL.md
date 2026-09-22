---
name: tackle
description: Use for durable planning and explicit task execution of multi-session work, including migration, validation, status and lessons.
---

# Tackle

**Tackle 8.2.0** is a model-agnostic planning and execution method. Install: Markdown-only `SKILL.md` plus `references/`. Release changes: changelog.

## Public surface

One entry: `tackle`. Select it, then state the request in any language. Action names do not register
host commands. Bare invocation or help offers brief choices without writes. Interpret the complete
request, including negation and quoted examples; see [invocation.md](references/guides/invocation.md).

| Surface | Request | Result |
|---|---|---|
| **PLAN** | `plan` | Prepare requirements, contracts, task briefs and readiness. PLAN-only stops before implementation. |
| **RUN** | `run`, `run --one`, `run <P-id>` | Execute authorized ready tasks, check, correct within budget, integrate and accept delivery. |
| **STATUS** | `status [<workspace>]` | Read-only status, list, next and plain resume. Explicit `--handoff` writes only its projection. |

Use **validate the plan**, **audit the result** and **review lessons** for `verify`, `judge` and
`retro`; `init` forwards to PLAN scaffolding. During 8.x, documented legacy aliases forward with
their original boundaries: `implement` → RUN; `ground`/`trace`/`drill` → PLAN validation;
`pulse`/`list`/`next`/`resume` → STATUS; `handoff` → STATUS `--handoff`. They retire in 9.0; migration
retains their interpretation. A diagnostic or standalone STATUS request authorizes no fix. An explicit resume request that also states execution intent enters RUN after preflight.

## PLAN and RUN

Resolve links from their containing file; locate missing references before retrying.
- **First:** inspect named owner prerequisites in a tool call containing **only those probes**. Wait for results.
- **Missing:** stop that scope; report affected work and owner action. No inventories, guides or implementation/capability discovery. Only required state/evidence recording and independently authorized work continue.
- **Otherwise:** read named inputs and retained records before guides; reuse routing or read [intake-and-gate.md](references/guides/intake-and-gate.md) alone through sizing.

**Direct (None)** uses that bounded procedure without a workspace; **Focused (Lite)** uses only
[lite-plan.tmpl.md](references/lite-plan.tmpl.md); **Coordinated (Full)** loads the needed operation.
More guidance requires a specific unresolved capability. Risk triggers precede task count; small
work needs no milestone/archive/storage machinery.

PLAN extracts supplied intent without reconfirmation. Compile sufficient task briefs with
requirements, observable outputs, cases, checks, decisions and current inputs. Separate hard requirements from
delegated technical choices; missing product behavior blocks consumers. Validate coverage,
dependencies, interfaces and semantic counterexamples. Cold probes retain their risk trigger and
bounded allowance. Long initiatives may prepare one milestone at a time: every requirement retains
an owner, later tasks remain Draft and only verified tasks become Ready to run.

Explicit PLAN+RUN authorization persists within scope. Answer status questions during active work
and continue; do not ask for execution permission again. Follow the shared [decision and
communication policy](references/guides/communication.md). Operational diagnosis uses permitted
tools; recovery never widens access, product requirements or authorization.

RUN records the pinned procedure, current contract, dependency outputs, environment and write
scope. Reuse verified current state and sufficient existing checks; do not append equivalent
assertions or unchanged closure reruns. Changed content, selector
membership, configuration, interfaces, runtime or freshness invalidate affected consumers. Unknown
dependencies require conservative checks. Record actual commands, complete results and preserved
inputs; use complete retained native capture or the scoped capture recipe. Distinct executions
remain distinct events even when immutable bytes are shared.

Task checks, related regression checks and affected integration checks precede task completion.
Deliverable acceptance precedes initiative completion. Three failed correction-validation cycles
per task and two identical no-progress observations bound implementation correction. Consume known
failure evidence; repeat its check only after a relevant change or permitted recovery. Lineage preserves spent cycles across
split, merge and resume. Classify other failures and stop affected
work with records; do not silently replan or upgrade a model.

<a id="migration-and-distribution"></a>
## Compatibility and state

[Terminology](references/terminology.md) defines visible names, exact state mappings and persistent
aliases. Keep P-ids, existing paths and historical records. New validated boards may use Draft,
Ready to run, In progress, Checking and Complete; Blocked, Interrupted, Skipped and Unverifiable
remain distinct. Complete means every mandatory task obligation passed. Historical E0–E3 codes
remain readable, never an ordinal scale. Report method, result and observed independence; a role
name or self-review cannot create independent evidence. Unknown telemetry stays `n/a`.

The task board is canonical current state; history is append-only; current-work projections are
reconstructable. Validate projections against authoritative inputs and checkpoints. Preserve original
history during reversible archival. Protect current, interrupted, unresolved and pinned verification
records; retired bytes cannot support reuse. Maintenance follows an authorized initiative policy;
STATUS never archives or cleans up.

Migrate only selected active workspaces on a disposable copy first, preserve history and correction
lineage, and adopt at an explicit task boundary. Interrupted tasks stay on their pinned procedure.
Ordinary invocation performs no network access or installation mutation. Releases require separate
authorization, eight self-lint gates, catalog/workspace sweep and required behavioral evidence.

## Core conventions

1. **Authority order** — user > specification/contract > protected tests/acceptance > implementation. Preferences and hypotheses cannot override this order.
2. **Reference verification** — verify claims against `file:line` or explicitly historical sources; re-anchor stale citations.
3. **Scope** — write only declared task scope and authorized workspace artifacts; preserve unrelated edits.
4. **Task contract** — include observable purpose, requirements, interfaces, cases, constraints, non-goals, approach, checks and recovery; omit only inapplicable fields.
5. **One responsibility** — one task has one coherent observable acceptance target; use an honest command or named review rubric and actual reviewer. Preserve valid alternatives.
6. **Run discipline** — explicit intent precedes mutation; pin procedure, classify failures and preserve shared correction budgets. Apply [code style](references/guides/design-and-contract.md#code-style).
7. **Records and independence** — capture actual command, cwd, runtime, actor, revisions, complete streams, exit/timeout/signal and artifact hashes. Every required assertion must propagate failure; `set -u`, `pipefail` or a final PASS alone cannot. Wrapper success cannot hide child failure; reconstructed prose is not raw evidence.
8. **State ownership** — board is current state; log is history; questions and decisions retain their sources. Reconcile `observe-incomplete` before repeating effects; grades derive from records.
9. **Decision ownership** — user owns product choices; reversible technical choices are delegated within scope. Changed acceptance needs a superseding decision. Reuse authorized plans/seeds gitignore choices, otherwise ask once.
10. **Learning consent** — select applicable, current lessons; incompatible hypotheses remain historical. Only retro writes profiles after confirmation; backlog ideas are deliberate writes.
11. **Provider independence** — report actual capabilities, model, effort and telemetry; never invent bindings or assume a vendor mechanism.

## Output

State the result or useful progress, observed checks and material uncertainty. Ask only when input
changes affected work. No mandatory footers; preserve necessary information over length targets.

## Full guide map and explicit queries

PLAN: [intake](references/guides/intake-and-gate.md), [scaffold](references/guides/scaffold.md),
[contracts](references/guides/design-and-contract.md), [readiness](references/guides/decompose-and-lint.md),
[validation](references/guides/verify.md). RUN: [run](references/guides/run.md).
STATUS: [status](references/guides/status.md). Explicit [audit](references/guides/judge.md),
[lessons](references/guides/retro.md), [migration](references/guides/migrate.md),
[release checks](references/guides/lint-spec.md), [owner-controlled updates](references/guides/update.md).
