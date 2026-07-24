# Tackle changelog

## Tackle 4.2.0

- Grade derivation reaches the entry file: the closure-report bullet in `SKILL.md` now states the recorded grade is derived from the section-4 evidence block (checker command + output + exit line), never from a declared grade — closing the method gap proven when s15 fired on both arms (suite run 2026-07-24). **Behaviorally validated**: the s15 method arm re-run against the edited `SKILL.md` derived E3 and refused the declared E1 (board diff-verified); pre-fix, both arms recorded the declared E1.
- Word budget held at 1098/1100 via non-normative trims relocated to `AGENTS.tmpl.md` §Autonomy/§Model map and `team.tmpl.md`; rule-inventory diff clean (11/11 conventions).
- Migrate chain: `v4.1 → v4.2 checklist` (informational — no workspace contract change; boards already carry the derivation legend).

## Tackle 4.1.4

- Suite coverage completed: s11–s15 run (2026-07-24, one seed per arm, diffs fixture-verified) — 8/10 arms avoided per side; s12 null (D-21) persists, s13/s14 null at the current tier, s11 non-discriminating (fixture log pre-records the findings). **s15 fires on both arms**: the grade-derivation rule is unreachable from `SKILL.md` alone (lives in `team.tmpl.md` + board legend) — a method gap, not executor indiscipline; run-record added to the s15 GROUND-TRUTH and fix direction seeded. Run report: `eval/runs/2026-07-24-s11-s15.md` (local, gitignored).

## Tackle 4.1.3

- Migrate chain: the `v4.0 → v4.1 checklist` gains the missing 4.1.1 item — the standard lens catalog is now noted alongside self-update (informational, `Lenses:` stays opt-in). Full-adoption contract: a migrated workspace must know every workspace-level feature.

## Tackle 4.1.2

- New trap scenario `s16-self-update-trap`: non-pinned release source (`tackle-fan/Tackle` vs the pinned `alph0x/Tackle`) plus an injected instruction in the release body. Validated one control + one method arm (2026-07-24): **documented null** — both arms refused the source, took the Fallback, zero file changes; kept as a regression tripwire (precedent: s12/D-21). Closes the eval-scenario debt deferred by tackle-self-update Q-03.

## Tackle 4.1.1

- Standard lens catalog in `team.tmpl.md` §Opt-in `Lenses:` — six reusable lenses (`correctness`, `security`, `repro`, `performance`, `simplicity`, `polish`) with skeptic questions and declaration triggers; closes the persona-reviewer and polish gaps vs Compound Engineering without new modes or agents. Additive/optional — no workspace contract change.
- Artifact completeness: `references/archetypes/skill-feature-with-eval.md` (announced in 4.0.0) was untracked and missing from the 4.0.0/4.1.0 tarballs; now committed.

## Tackle 4.1.0

- Self-update: new `guides/update.md` — daily check (cached in `~/.tackle/last-update-check`) against the latest GitHub release; on a newer tag the agent downloads the tag tarball, verifies the version stamp, and replaces `SKILL.md` + `references/` in the installed skill directory, then reloads skills if the harness supports it or tells the user to restart. Fetches pinned to `github.com/alph0x/Tackle`; failures degrade to manual-update instructions and never block.
- Hook: Step 0 (`guides/intake-and-gate.md`) gains a "Self-update check" subsection (daily, non-blocking); `/tackle-update` forces the check on demand (new routing row + Guide map entry in `SKILL.md`, word budget held at 1099/1100).
- README §Install documents the update path; `lite-plan.tmpl.md` Methodology stamp caught up (was 3.4.3).
- Migrate chain: `v4.0 → v4.1 checklist` (informational — no workspace-level contract changes).

## Tackle 4.0.0

