# Terminology and compatibility

A repository contains initiatives. Each initiative has an objective, a plan and tasks. A run
executes authorized tasks and produces a deliverable. Checks produce verification records that
support acceptance. Decisions, blockers and history explain progress. A workspace is the directory
supporting one initiative. It is not the repository or the objective.

Use one term for one responsibility. A criterion states **what must hold**, a check states **how
to observe it**, and a record preserves **what happened**. A role names a responsibility; it does
not require another agent or prove independence.

## Component inventory

| Canonical visible name | Historical name / stable identifier | Meaning and choice |
|---|---|---|
| Initiative, repository, workspace, plan | unchanged | Distinct objective, containing project, working directory and intended work. |
| Task / task brief | Point / Point briefing; legacy `P-01`, `points/`, `point.tmpl.md` | New work uses `T-01`, `tasks/`, `task.tmpl.md` and `resource-usage.tmpl.md`; retain historical IDs, paths and `usage.tmpl.md` for reading. |
| Task board | Board; historical `board.md` | New `task-board.md` is canonical current task state; old boards stay readable. |
| History | Log; historical `log.md`, `log-archive.md` | New `history.md` and optional `history-archive.md` preserve ordered events. |
| Current work / checkpoint | Coordinator continuity; historical `coordinator.md` | New `current-work.md` is a verified disposable projection. |
| Handoff brief | Handoff; historical `HANDOFF.md` | New `handoff-brief.md` carries portable context and required records. |
| Requirement / criterion / contract clause | unchanged | Required behavior / acceptance statement / selected invariant with source revision. |
| Acceptance check | Done-signal; legacy `Done-signal` and `Run` fields | Command or defined review procedure; retain reader aliases. |
| Task check | Target check | Observes the task's intended behavior. |
| Related regression check | Surround check | Observes affected surrounding behavior. |
| Deliverable acceptance | Global acceptance | Checks final integrated outputs and all mandatory delivery obligations. |
| Write scope | Touches | Complete permitted write set; readers accept both labels. |
| Reference verification | Grounding | Verifies that sources support claims, including current fingerprints and historical citations. |
| Verification records | Evidence; historical `evidence/` | New `verification-records/` stores preserved results and inputs; old paths remain valid. |
| Check summary / raw check record | Receipt / observation | Readable index / original captured event. An execution remains a distinct event. |
| Open question / pending decision / blocker | historically mixed in questions | Information request / unresolved choice / condition preventing affected work. Do not conflate them. |
| Backlog idea | Seed; `docs/seeds/` | Deliberately deferred work, with the same gitignore decision as plans. |
| Reference plan | Archetype; `references/archetypes/` | Reusable proven structure, not an obligation to copy it. |
| Preferences and lessons | Profile; existing profile paths | Applicable preferences, directives and hypotheses with consent-controlled writes. |
| Resource usage | Usage; historical `usage.md`; `tackle-observability/2` schema | New `resource-usage.md` and optional `resource-usage.telemetry.jsonl` hold observed lifecycle and resource information; old sidecar paths remain readable; unknown remains `n/a`. |
| Executor | Driver / Executor | Implements authorized work. |
| Coordinator | unchanged | Owns shared state, dependencies and deliverable acceptance. |
| Reviewer / verifier / auditor | Reviewer or Quality Guardian / Checker, Verifier or Spec Reader / Judge or Red-Teamer | Semantic assessment / actual checks / explicit finished-work audit. Keep responsibilities distinct. |
| Autonomy | `L1` report, `L2` assisted, `L3` unattended | Authorization limits; a level never supplies missing user permission. |
| Model capability / reasoning effort | tier `fast/standard/frontier`; effort `low/medium/high/max` | Capability needed / requested effort. Record actual bindings; names do not establish access or quality. |
| Correction budget / attempt journal | Budget / Attempts | Persistent failed correction cycles, separate from initial checks and operational recovery. |
| Dependency / produced artifact / consumer | Depends on / crossing artifact | A named interface and revision actually consumed; shared writes are coordination, not a false dependency. |
| Team / parallel batch / milestone | Solo, Pair, Pod, Squad / wave / optional milestone | Capability allocation / runnable concurrent tasks / observable intermediate outcome. Each must earn its cost. |
| Readiness check / acceptance gate | gate, seal | Checks permitting a state transition / protected expectation. Neither is a new workflow or role. |
| Task report / failure report | closure report / escalation packet | Results and records / expected-versus-observed blocker with affected work and remaining budget. |
| Run / deliverable / decision | unchanged | Execution episode / integrated output / recorded choice. |

