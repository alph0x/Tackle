# Seed — Tackle harness + hardening initiative (mostly absorbed)

**Status:** W1 ABSORBED into `tackle-model-teams` as P-12/P-13 (D-15, 2026-07-16) — suite as protocol, no software runner. What remains parked here: the **CI hook** (repo infrastructure: run lint + eval suite automatically on skill changes) and any future scenario ideas beyond s6/s7. Intake via `/tackle-plan` when the CI hook is wanted.

## Origin

Strict skill evaluation, 2026-07-16 (recorded in `docs/plans/tackle-model-teams/log.md` session 4, D-14).

## W1 — The mother weakness: the skill does not verify itself

- 26 routed modes; 4 trap scenarios (`eval/scenarios/`); zero automation — lint, eval, and done-signals all run by hand; no CI in the repo.
- ~19 of 26 modes have no behavioral validation at all: drill, trace, pulse, handoff, retro, migrate, improve, learning loop, checklist, constitution, specify, tasks…
- The skill's core claim is mechanical verification; its own repo verifies nothing automatically.

## Candidate scope (to size at intake)

1. **Eval harness automation** — the `workflow.js` deferred by `tackle-fable-judge` D-02: run a scenario (control/method arms), capture reports, diff against fixtures, judge, emit scores. Harness-agnostic, no shipped runtime deps if possible.
2. **Scenario expansion** — one trap per unvalidated high-risk mode cluster: resume/status grounding-age, retro profile writes (opt-in violation trap), migrate (old-format plan), improve (unstructured source).
3. **CI hook** — a documented way to run lint + eval suite on skill changes (release-sweep rule from 3.3.0 P-07 becomes executable).
4. **W3 follow-through** — explore mechanical fabricated-evidence detection (evidence-block output vs re-run diff); if none found, keep the accepted-residual row 15 in `failure-modes.md`.

## Explicitly out (decided 2026-07-16)

- W2 (s5 consent trap) and W5 (gate-accuracy retro metric) — shipped earlier as P-10/P-11 of `tackle-model-teams` (D-14).