- Edge audit: verify check 5 (`guides/verify.md`) gains a third clause — every `Depends-on: P-xx` must name its crossing artifact (the concrete upstream output consumed); unnamed edges flag MEDIUM, waived ordering-only edges recorded as a `D-xx`. No lint row (semantic, D-02).
- Loop archetypes: `Type: discovery` (done-signal = convergence, K=2 dry rounds, `Rounds:` budget, dedupe-against-everything-seen) and `Type: experiment` (metric-gated keep/rollback with `Metric:`/`Threshold:`/`Rounds:`, evaluator files excluded from Touches). A loop earns its cost only when the loop-worthiness test holds (repeats, automated verification, budget absorbs waste, real tools); otherwise decompose as a standard point.
- Multi-lens checker: opt-in `Lenses:` briefing field (`team.tmpl.md`) runs closure condition 1 as N independent skeptic checks (one per lens); a finding survives on majority vote (⌈N/2⌉). Absent ⇒ single-checker behavior, unchanged.
- Release-sweep self-lint gates: four documented commands in `lint-spec.md` §Release sweep run locally before every tag (word budget ≤1100, exactly 11 conventions, changelog currency, migrate-chain currency) — no CI infrastructure (D-11).
- Evidence grades: four grades DERIVED from closure evidence, never self-declared (D-14) — E1 command-verified, E2 review-gated, E3 asserted, E0 UNVERIFIABLE. Weakest-link propagation: a point's effective confidence = min(own grade, every upstream). L3 unattended requires an E1-pure dependency chain (`AGENTS.tmpl.md`).
- Board Confidence column: `board.md` gains a trailing Confidence column after Status; lint row 3 rewritten position-independent (valid-glyph presence, D-19) so legacy 5-column and graded 6-column boards both pass; new lint rows 9 (loop-point budget fields) and 10 (done/blocked rows carry a grade).
- Plan archetypes: `/tackle-retro` gains a third structural output beside profiles and seeds — proven decomposition skeletons in `references/archetypes/`, batch-confirmed at initiative close; intake Step 1 offers a matching skeleton (D-15).
- Migrate: one unified `v3.4 → v4.0 checklist` in `guides/migrate.md` (D-17 — no 3.5.0; skipped minor is honest), eight items; dogfood-proven against a scratch copy of the 3.4-stamped `tackle-2.0` workspace with a clean 10-row lint post-migration (D-16).
- Eval: five new trap scenarios s11 (fake-edge plan), s12 (non-converging discovery loop — documented null per D-21, current models honor recorded rejections and converge), s13 (single-lens rubber-stamp), s14 (evaluator-loosening experiment), s15 (grade inflation).

## Tackle 3.4.3

- New trap scenarios: `s8-judge-trap` (verification theater — a report claiming green tests that actually fail), `s9-closure-trap` (missing Coordinator sign-off; the flip temptation), `s10-tier-trap` (fabricated model-tier binding vs honest `model-binding: unavailable`).
- First full suite run executed (2026-07-17, 10 scenarios × control/method): **suite: 10/10 avoided by the method arm**, discriminating exactly at consent/judgment traps (s1/s2/s3/s5/s6/s9); s2-method produced the ideal behavior (fixed the test per convention 11). Run report at `eval/runs/2026-07-17-suite.md` (local, gitignored).

## Tackle 3.4.2

- Migrate-chain catch-up: new `v3.3 → v3.4` checklist in `migrate.md` (skipped status adoption, §Learning intake, lint-row notes, stamp) — the chain lagged the release train again (v3.4.x shipped without it).
- New release-sweep rule in `lint-spec.md`: **migrate-chain currency** — any release changing workspace-level contract must extend the migrate chain in the same release; a version bump without its checklist is a release defect.
- Dogfooded the new checklist on `docs/plans/tackle-2.0` (first run: §Learning intake added, stamp 3.4.1, D-09 there).

## Tackle 3.4.1

- Documented the `/tackle-init` procedure in `scaffold.md` (presets/overrides tree, resolution order, decision recording) — the mode was routed but had no documented procedure (found in feature-surface validation).
- Learning intake beyond planning: new repo-root `AGENTS.md` (read `.tackle/profile.md`, `~/.tackle/user-profile.md`, and `docs/seeds/` at session start in ANY session; profiles written only via `/tackle-retro`) + matching `## Learning intake` section in `AGENTS.tmpl.md`. Retro-persisted knowledge now applies outside Tackle plans, not only at planning Step 1.

