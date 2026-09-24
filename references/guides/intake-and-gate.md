## Update boundary (explicit user control)

Ordinary Tackle invocation performs no network access or installation-tree mutation. Updating is
never initiated by planning or execution; an owner may use the documented external/manual workflow
only after explicitly requesting it. Tackle provides guidance but does not perform that workflow.

# Step 1 — Intake (infer first, then ask)

Read this guide through sizing before creating artifacts or loading further guides. Intake anchors
apply to every gate, but logging, scaffolding, compiled Tasks and handoff below apply only to
durable Lite/Full workspaces. None records relevant profile-derived choices in its direct receipt.
Do not batch this read with the Full guide map. Select the route first, then read only its complete
procedure. Use focused diagnosis to establish absence or resolve an authorized local path/capability fault.
Check named owner prerequisites in a separate tool call containing only those probes, then wait
for the result. Do not include inventories, other file reads or guide searches in that call.
If a prerequisite is missing, the next action for that scope is the blocker report; otherwise
continue with named inputs, retained records and route selection. Do not prepare or dispatch
dependent discovery before making this decision.
A confirmed missing owner prerequisite takes precedence over route selection: report affected work
and the needed owner input, then stop that scope. Do not read intake or run workspace inventories,
implementation searches or capability probes afterward. Only required state/evidence recording and
independently authorized work continue. Never enumerate speculative later prerequisites to expand
that blocker. On resume, read the named current inputs and retained observations before any other
guide; an already sufficient check needs no equivalent auxiliary assertion or unchanged closure rerun.

Extract or confirm:
- Problem
- Observable result expected
- Top 2 non-goals
- Highest-shape decision

Do not assume; ground claims in `file:line`.

