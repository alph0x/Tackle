# PLAN card

PLAN is a preparation protocol: it stops before source execution. Read this card in full for a
Coordinated (Full) request; a Direct or Focused request exits at step 2. `INTENT: PLAN prepares
tasks and stops before source execution.`

1. **Intake anchors.** Extract or confirm the four anchors — problem, observable result expected,
   top 2 non-goals, highest-shape decision — from the request or resolved decisions; ground claims
   in `file:line`. A sufficient request needs no reconfirmation. The full infer-first-then-ask
   procedure, the owner-prerequisite probe, the
   [learning-loop read](intake-and-gate.md#learning-loop-read-if-enabled) and reference-plan offer
   are in [intake-and-gate.md](intake-and-gate.md#step-1--intake-infer-first-then-ask), Step 1
   through [Step 1.5](intake-and-gate.md#step-15--anchor-the-intake-before-sizing).
2. **Sizing and routing**, before any route-specific loading:

   | Gate | Use for |
   |---|---|
   | **Direct** | One-session, one product file, specified behavior, bounded correction or local edit |
   | **Focused** | Single-session, bounded scope, few unknowns |
   | **Coordinated** | Multi-session / multi-track / multi-team / high uncertainty / handoff expected |

   Evaluate the risk precedence before reducing ceremony by task count: write scope ≥2 modules, a
   changed public surface, work spanning sessions or teams, or an expected handoff, each force
   **Coordinated** even when the initiative has only a few tasks. Within what is still eligible,
   choose the lowest ceremony.
   - **Direct** goes to the [bounded route](intake-and-gate.md#bounded-none-route) and reads no
     further guide;
   - **Focused** goes to `../lite-plan.tmpl.md`, which holds its whole preparation and execution in
     one place;
   - **Coordinated** continues with this card.

   The full gate table, its worked examples and the bounded route's complete procedure are in
   intake-and-gate.md, [Step 2](intake-and-gate.md#step-2--gate-sizing-full--lite--none): read it
   alone through sizing, before this card or any other guide.
3. **The scaffold.** If this initiative has no previously authorized gitignore decision, ask the
   user explicitly and record the answer; otherwise reuse it, for `docs/plans/` and `docs/seeds/`
   alike. Then copy the core set of artifacts from the templates into `docs/plans/<initiative>/`
   and run the file-map check before handoff. The full procedure, the core file map and the
   optional depth artifacts are in [scaffold.md](scaffold.md#step-3--scaffold-inside-plan).
4. **Compile behavior, acceptance and contracts.** In order, so every later choice has an observable
   contract: name every requirement's observable behavior and boundary cases; give each one a task
   check, a related regression check and an evidence slot, with positive and negative fixtures;
   compile the interfaces, invariants, dependencies and recovery rules the tasks will consume; then
   write each task's brief from these compiled obligations. Prefer one end-to-end check through the
   real consumer as the sole new test for a criterion it covers; every negative fixture must expose
   an implementation that satisfies a keyword, file-existence or count check while violating the
   required behavior. Stabilize `design-contract.md` now, in this PLAN run — do not wait for a
   second session. The full compilation order — [behavior and outputs](design-and-contract.md#behavior-and-outputs),
   [acceptance and test strategy](design-and-contract.md#acceptance-and-test-strategy),
   [contracts and decisions](design-and-contract.md#contracts-and-decisions) and the
   [task brief](design-and-contract.md#task-brief) — the
   [architecture recommendation](design-and-contract.md#step-55--architecture-recommendation), the
   [stabilization rules](design-and-contract.md#step-575--stabilize-the-design-contract-full-only)
   and the [code style rule](design-and-contract.md#code-style) are in design-and-contract.md.
5. **Decompose to the fewest tasks.** One task, unless a qualifying reason forces a split: a
   different owner, parallel self-contained work, a hard dependency, an independent review or
   approval, or follow-up that needs its own tracking. Each separate task's briefing names its
   reason in the plan's task table (`Why separate`, or `—` for a single-task plan). A merge-back
   pass then folds every task without a surviving reason into its parent, as a checklist item or
   acceptance criterion. What is left is cut for parallelism by crossing artifacts and interfaces,
   not by a merely disjoint write scope, and each is the smallest coherent vertical slice with one
   runnable acceptance check. The skeleton board, the cut rules, the right-sizing collapse and the
   [model and tier proposal](decompose-and-lint.md#model-and-tier-proposal-compile-time) are in
   [decompose-and-lint.md](decompose-and-lint.md#step-6--decompose-into-loop-runnable-points-and-delivery-obligations),
   Step 6 and [Step 6.6](decompose-and-lint.md#step-66--right-size-the-plan).
6. **Lint.** Run every row of `lint-spec.md` — the 17 mechanical, copy-paste checks that decide
   wiring, grounding, statuses, citations, seals and collisions — and report the agent-computed
   summary. Structural lint does not by itself establish readiness: a passing board can still hold a
   Draft task or an unanswered product question, reported as a separate blocker, not a lint finding.
   Then judge what no row can decide: contract churn, quality dimensions, the reversibility gate,
   deferral and questions, the Q-guard, and depth-artifact coherence. The full judge checklist is in
   decompose-and-lint.md, [Step 6.5](decompose-and-lint.md#step-65--lint-the-wired-plan). For a
   nontrivial task graph, the
   [optional task consistency recipe](decompose-and-lint.md#optional-task-consistency-recipe) checks
   task identities, scope ownership and producer/consumer compatibility mechanically.
7. **Readiness validation.** Run the shared validation contract — preparation, product, evidence
   integrity, relevant change — then the coverage matrix (every criterion has a task, check and
   verification-record slot; every task traces to a criterion) and one bounded semantic
   counterexample review: which wrong implementation would still pass the stated checks. Any HIGH
   finding, or an ungrounded task, blocks a task from Ready to run; a MEDIUM finding also blocks
   unless the user explicitly accepts the risk, and a LOW finding is advisory. Three of this
   validation's checks are linked here directly, not as depth, because a stale citation, a broken
   seal or an unmet readiness criterion is as much a readiness check as the review itself:
   [step 0, mechanical grounding](verify.md#step-0--mechanical-grounding-two-phase-citation-check)
   (the two-phase citation check, run right after this PLAN and on any cold session that reports
   stale), [step 8, seal integrity](verify.md#step-8--seal-integrity) (every `SEALED: D-xx`
   resolves to a live decision, and every compiled clause hash still matches its contract clause)
   and [Step 6.75's Ready-to-run criteria](decompose-and-lint.md#step-675--integrated-readiness-validation)
   (coverage, interfaces and fixtures coherent and passing, fingerprints recorded, no material
   contradiction or unowned obligation left).
   The full validation contract, [including its two halves](verify.md#product-verification-has-two-halves),
   the coverage matrix, the [cold-resolvability probe](verify.md#cold-resolvability-probe-risk-triggered)
   and the milestone-readiness rules are in
   [verify.md](verify.md#step-7--shared-validation-plan-readiness-and-explicit-verify). This step records readiness evidence; it
   never runs source execution or claims a product PASS. Handoff carries the matrix, the global
   obligations, the Ready fingerprints and the explicit execution boundary; RUN records its own
   intent before it may mutate source.
   A brief locks only after its `lock` [adversary checkpoint](run.md#adversary-checkpoints).

**Stop rule.** PLAN exists to unblock execution. When the next step is small and clear, do it; do
not re-plan a plan, and do not open a second planning session to restate a decision this one
already settled.

**Depth.** The deeper mechanics of each step above stay in its guide, reached from the closing
Depth list below or from the anchored links inside the steps themselves — the anchored links are
procedure, not depth, even though their text lives in a guide: link them, never copy them, because
a pasted copy would sit inside a fenced block or a paraphrase that no duplicate check inspects. Each
guide's first line points back to this card. Never move a step of this procedure, a safety rule or
a readiness check behind Depth to shorten this card.

## Depth (on demand)

[Update boundary](intake-and-gate.md#update-boundary-explicit-user-control),
[learning-loop read](intake-and-gate.md#learning-loop-read-if-enabled) and
[reference plans](intake-and-gate.md#archetypes),
[decision ownership](intake-and-gate.md#decision-ownership),
[optional intake artifacts](intake-and-gate.md#optional-intake-artifacts),
[request boundaries](intake-and-gate.md#requests-share-the-same-boundaries),
[scaffold depth artifacts](scaffold.md#depth-artifacts),
[acceptance and test strategy](design-and-contract.md#acceptance-and-test-strategy),
[architecture recommendation](design-and-contract.md#step-55--architecture-recommendation),
[stabilizing the design contract](design-and-contract.md#step-575--stabilize-the-design-contract-full-only),
[code style](design-and-contract.md#code-style),
[loop reference plans](decompose-and-lint.md#loop-reference-plans-type-discovery--type-experiment),
[the task consistency recipe](decompose-and-lint.md#optional-task-consistency-recipe),
[the shared validation contract](verify.md#shared-validation-contract),
[the two halves of product verification](verify.md#product-verification-has-two-halves),
[the coverage matrix](verify.md#coverage-matrix-criterion--evidence),
[the cold-resolvability probe](verify.md#cold-resolvability-probe-risk-triggered),
[selective revalidation after drift](verify.md#selective-revalidation-after-drift),
[preparation horizon](decompose-and-lint.md#preparation-horizon),
[milestone readiness](verify.md#milestone-readiness),
[PLAN-only intent and handoff](verify.md#plan-only-intent-and-handoff).