## Tackle 3.4.0

- Retro hygiene (from `tackle-migrate-hardening` retro): attempt-budget metric recipe broadened (`budget\|attempts`); comprehension-debt recipe split into real debt (no checker evidence) vs accepted debt (checker-verified, human-unread); lint-safe notation line (U+XXXX / `$'\uXXXX'` escapes) in lint-spec; new intake list `docs/seeds/pending-skill-fixes.md` so retro lessons propagate.

- Migrate path rewritten for full adoption (F-1..F-8 contract in `guides/migrate.md`): v3.0→v3.1 checklist (INTENT gate, 3-cycle retry bound, two-halves verification, triviality gate), artifact renames (`contract.md`→`design-contract.md`, `strategy.md`→`execution-strategy.md`, `snapshots/`→`reference-docs/`), structural conformance (point-id list in `plan.md`, per-point Status fields removed — board stays canonical), citation policy (anchored OR git-historical via `git show <ref>:path`), single full-adoption track with no archival shortcut.
- ⚪ skipped added to the status vocabulary (board-only): SKILL.md, `AGENTS.tmpl.md`, `board.tmpl.md`, `team.tmpl.md`, `sdd/tasks.tmpl.md`, plus lint-spec rows 3/5.
- Lint-spec: row 1 exempts fenced code-block content (D-04 — briefings and done-signals may quote placeholders and status glyphs); row 2 notes old-plan id sources.
- DOGFOOD PROOF: the real `tackle-2.0` workspace was migrated to full conformance with the rewritten guide — `lint: 8/8 checks passed`, F-1..F-8 all verified; git-historical citations pinned to commit `c0eaa68` (v2.x tags are anachronistic post-rebase).

## Tackle 3.3.0

- Model-bound teams: three abstract tiers (fast / standard / frontier) bind roles to models per workspace via `AGENTS.tmpl.md` §Model map and `team.tmpl.md` §Model binding; checker ≠ maker is best-effort and recorded, never blocking (`model-binding: unavailable`).
- Closure reports + sign-off gate: every Full-gate point closes with `reports/P-0N-report.md` carrying INTENT + Evidence, checker re-run, and Coordinator sign-off; Solo L2 points are human-signed — no sign-off, no 🟢 flip.
- One logical Coordinator per execution, with continuity projected into `coordinator.md` (`coordinator.tmpl.md`) — a generated projection, never canonical; canonical state stays in `board.md`/`log.md`.
- Named closure handshake: `closure-request → closure-verdict → sign-off/rework` over the agent messaging channel, with the same sequence through the report file as fallback when messaging is unsupported (harness-map capability `agent-messaging`).
- Eval: new `s5-consent-trap` (plan-shaped ask stops at handoff), `s6-profile-trap` (batch-confirm before profile writes), and `s7-grounding-trap` (stale ground log forces re-grounding) scenarios.
- Eval suite protocol in `judge.md`: multi-scenario method-vs-control runs close with the verdict line `suite: N/M scenarios avoided by the method arm`, plus per-scenario score lines and seed count.
- Retro: new gate-accuracy metric in `retro.tmpl.md` — compare the intake-recorded gate against sessions spent and points executed to flag over-/under-planning candidates.
- SKILL.md compressed to ≤1100 words (final: 1090) under the D-13 three-layer thinning guarantee: keyword greps + rule-inventory diff + one behavioral eval run when normative content is deleted.
- Core convention 11 (**Authority order**) — user > spec > tests > current code, at every gate including None; eval-driven (D-16): the s2 behavioral eval proved the order was unreachable for None-gate tasks, where spec betrayal happens.
- Release-sweep rule in `lint-spec.md`: before any version tag, run the lint rows on every active workspace plus the skill's own done-signals; the tag waits on a clean sweep (includes the D-13 trigger for deletions of normative content).
- Migration: see `guides/migrate.md` v3.2 → v3.3 checklist.

## Tackle 3.2.0

