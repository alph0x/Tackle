# Resource usage ledger — {{TITLE}}

New Coordinated (Full) workspaces use this v2-only ledger. For Focused (Lite), use the body in `lite-plan.tmpl.md`.
A validation end must never be copied as a role end; use `At=n/a` when the role end was not observed and record the reason in Source. `At` is a clock in the form `YYYY-MM-DDTHH:MM:SS[.fff](Z|±HH:MM)`; minute-only and space-separated clocks are unmeasured.

## v2 lifecycle ledger

Schema: tackle-observability/2

New workspaces append one lifecycle row per observed role event, in this exact column order:

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

`Event` is `start`, `finish` or `observe-incomplete`: append `start` before substantive work and one terminal
`finish` at role close; for a role that ends abruptly, append `observe-incomplete` when observed, never inventing
an end time or duration. `Run ID` defaults to `<YYYY-MM-DD-sN>/<task>/<role>/<ordinal>`, unique within the
workspace. Unavailable Harness, Model, Effort, Attempts, Rework and Verification values are `n/a`, never
estimated. Attempts and rework retain the shared Run counters across actors and resumptions; they never reset
for a new role or session. Lifecycle recording is informative and never gates task closure. Outcome is
`running` for start, `success`/`failed`/`blocked`/`aborted` for finish and `incomplete` for observe-incomplete.
Product acceptance prose stays in Verification/Source, even when the role finishes successfully. A positive
Attempts count needs a relative trace reference or stable event identifier for task-matched failed correction
validation or one declared authorized escalation; count labels, initial checks, dispatches and repeated tests
alone do not support it. Preserve distinct cycles across actors, counting a duplicate event only once. `0`
requires observed absence with its source; use `n/a` when support is unknown.

Optional exact telemetry is an additive `resource-usage.telemetry.jsonl` sidecar
(`references/guides/usage-observability.md`); the lifecycle table stays useful without it.