## Routes and actions

**Direct** is the visible name for **None**: the existing bounded one-file correction without a
workspace. **Focused** is **Lite**: bounded durable work with plan, history and usage. **Coordinated**
is **Full**: cross-module/API, multi-session/team, uncertainty or handoff needs. All existing risk
triggers apply before task count. Persistent `Gate: Lite` stays exact for compatibility; visible
headings may say Focused. Renaming a route never lowers its obligations.

Use action verbs: **plan, run, show status, validate the plan, audit the result, review lessons**.
Keep PLAN/RUN/STATUS, `verify`, `judge`, `retro`, documented flags and aliases in
[invocation.md](guides/invocation.md). These names register no additional host skill entries.

## States and observations

New task boards declare `Schema: tackle-workspace/5` and use **Draft → Ready to run → In progress →
Checking → Complete**. Draft includes deferred or insufficiently prepared work. Ready to run
requires current readiness records. In progress covers preflight/implementation/correction;
Checking covers task, regression and affected integration validation. Complete requires every
mandatory task obligation, not merely implementation. Initiative completion additionally requires
deliverable acceptance. Blocked, Interrupted, Skipped and Unverifiable remain distinct. On `/5`
boards, Waiting on owner means progress needs an owner action, and it differs from Blocked.

| Historical value | Read/display mapping | What it does not establish |
|---|---|---|
| `🔴` not started | Draft; Ready to run only with current readiness evidence | Readiness cannot be inferred from color. |
| `Ready` / preflight | Ready to run / In progress | Product success. |
| `🟡`, implementing, correction | In progress | Passed checks. |
| target validation, validating, integrating, accepting | Checking | Task or deliverable acceptance. |
| `🟢`, done, complete | Complete as historically recorded | Fresh verification or deliverable acceptance. |
| `⏸`, blocked | Blocked | A skipped obligation or exhausted budget reset. |
| `observe-incomplete`, interrupted | Interrupted; observation token stays `observe-incomplete` | Whether the side effect occurred; reconcile records first. |
| `⚪`, skipped | Skipped with authorized reason | Completion of a mandatory criterion. |
| `UNVERIFIABLE`, unavailable required check | Unverifiable, with affected work blocked | A passing result. |

Check-event states stay exact: started/incomplete, observed exit/timeout/signal, accepted or
rejected child result. Child acceptance is not semantic approval. Describe verification by method
(command/review/audit), result and **observed** independence. E0–E3 remain readable historical codes:
E0 unverifiable, E1 independently command verified, E2 named review gate, E3 asserted. They are not
an ordinal quality scale. Renaming evidence never upgrades it or invents a reviewer.

## Files, fields and adoption

Keep one authoritative file for each fact. New workspaces use T-ids, `tasks/`, `task-board.md`,
`history.md` and `resource-usage.md`; existing P-ids, paths, D-ids, Q-ids, raw-record fields, lifecycle columns and documented anchors remain valid for historical reading. New briefs use Write scope,
Acceptance check, Task check and Related regression check; readers accept their old aliases.
Legacy section anchors have explicit HTML aliases where a heading changes. Existing schema tokens
are never translated for a localized conversation. Do not renumber a historical task, duplicate an
identity, or reset authorization/correction lineage to adopt terminology. A selected migration uses
a reversible copy and explicit P→T mapping.

Use new board schema only in validated new workspaces or selected copy-first migrations.
[Migration](guides/migrate.md#candidate-workspace-format) preserves history and reversible mapping.
An unchanged old workspace stays readable under its pinned procedure; no automatic migration of
closed or unrelated work. New schema names are English. Long-context and record-store metadata
are optional capability-specific additions, not prerequisites for Direct or Focused work.
