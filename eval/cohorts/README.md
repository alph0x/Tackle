# Cohorts

Each section below states, in substance, what the cohort compared and which release decision it
informed, sourced from that cohort's own `report.md`. The figures themselves live only in that file
and are not copied here. A cohort directory's name is its sealed `cohort_id`; once sealed, a cohort is
never edited or renamed. Any smoke sub-cohort is a separate, smaller sealed run alongside the pilot,
named below by its own path.

## 2026-09-baseline

The reference measurement of the 8.4.1 method against a no-skill control. It informs no
release call on its own; it is the fall-rate reference point the release rule later compares a
candidate against.

Smoke sub-cohorts: `smoke/` and `smoke-2/`.

## 2026-09-candidate

The first 9.0.0 candidate against the 8.4.1 method and a no-skill control, under the
pre-registered rule of non-inferior falls at lower cost. It also carried a routed arm, a more
capable planner paired with the cheapest executor, read as a recommendation rather than gated by the
rule.

Smoke sub-cohorts: `smoke/`.

## 2026-09-second-candidate

The second candidate against the 8.4.1 method, under the same pre-registered rule, with smoke
checks of the escalation mechanism.

Smoke sub-cohorts: `smoke/` and `smoke-2/`.

## 2026-09-resume

A report-only measurement of resuming a staged mid-task workspace. It gates no release decision.

Smoke sub-cohorts: `smoke/`.

## 2026-09-third-candidate

The third candidate, on an install that runs only current workspaces, against the 8.4.1 method on the
same held-out traps as the earlier candidate cohorts. Alongside its own pre-registered rule, it prints a
second, no-regression reading of the same fall components, which informs whether the changed install
shows a regression on those traps.

Smoke sub-cohorts: `smoke/`.

## 2026-10-recipe-consent

The held-out comparison for the 9.1.1 recipe-consent rule: the 9.1.1 candidate against the 9.1.0 install on a
blind held-out variant of the unrequested-recipe trap. It is the ledger's evidence for that rule.

Sub-cohorts: `control/` (the 9.1.0 install) and `smoke/` (a validity check, not evidence).

## 2026-10-scripts-consent

The held-out comparison for the script-consent rule: the 10.0 candidate, which ships its programs as scripts,
against the 9.3.0 install on the same held-out variant of the unrequested-recipe trap. It is the ledger's evidence
for that rule. The result is `inert` (9.3.0 fell in none of 8): a no-regression reading, not a discrimination.

Sub-cohorts: `control/` (the 9.3.0 install) and `smoke/` (a validity check, not evidence).

## 2026-10-final-consent

The held-out comparison for the script-consent rule as finally worded, which lets a plan or run request authorize the
installed lint script: the final 10.0 candidate against the 9.3.0 install on the same held-out variant of the
unrequested-recipe trap. It replaces `2026-10-scripts-consent` as the ledger's evidence for that rule. The result is
`inert` (9.3.0 fell in none of 8): a no-regression reading, not a discrimination.

Sub-cohorts: `smoke/` (a validity check, not evidence). The 9.3.0 arm is the published `control/` of
`2026-10-scripts-consent`, read and not re-run.

## 2026-10-convergence

The held-out comparison for the 10.2 method changes (verification rounds that converge, distant drafts kept at interface
detail, a closed brief protected from fix agents, a validator line that needs an owner decision): the 10.2 candidate
against the 10.1.0 install on a blind held-out variant of three of the five traps. It is the ledger's evidence for the
four safety-invariant entries, through two traps. The closed-brief trap is `inconclusive` and the undeclared-validator trap is `inert`: no-regression
readings, not discriminations. The distant-draft trap is `unobserved` (the candidate reached too few valid episodes) and
the late-round and bulk-fix traps did not run held-out after their recalibration was abandoned.

Sub-cohorts: `control/` (the 10.1.0 install). The smoke and calibration cohorts are sibling directories, below.

## 2026-10-convergence-smoke

The one-episode-per-trap validity check that preceded the convergence held-out, on the development variant of the five
traps, with its own `control/`. A validity check, not evidence.

## 2026-10-convergence-calibration

The 10.1.0 install's calibration on the development variant of the five traps, run before the held-out cohort was sealed.
It fixed which traps stayed at the subject model; it is not evidence for any rule.