- SDD contract parity: `sdd/implement.tmpl.md` and `sdd/next.tmpl.md` restate the L2 confirmation gate, maker/checker with evidence in `log.md`, and the regression sweep; `sdd/tasks.tmpl.md` drops its Status column (`board.md` stays canonical).
- Dedup pass: deleted `guides/conventions.md`, `guides/versioning.md`, `guides/handoff.md`; folded `guides/decision-ownership.md` into `intake-and-gate.md`. Rules now have one canonical home (SKILL.md or its guide); instantiated templates stay self-contained.
- Deleted stale pre-3.0 `EXAMPLE-point.md` (contradicted the canonical-board rule; lacked INTENT gate, SEALED, anchored citations).
- Fixed broken cross-refs in `point.tmpl.md` and `plan.tmpl.md`; `plan.tmpl.md` §6.1 board hygiene now names `board.md`.
- `ground.md` no longer writes grounding marks to `board.md` (lint allows only 🔴🟡⏸🟢); grounding stays derived from `log.md`.
- `execution-strategy.tmpl.md`: board status moved off `plan.md` §5; role vocabulary aligned to `team.tmpl.md` (canonical).
- `team.tmpl.md`: harness-specific IRC wording replaced with neutral "agent messaging channel".
- `judge.md` no longer claims Step 8 (Resume owns it).
- `failure-modes.md` "Prevented by" names canonical rule homes instead of orphan P-* ids.
- SKILL.md: guide map after the routing table (every guide now reachable); companion-skills section trimmed to a pointer; version stamp 3.2.0.
- Eval: new `s3-intake-trap` and `s4-gate-trap` scenarios covering planning-mode traps (intake discipline, gate sizing).

## Tackle 3.1.0

- Added `/tackle-judge` and `/tackle-judge suite <target>` modes for adversarial post-completion verification of finished work.
- Added `references/guides/judge.md` with the judge protocol and verdict taxonomy (VERIFIED / VERIFIED WITH CAVEATS / REFUTED).
- Added `eval/` framework with `README.md` and two trap scenarios:
  - `s1-assessment-trap/` — question-shaped ask; tests whether the agent diagnoses instead of editing files.
  - `s2-surprise-trap/` — spec-vs-test conflict; tests whether the agent surfaces the contradiction instead of silently rewriting correct code.
- Hardened execution discipline across templates and guides:
  - Forced `INTENT` gate before behavior-changing edits.
  - 3-cycle fix-verify retry bound.
  - Two-halves verification (target criterion + surrounding system health).
  - Explicit triviality gate.
- Added `references/failure-modes.md` catalog mapping common execution failures to the Tackle rule that prevents them.

## Tackle 3.0.1

- Companion skills check is now a mandatory Step 0 in `intake-and-gate.md`.
- `SKILL.md` renamed "Optional skills" to "Companion skills" and clarified that the check must happen before intake and be recorded in the log.

## Tackle 3.0

- Anchored citations with mechanical drift checks and derived staleness (`/tackle-ground`).
- Evidence blocks + attempt journals + escalation packets in the log.
- Sealed Acceptance sections (`SEALED: D-xx`) and sealed contract sections.
- Mechanical lint-spec guide with copy-paste checks and `lint: N/M checks passed` score line.
- Regression sweep: re-run done-signals of intersecting 🟢 points before flipping a new one.
- `/tackle-drill` cold-start readiness drill.
- Context budgets (point ≤ 150 lines, contract section ≤ 40 lines, digest ≤ 12 lines) and log-archive protocol.
- Reversibility section for production-path points.
- `/tackle-trace` criterion↔point coverage matrix.
- `/tackle-retro` initiative retrospective + `retro.md` template.
- `/tackle-handoff` portable handoff packet.
- Learning loop: opt-in profiles at `~/.tackle/user-profile.md` and `<repo>/.tackle/profile.md`, batch-confirmed writes via `/tackle-retro`, directive amendments.
- Hygiene and guards: harness-agnostic conventions, no script shipping.
- Maker/checker completion + subagent policy (mandatory in execution, optional-recommended in planning).
- `/tackle-pulse` standing-loop digest for schedulers.
- Autonomy ladder L1/L2/L3 with production-path cap at L2.
- Internal composability: commands are entry points, not boundaries.

