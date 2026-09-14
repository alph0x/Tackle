## Update boundary (explicit user control)

Ordinary Tackle invocation performs no network access or installation-tree mutation. Updating is
never initiated by planning or execution; an owner may use the documented external/manual workflow
only after explicitly requesting it. Tackle provides guidance but does not perform that workflow.

# Step 1 — Intake (infer first, then ask)

Read this guide through sizing before creating artifacts or loading further guides. Intake anchors
apply to every gate, but logging, scaffolding, compiled Points and handoff below apply only to
durable Lite/Full workspaces. None records relevant profile-derived choices in its direct receipt.

Extract or confirm:
- Problem
- Observable result expected
- Top 2 non-goals
- Highest-shape decision

Do not assume; ground claims in `file:line`.

The four anchors are the intent contract: **explore intent** before proposing approaches — extract and confirm all four first. Infer first, then ask: propose your reading of the request and confirm it, don't ask open-ended. Batch remaining doubts with a recommended default each (convention 8). The anchors gate decomposition (Step 1.5). This guide is self-contained: intake needs nothing outside it — no external planning skills.

## Learning-loop read (if enabled)

If a profile exists at the relevant scope with `Evolution: enabled`, read it **before** proposing defaults:

- User profile: `~/.tackle/user-profile.md`
- Project profile: `.tackle/profile.md` in the repo root

Propose any profile-derived default explicitly tagged `(from your profile)`. These are proposals, never silent decisions — the user may accept or override each one.

Apply active `directive:` entries on top of the template-resolution stack when instantiating templates or briefings; project directives outrank user directives. A directive whose target section no longer exists is flagged **stale** for re-confirm-or-retire at the next retro. Directives tagged `applies_to:` are exempt from instantiation-time application — they bind at their action moment.

Record one tally line in the log's `### Intake (context gathered)` section:

```
profile proposals: N accepted, M overridden (<which>)
```

If the profile is absent, disabled, or no defaults apply, skip this step without logging a tally.

### Archetypes

Read `references/archetypes/` alongside the profiles. When an archetype's summary matches the incoming initiative's shape, offer its skeleton — point list, edge pattern, wave shape — as a proposal explicitly tagged `(from archetype <name>)`, flagging its trap warnings with the offer. These are proposals, never silent defaults: the user may accept, adapt, or override, and overrides are retro material.

If no archetype matches, skip without offering. There is no scoring engine — read and judge, exactly like profiles and seeds.

## Decision ownership

The user decides every product doubt. Batch doubts with a recommended default each; don't drip-feed.
Tag each 🔴 blocking or 🟡 proceed-on-default. Under delegation, every mandatory product choice
becomes a provisional `Q-xx` with your default. Reversible technical choices inside an explicitly
authorized Point are local freedom when their decision and evidence are recorded.

# Step 1.5 — Anchor the intake before sizing

Lock the problem, observable result, top 2 non-goals, and highest-shape decision before choosing a gate.

For a selected Lite route, `../lite-plan.tmpl.md` provides these preparation and execution steps in one place, including scaffold consent. The detailed guide sequence below is for Full.

## PLAN preparation order

PLAN is a preparation protocol, not a source-execution command. After the four anchors are
confirmed, keep the work in this order so that every later choice has an observable contract:

1. **Behavior and outputs** — turn each required behavior into a stable criterion id with its
   observable output, boundary cases, and allowed semantic alternatives. Name exact bytes, order,
   paths, stdio, or exits only when a consumer depends on them.
2. **Acceptance and test strategy** — give every criterion a target check, a surrounding check,
   and an evidence slot. Include negative fixtures for omitted behavior and invalid evidence.
3. **Contracts and decisions** — compile the interfaces, invariants, dependencies, and recovery
   rules that Points will consume. Resolve product choices as user-owned decisions; record
   reversible technical choices as local decisions.
