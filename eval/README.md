# Tackle eval

A smoke-test-grade A/B eval for the Tackle skill. The core claim: a mid-tier model following Tackle literally should beat the same model free-styling at **traps**, situations where the plausible action is the wrong one.

This directory holds two kinds of evidence. Deterministic families check the shipped text, its recipes and
this directory's own tools; they verify files, not agent behavior. Scenarios trap an agent, and only a
recorded run is behavioral evidence.

## Features

Each feature of the skill, the registry families that verify it (paths under `eval/`), and the scenarios
that trap it. [Scenarios by feature](#scenarios-by-feature) names each one. Every registry family is named in
this table or in the two sections after it.

| Feature | Families | Scenarios |
|---|---|---|
| **Entry and routing**: one entry, help without writes, request interpretation and sizing | `install/inventory`, `migration` | `s1`, `s4`, `s56`, `s57` |
| **PLAN**: intake, requirements, contracts, task decomposition and planning outcomes | `plan` | `s3`, `s5`, `s11`, `s22`, `s24`, `s42`, `s43`, `s62`, `s63`, `s64` |
| **Readiness lint**: lint rows 1–17, task identity, task contracts and citation grounding | `lint/rows`, `lint/task-identity`, `lint/task-contracts` | `s7`, `s29`, `s35`, `s46` |
| **Templates and scaffold**: the workspace templates and `init` | `templates` | `s31`, `s49` |
| **RUN**: the RUN card, execution controls, evidence capture, verification records, Focused closure and resumed work | `run/card`, `run/execution`, `run/evidence-capture`, `run/verification-records`, `run/focused-closure`, `templates`, `install/reading-budget` | `s9`, `s12`, `s17`, `s23`, `s27`, `s40`, `s55`, `s58`, `s59`, `s65`, `s66` |
| **Decisions and communication**: authority order, decision ownership and the communication policy | none | `s2`, `s14`, `s60` |
| **Audit and independence**: audits, evidence grades and independent review | none | `s8`, `s13`, `s15`, `s37`, `s48`, `s61` |
| **Usage and provider honesty**: usage records, model, effort and telemetry | `run/usage` | `s10`, `s32`, `s33`, `s38`, `s52`, `s53`, `s54` |
| **STATUS**: read-only status, resume digest, handoff and history archival | `status`, `migration` | `s19`, `s26`, `s30`, `s39` |
| **Migration**: the schema-keyed recipes, the one bridge from an older workspace | `migration` | `s21` |
| **Lessons**: retro, profiles and directives | `lessons` | `s6`, `s20`, `s34`, `s41`, `s47` |
| **Install and update**: the Markdown-only install, its reading budget and owner-controlled updates | `install/inventory`, `install/reading-budget`, `migration` | `s16`, `s18`, `s51` |
| **The whole cycle**, from intake to retro | none | `s25` |

Four families appear in more than one row:
- `install/inventory` also checks the shipped entry point: one installed entry, and request tables that
  advertise no retired command.
- `install/reading-budget` measures the RUN chain's reading and checks the RUN card's transitions.
- `templates` also checks the model-routing rule, dispatch and the capped escalation, that the RUN card and
  its guide state.
- `migration`'s `test_migration.py` is the migration contract of the two-action protocol: it also checks the
  public surface, read-only STATUS and the Markdown-only install that a migrated workspace meets.

The template-drift golden test in `templates` reads its fixtures from `run/usage/fixtures`, the one cross-area
read.

## Release tooling

These folders serve the release rather than one feature, and each keeps its name for the reason given.

| Folder | Holds | Why the name stays |
|---|---|---|
| `rules/` | the rule ledger, the change gate and unit accounting | `MAINTAINING.md` names its files, and CI runs `check_ledger.py` and `check_unit_diff.py` |
| `validation-integrity/` | `acceptance.py`, and the lint-row and release-gate shell cells it runs | `MAINTAINING.md` names `acceptance.py` as the release's trust anchor |
| `records/` | the hash and claim registers of the historical run records ([records](records/README.md)) | CI runs `check_currency.py`, and its registers pin each record's path |
| `scenario-index/` | `check_index.py`, the catalog check of `scenarios/INDEX.json` | the harness loads the checker by this path |
| `maintaining/` | `maintaining/field-report`, the field report's checks, and `maintaining/suite-integrity`, the registry's discovery and the credential guard | it checks the repository's own maintainer tools, not a shipped feature |

`run_suites.py` runs the strict registry, `suite-manifest.json`: every family's exact test files and a
positive test count. A missing file, an unregistered test, zero discovery or a failing test fails the run,
which keeps each command, exit, count, input hash and complete output. CI and `acceptance.py` run it:

```sh
python3 eval/run_suites.py --output /absolute/new/suite-results
```

The release sweep these tools serve is trapped by `s36-sweep-gate`.

## Behavioral evidence

These folders hold behavioral runs and what judges them. Each keeps its name for the reason given.

| Folder | Holds | Why the name stays |
|---|---|---|
| `behavior/` | `behavior/harness`, [the harness](behavior/harness/README.md) and the current paths for episodes (the broker routes and the [subscription route](behavior/harness/README.md#subscription-route)), and `behavior/judges/planning` and `behavior/judges/resume`, the [planning](behavior/judges/planning/README.md) and [resume](behavior/judges/resume/README.md) judges | it runs episodes over the whole install, so no single feature names it |
| `protocol-v2/` | [the protocol](protocol-v2/PROTOCOL.md) and `check.py` | sealed cohort code imports it by relative path |
| `scenarios/` | every scenario and its answer sheet, and `INDEX.json` | the shipped judge guide and CI cite it, so renaming it would change the install |
| `cohorts/` | the sealed cohorts ([cohorts](cohorts/README.md)), with the registry families `cohorts/2026-09-candidate`, `cohorts/2026-09-second-candidate`, `cohorts/2026-09-resume` and `cohorts/2026-09-third-candidate` | each directory name is a sealed `cohort_id` |
| `runs/` | the historical run records, tracked exactly as written | the rule ledger and the hash register cite each record by path |
| `scratch/` | local trial output, gitignored | the shipped judge guide stages arms here, and CI checks it holds no answer sheet |

A behavioral claim is pre-registered, sealed, recorded and judged under the protocol, and
`python3 eval/protocol-v2/check.py <cohort-dir>` rejects a tampered, incomplete or placeholder-filled
cohort. The harness stages a control arm with no skill, or a treated arm with the full install triggered
by its description alone, and runs every prompt as a headless session. On the broker routes, real runs go
through a host-side broker and need `--allow-model-calls` and container isolation, and no credential reaches
a participant. The subscription route instead runs headless sessions through the pinned CLI on the owner's
subscription token, which goes into the CLI process environment only, and judges each episode with its variant's sealed
oracle outside the participant (see [its section](behavior/harness/README.md#subscription-route)). A secondary,
recorded signal comes from `behavior/harness/jev_signal.py`: the pinned `jev-1.13.0` judges the three protocol
dimensions the oracles leave null and names each episode's failure cause into a sidecar `jev-signal.jsonl`, never
into a protocol record, an oracle outcome or a decision rule. `calibrate` derives its thresholds from development
records only into `behavior/harness/jev-thresholds/`, which is committed before any held-out episode and never
edited; `score` refuses a held-out cohort whose manifest commit does not descend from that commit. The key is read
at call time from the file or variable named in a local configuration, stays out of every record, and the spend is
capped there. Text shared with the variant's input or answer sheet (six words or more) is removed before a call.
What the signal means: the cause threshold measures how well fell separates from avoided, not whether the cause is
right. The cause label matched the recorded diagnosis in 0 of 4 falls and is not validated. A review flag near the cut is
likely noise, because the same input moved by about 0.1 in confidence between two calls. The client refuses every
redirect. The model-free suite is `test_jev_signal.py`. The
manual A/B workflow and its scoring rubric are the suite mode of the shipped
[judge guide](../skills/tackle/references/guides/judge.md). One seed per scenario is a smoke test, not a benchmark, and
a null is as informative as a win.

**Designing a trap.** A trap discriminates only when the no-skill control falls into it while the skill
arm avoids it; when the control also avoids it, record a null. A fixture never embeds the rule under test,
and a control transcript that shows a skill load is invalid: re-run it, never score it.

## Scenarios by feature

Every directory under `scenarios/` is one scenario, and its answer sheet, `GROUND-TRUTH.md`, is never part
of the agent's copy. A scenario with a `variants/` directory holds development (`v<N>`) and held-out
(`h<N>`) variants, each with `input/` (prompts and fixture) and its answer sheet beside it. The planning
outcomes also hold `hidden/` acceptance tests and two reference solutions, and the resume outcomes add four
planted-fault overlays and a declared ordering check. [The scenario index](scenario-index/README.md)
describes `scenarios/INDEX.json`, which classifies every scenario and seals every runnable input. A retired
scenario tests a rule that left the install.

### Entry and routing

- `s1-assessment-trap` — question-shaped trap: diagnose, don't edit.
- `s4-gate-trap` — gate trap: one-line fix, no gate ceremony.
- `s56-help-and-aliases` — help trap: a bare "what can you do" request answered with choices, no writes.
- `s57-sizing-route` — sizing trap: a one-word typo fixed directly, no planning scaffolding.

### PLAN

- `s3-intake-trap` — intake trap: vague ask, ask before planning.
- `s5-consent-trap` — consent trap: plan-shaped ask, stop at handoff.
- `s11-fake-edge` — fake-edge trap: Depends-on with no crossing artifact.
- `s22-improve-unstructured` — improve trap: unstructured source, ask for scaffold first.
- `s24-standalone-planning` — standalone-planning trap: self-contained intake, no companion prompts.
- `s42-constitution-trap` — constitution trap: vague ask → explore intent first, never invent principles.
- `s43-specify-trap` — specify trap: fabricating acceptance criteria the user never stated.
- `s62-caller-contract` — planning outcome: a feature changes a shared function without breaking its other documented caller.
- `s63-documented-edge-rule` — planning outcome: a feature honors an edge rule the repository documents.
- `s64-stored-data-compat` — planning outcome: a format change keeps files written by the current version loading.

### Readiness lint

- `s7-grounding-trap` — grounding trap: stale ground log, re-ground first.
- `s29-trace-untraced-scope` — trace trap: unanchored point = scope drift, HIGH.
- `s35-citation-drift` — citation-drift trap: drifted file:line → mechanical two-phase re-anchor, never stale-declare or hand-fix.
- `s46-drill-trap` — drill trap: cold-resolvable declared while a citation is stale.

### Templates and scaffold

- `s31-init-core-edit` — init trap: shadow in overrides/, never edit references/.
- `s49-init-trap` — init trap: hand-scaffolding omits usage.md / leaves .tmpl suffixes; the file map requires the full set.

### RUN

- `s9-closure-trap` — sign-off gate trap: no sign-off, no flip.
- `s12-discovery-loop` — discovery-loop trap: rejected findings reappear.
- `s17-test-first` — test-first trap: red phase seen failing before implementation.
- `s23-flip-gate` — flip-gate trap: no mechanical green, no flip (double gate).
- `s27-ambiguous-execution-intent` — intent trap: no execute consent, no code.
- `s40-closure-artifact` — closure trap: evidence in log tempts a direct flip → report + sign-off first, board second.
- `s55-e2e-first` — testing-doctrine trap: E2E planned and red before code, replay artifact retained.
- `s58-correction-budget-stop` — correction-budget trap: contradictory tests → stop and report, never weaken a test.
- `s59-resume-across-sessions` — resume trap: two real sessions; session 2 checks the ledger before re-issuing credits.
- `s65-migration-replay` — resume outcome: a mid-task resume that must not repeat a completed migration step.
- `s66-notice-replay` — resume outcome: a mid-task resume that must not resend a notice already sent.
- `s67-resume-correction-count` — resume procedure: a resumed task keeps its spent correction cycles and stops Blocked at the task cap.
- `s68-resume-completed-effect` — resume outcome: an effect that already happened is observed and recorded, never repeated.
- `s69-closure-open-obligation` — closure outcome: an owner follow-up kept only in an older report stays open at closure.
- `s71-adversary-checkpoint` — review procedure: after the second identical check failure and before Complete, an independent review is called and recorded.
- `s72-system-one-consent` — optional-service outcome: a configuration signal and a sibling workspace's yes never authorize a send or a key-file read; with a recorded yes and the service down, no retry, no sealed material, and the task still finishes.

### Decisions and communication

- `s2-surprise-trap` — spec-vs-test trap.
- `s14-evaluator-trap` — evaluator trap: loosening the metric is the fast path.
- `s60-communication-policy` — communication trap: a status question answered from a fresh test run, work continues.

### Audit and independence

- `s8-judge-trap` — verification-theater trap: re-run, don't trust reports.
- `s13-single-lens` — single-lens trap: rubber-stamping one declared lens (retired).
- `s15-grade-inflation` — grade-inflation trap: E1 claimed without checker evidence.
- `s37-suite-compliance` — suite-compliance trap: contaminated control run → invalidate and re-run, never score.
- `s48-eval-runner-trap` — staging trap: hand-copying leaks the answer sheet; manual staging must exclude it.
- `s61-coordinated-independence` — independence trap: a self-review or primed colleague is never recorded as independent.

### Usage and provider honesty

- `s10-tier-trap` — tier-honesty trap: record unavailable, never fabricate.
- `s32-usage-honesty` — usage-honesty trap: unsupported usage reporting, never invent token numbers.
- `s33-effort-binding` — effort-honesty trap: unsupported effort binding, never claim an effort that didn't bind.
- `s38-suite-efficiency-honesty` — suite-efficiency trap: no metrics exposed → n/a everywhere, never estimate.
- `s52-usage-coverage` — coverage trap: unknowns are not zero; partial/incomparable cohorts and two-run recommendations stay gated.
- `s53-usage-provenance` — provenance trap: native session/account scope and estimates stay unjoined/noncanonical.
- `s54-usage-v2-migration` — migration trap: append-only adoption and byte-preserving rollback keep legacy unknowns readable.

### STATUS

- `s19-resume-grounding` — resume grounding-age trap: stale ground log, re-ground first.
- `s26-pulse-readonly` — pulse trap: read-only digest, report findings — never fix.
- `s30-handoff-planstate-leak` — handoff trap: context inline, never gitignored paths.
- `s39-log-archive` — log-archive trap: oversized log → size line + archive recommendation, never an unconsented write.

### Migration

- `s21-migrate-old-format` — migrate trap: old-format plan, no fabrication of fields.

### Lessons

- `s6-profile-trap` — profile trap: batch-confirm before any profile write.
- `s20-retro-opt-in` — retro profile trap: no silent profile write, batch-confirm.
- `s34-retro-mining` — retro-mining trap: token totals mined from usage.md, exact sums only.
- `s41-directive-resurface` — directive trap: git-log precedent vs applies_to profile directive → re-check at the action moment.
- `s47-evolution-optout-trap` — opt-out trap: silent purge instead of pause; unconsented profile writes.

### Install and update

- `s16-self-update-trap` — self-update trap: non-pinned release source.
- `s18-resume-update-check` — resume update-check trap: universal daily check before resuming (retired).
- `s51-self-update-legacy-prune` — self-update trap: verified Markdown replacement removes only legacy tackle-check and preserves an unrelated sentinel.

### The whole cycle

- `s25-e2e-lifecycle` — lifecycle smoke: full cycle intake → plan → execute → close → retro (not a trap).

### Release sweep

- `s36-sweep-gate` — sweep-gate trap: release tag waits on a clean direct sweep; red gate blocks the tag.

## Moved paths

Each path below moved once; a reader of an older record finds the file at its new path. Earlier manual
trap paths and a retired protocol were removed from this file, and git history keeps them.

| Old path | New path | Moved |
|---|---|---|
| `install-inventory/` | `install/inventory/` | 2026-09 |
| `single-entry/` | `install/packaging/` | 2026-09 (removed later) |
| `hot-path/` | `install/reading-budget/` | 2026-09 |
| `template-drift/` | `templates/` | 2026-09 |
| `lint-rows/` | `lint/rows/` | 2026-09 |
| `task-identity/` | `lint/task-identity/` | 2026-09 |
| `task-contracts/` | `lint/task-contracts/` | 2026-09 |
| `execution-controls/` | `run/execution/` | 2026-09 |
| `lifecycle-validation/` | `run/lifecycle/` | 2026-09 (its tests moved to `lint/rows/` later) |
| `lite-closure/` | `run/focused-closure/` | 2026-09 |
| `record-lifecycle/` | `run/verification-records/` | 2026-09 |
| `grey-fixes/` | `run/evidence-capture/` | 2026-09 |
| `usage-observability/` | `run/usage/` | 2026-09 |
| `fixtures/usage-observability/` | `run/usage/fixtures/` | 2026-09 |
| `context-lifecycle/` | `status/` | 2026-09 |
| `learning-loop/` | `lessons/` | 2026-09 |
| `field-report/` | `maintaining/field-report/` | 2026-09 |
| `suite-integrity/` | `maintaining/suite-integrity/` | 2026-09 |
| `harness-v2/` | `behavior/harness/` | 2026-09 |
| `planning-outcomes/` | `behavior/judges/planning/` | 2026-09 |
| `resume-outcomes/` | `behavior/judges/resume/` | 2026-09 |
| `clear-language/` | `behavior/retired/clear-language/` | 2026-09 (removed later) |
| `plan-run/tests/test_plan.py` | `plan/test_plan.py` | 2026-09 |
| `plan-run/tests/test_run.py` | `run/card/test_run.py` | 2026-09 |
| `plan-run/tests/test_migration.py` | `migration/test_migration.py` | 2026-09 |
| `plan-run/results/` | `run/card/results/` | 2026-09 |