The four anchors are the intent contract. Extract supplied anchors and record the scope; a sufficient request needs no reconfirmation. Ask only for missing material product behavior, with a recommendation and its effect on affected work. Delegated reversible technical choices proceed within scope. Apply the shared [decision policy](communication.md#decide-whether-input-is-needed); reading another guide is unnecessary when these rules answer the question.

## Learning-loop read (if enabled)

If a profile exists at the relevant scope with `Evolution: enabled`, read it **before** proposing defaults:

- User profile: `~/.tackle/user-profile.md`
- Project profile: `.tackle/profile.md` in the repo root

Select profile entries by applicability, current procedure, supporting evidence and supersession before ranking confidence. Tag a relevant suggestion `(from your profile)`. Existing explicit instructions and delegated choices need no fresh confirmation merely because a compatible preference supports them. A hypothesis is a suggestion, never authority over the current contract.

Apply compatible active directives to their named section or `applies_to:` action. Current user instructions and the authority order come first; project preferences outrank user preferences only where both apply without conflict. A missing section or retired mechanism makes an entry stale; a conflicting hypothesis is inapplicable even when marked active. Explain a conflict when it changes a decision, preserve the original profile, and propose re-confirmation/retirement only through consented retro. Old profiles need no new fields; optional procedure/version, source and supersedes notes can clarify applicability. For example, an old `tackle-check` distribution hypothesis cannot add an executable to the Markdown install, and an all-green-board hypothesis cannot waive deliverable acceptance.

Record one tally line in the log's `### Intake (context gathered)` section:

```
profile proposals: N accepted, M overridden (<which>)
```

If the profile is absent, disabled, or no defaults apply, skip this step without logging a tally.

<a id="archetypes"></a>
### Reference plans

Read `references/archetypes/` alongside the profiles. When an reference plan's summary matches the incoming initiative's shape, offer its skeleton — task list, edge pattern, wave shape — as a proposal explicitly tagged `(from archetype <name>)`, flagging its trap warnings with the offer. These are proposals, never silent defaults: the user may accept, adapt, or override, and overrides are retro material.

If no reference plan matches, skip without offering. There is no scoring engine — read and judge, exactly like profiles and seeds.

## Decision ownership

Use the shared decision policy above. Distinguish an informational question, a pending material product decision, and a blocker. Record a Q-id only when an answer changes the work; identify the affected requirement and continue unaffected work. Reversible technical choices inside authorized scope are local freedom, with a recorded reason when consequential. Diagnose operational failures through permitted tools before asking for user input.

# Step 1.5 — Anchor the intake before sizing

Lock the problem, observable result, top 2 non-goals, and highest-shape decision before choosing a gate.

For a selected Lite route, `../lite-plan.tmpl.md` provides these preparation and execution steps in one place, including scaffold consent. The detailed guide sequence below is for Full.

## PLAN preparation order

PLAN is a preparation protocol, not a source-execution command. After the four anchors are
sufficiently established from the request or resolved decisions, keep the work in this order so that every later choice has an observable contract:

1. **Behavior and outputs** — turn each required behavior into a stable criterion id with its
   observable output, boundary cases, and allowed semantic alternatives. Name exact bytes, order,
   paths, stdio, or exits only when a consumer depends on them.
2. **Acceptance and test strategy** — give every criterion a task check, a surrounding check,
   and an evidence slot. Include negative fixtures for omitted behavior and invalid evidence.
3. **Contracts and decisions** — compile the interfaces, invariants, dependencies, and recovery
   rules that Tasks will consume. Resolve product choices as user-owned decisions; record
   reversible technical choices as local decisions.
4. **Decomposition and readiness** — create the scaffold, Tasks, coverage matrix, and bounded
   readiness review. A Task is not Ready merely because its requirement id appears in a briefing.

The preparation order is a single PLAN run. Do not wait for a later planning session before
stabilizing a contract or assigning Ready. A new session with unchanged relevant fingerprints may
reuse the recorded readiness evidence; changed inputs are handled by the selective revalidation
rule in `verify.md`.

Material product ambiguity blocks the affected criterion and its consumers. A reversible delegated
technical choice is recorded with its decision and evidence and does not block unrelated scope.

<a id="step-2--gate-sizing-full--lite--none"></a>
# Step 2 — Route sizing (Coordinated / Focused / Direct)

Persistent route identifiers Full/Lite/None remain readable; the visible names below preserve their risk conditions.

| Gate | Use for | Example |
|---|---|---|
| **Direct (None)** | One-session, one product file, specified behavior, bounded correction or local edit | restore a whitespace normalization already required by tests/spec |
| **Focused (Lite)** | Single-session, bounded scope, few unknowns | add one validation to an existing endpoint |
| **Coordinated (Full)** | Multi-session / multi-track / multi-team / high uncertainty / coordination handoff expected | introduce a new subsystem |

**Risk precedence**: evaluate the tie-breaker before reducing ceremony by Task count. Write scope ≥2 modules OR changes public API OR spans sessions/teams OR coordination handoff expected → **Full**, even when the initiative has only a few Tasks. A durable record for one bounded task alone remains Lite only when no Full trigger applies. Within the routes still eligible after this check, choose the lowest ceremony that satisfies the other conditions.

<a id="bounded-none-route"></a>
## Bounded Direct route

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
Prefer one E2E check through the real consumer as the sole new test when it covers the behavior.
Never add a unit test after implementing the behavior it covers; if isolation is necessary, list
its applicable failure modes and expected outcomes before the test and implementation. Retain the
replayable artifact from any E2E run as described in `testing.md`.
Run the target and affected related regression checks; one command may cover both when its coverage is
explicit. Preserve protected files and unrelated changes. Stop on contradictions, unavailable
required checks or repeated no-progress; use the same three failed correction-cycle cap as RUN.
For exact-byte edits, use a write that preserves the specified bytes and final newline. Every
required assertion must make the compound command fail: use explicit failure exits or an equivalent
verified mechanism, not `set -u`, `pipefail` or a trailing successful print. For example,
`cmp expected actual || exit $?` preserves a comparison failure. Consume an existing failed
observation and diagnose its cause; repeat the acceptance check only after a relevant input/environment
change or permitted operational recovery. A focused diagnostic read is allowed; merely rereading
the failure or starting a fresh session does not justify repeating it.
Record actual command/output/exit and available revisions in the tool transcript or a captured
receipt; unknown clocks/model/effort stay `n/a`. Never invent a start, a fingerprint or independence.
Finish with the change, observed result and remaining limit. Do not create a plan, log, ledger,
board, templates, synthetic PASS wrapper or plan-lint work just to satisfy None.

If a condition fails, announce why and enter Lite or Full before affected work. Explicit user
requests for a durable plan are honored even when None is eligible. A generic “Tackle plan and
run” permits sizing; it does not by itself require a durable workspace. Lite requires `plan.md`,
`log.md`, and `usage.md`; create separate decisions/questions files only when entries exist.
Coordinated work adds the core coordination artifacts. A None receipt is not a new workspace and has no
lifecycle-table requirement; existing workspaces retain their current ledger and history.

## Optional intake artifacts

When the user brings formal material at intake — a written product spec, or explicit project principles — `plan` instantiates it in the workspace from the intake templates:

- `specify.tmpl.md` → `spec.md` — the user's spec, captured verbatim plus scope interpretation; never invents acceptance criteria the user didn't state.
- `constitution.tmpl.md` → `constitution.md` — project principles the user actually holds; never fabricated from a vague ask (explore intent first).

Both are **optional** — only created when the user supplies the material; a vague ask is explored, not templated. Tasks trace to them (`point.tmpl.md` §Traces to) instead of a ticket line when they exist.

## Requests share the same boundaries

Internal invocation never bypasses guardrails: the ladder gates edits, intent stays explicit, and consents and the log/board trail match user-invoked ones. Natural-language requests, short actions and legacy text aliases follow the same modes; see [invocation.md](invocation.md). A resume triggered by memory of a workspace has the same gate, read-first and consent as one the user typed. A bare skill selection or help request stops at help before intake or scaffolding.