4. **Decomposition and readiness** — create the scaffold, Points, coverage matrix, and bounded
   readiness review. A Point is not Ready merely because its requirement id appears in a briefing.

The preparation order is a single PLAN run. Do not wait for a later planning session before
stabilizing a contract or assigning Ready. A new session with unchanged relevant fingerprints may
reuse the recorded readiness evidence; changed inputs are handled by the selective revalidation
rule in `verify.md`.

Material product ambiguity blocks the affected criterion and its consumers. A reversible delegated
technical choice is recorded with its decision and evidence and does not block unrelated scope.

# Step 2 — Gate sizing (Full / Lite / None)

| Gate | Use for | Example |
|---|---|---|
| **None** | One-session, one product file, specified behavior, bounded correction or local edit | restore a whitespace normalization already required by tests/spec |
| **Lite** | Single-session, bounded scope, few unknowns | add one validation to an existing endpoint |
| **Full** | Multi-session / multi-track / multi-team / high uncertainty / coordination handoff expected | introduce a new subsystem |

**Tie-breaker**: touches ≥2 modules OR changes public API OR spans sessions/teams OR coordination handoff expected → **Full**. A durable record for one bounded task alone remains Lite.

## Bounded None route

Choose None before reading other guides/templates when all conditions hold: one session, one
product file, a small localized edit (normally fewer than ten changed lines), a fully specified
result, no new feature, public contract expansion, dependencies, migration, shared-state or security-sensitive
change, cross-file integration, or handoff requirement. Focused inspection of the named source,
spec and existing tests is allowed; repository-wide discovery or unresolved product choices is
not. Restoring declared behavior counts as a correction, not a new feature merely because the
broken implementation behaves differently. Scope or risk overrides line count.

After explicit execution intent, name the scope and expected behavior, inspect the actual files
and available check, then edit. An existing failing regression is sufficient red evidence; add a
new test only for a meaningful uncovered case and use a new test file when originals are protected.
Run the target and affected surrounding checks; one command may cover both when its coverage is
explicit. Preserve protected files and unrelated changes. Stop on contradictions, unavailable
required checks or repeated no-progress; use the same three failed correction-cycle cap as RUN.
Record actual command/output/exit and available revisions in the tool transcript or a captured
receipt; unknown clocks/model/effort stay `n/a`. Never invent a start, a fingerprint or independence.
Finish with the change, observed result and remaining limit. Do not create a plan, log, ledger,
board, templates, synthetic PASS wrapper or plan-lint work just to satisfy None.

If a condition fails, announce why and enter Lite or Full before affected work. Explicit user
requests for a durable plan are honored even when None is eligible. A generic “Tackle plan and
run” permits sizing; it does not by itself require a durable workspace. Lite requires `plan.md`,
`log.md`, and `usage.md`; create separate decisions/questions files only when entries exist.
Full adds the core coordination artifacts. A None receipt is not a new workspace and has no
lifecycle-table requirement; existing workspaces retain their current ledger and history.

## Optional intake artifacts

When the user brings formal material at intake — a written product spec, or explicit project principles — `plan` instantiates it in the workspace from the intake templates:

- `specify.tmpl.md` → `spec.md` — the user's spec, captured verbatim plus scope interpretation; never invents acceptance criteria the user didn't state.
- `constitution.tmpl.md` → `constitution.md` — project principles the user actually holds; never fabricated from a vague ask (explore intent first).

Both are **optional** — only created when the user supplies the material; a vague ask is explored, not templated. Points trace to them (`point.tmpl.md` §Traces to) instead of a ticket line when they exist.

## Commands are entry points, not boundaries

Internal invocation never bypasses guardrails: the ladder gates edits, intent stays explicit, and consents and the log/board trail match user-invoked ones. Slash commands and natural-language triggers are aliases into the same modes — a resume triggered by memory of a workspace is the same gate, the same read-first, the same consent as one the user typed.
