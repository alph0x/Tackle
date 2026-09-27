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