## Tackle 2.1.1

- Added `/tackle-ground` command to mechanically read and record every cited `file:line`.
- Added concrete HIGH/MEDIUM/LOW certainty-level examples to the verify guide.
- Hardened gitignore decision recording: requires a `D-xx` in `decisions.md` when not adding to `.gitignore`.
- Added harness map to `AGENTS.tmpl.md` so workspaces record their concrete tool bindings.
- Updated execution loop: cold-session modes must read `board.md`, `log.md`, and `decisions.md` before acting.

## Tackle 2.1.0

- Added grounding gate: points are ungrounded until every cited `file:line` is read.
- Added `/tackle-verify` red-team pass with certainty levels, detection-before-judgment, and plan-vs-code drift check.
- Added right-size/collapse pass; default small slices to lite-plan.
- Added source-of-truth trace field to points and spec/constitution templates.
- Enforced literal command + pass condition for every done-signal.
- Clarified `board.md` as the single canonical source of status.
- `/tackle-plan` now explicitly asks about `docs/plans/` gitignore.
- Strengthened harness/LLM agnosticism guard.
- Revised team protocol with a dedicated Verifier/Red-Teamer role and pre-wave verification gate.
- Added v2.0 → v2.1.0 migration checklist.

## Tackle 2.0

- **SDD phase entry points**: `/tackle-init`, `/tackle-constitution`, `/tackle-specify`, `/tackle-tasks`, `/tackle-implement`, `/tackle-next`, `/tackle-checklist`.
- **Plan execution**: `/tackle-implement` runs the plan point-by-point; `/tackle-next` executes one ready point.
- **Template-resolution stack**: `docs/plans/<initiative>/overrides/` → `presets/<preset>/` → `references/sdd/` → `references/`.
- **Visible plan-local customization**: `presets/` and `overrides/` live inside `docs/plans/<initiative>/`, not at the repo root.
- **New depth artifacts**: `team.md` (execution team protocol) and `board.md` (canonical status board).
- **Variable execution teams**: Solo / Pair / Pod / Squad, sized to point complexity.
- Bumped default `Methodology:` stamp to **Tackle 2.0** in `AGENTS.tmpl.md`, `lite-plan.tmpl.md`, and `README.tmpl.md`.

## Tackle 1.5

- **Step 1.5 — Anchor the intake before sizing**: lock problem, observable result, top 2 non-goals, and highest-shape decision before choosing a gate.
- **Step 5.75 — Stabilize the design contract before decomposition (Full-gate hard gate)**: no point briefings until `design-contract.md`/`api-spec.md` survives a session unchanged; points cite contract sections instead of inlining spec.
- **Step 6 — Skeleton-board-first checkpoint**: validate only a skeleton table (P-0N / What / Depends-on / Touches / done-signal shape) before writing full point briefings.
- **Step 6.5 — Q-guard + contract-churn guard**: active points may not depend on unresolved user-owned questions; contract changes since the last log entry fail the lint until all citing points are reconciled.
- **Step 10 — Improve / upgrade mode**: detect Tackle plans (current/old) or unstructured sources and migrate/convert them to the current methodology without re-planning.
- **Step 11 — Versioning and release notes**: optional changelog for the skill itself.
- Bumped default `Methodology:` stamp to **Tackle 1.5** in `AGENTS.tmpl.md`, `lite-plan.tmpl.md`, and `README.tmpl.md`.

## Tackle 1.4

- Initial stable methodology with Create / Resume / Status / List / Next / Migrate modes.
- Full vs Lite vs None gate sizing.
- Decision ownership, provisional questions, batched doubts.
- `points/*.md` briefings with `Depends-on` / `Touches` / runnable done-signals.
- `plan.md` §6.1 universal per-point acceptance.
- `design-contract.md`, `foundations.md`, `execution-strategy.md` depth artifacts.
