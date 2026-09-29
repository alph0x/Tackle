# Resource usage ledger — {{TITLE}}

New Coordinated (Full) workspaces use this v2-only ledger. For Focused (Lite), use the body in `lite-plan.tmpl.md`.
A validation end must never be copied as a role end; use `At=n/a` when the role end was not observed and record the reason in Source.

## v2 lifecycle ledger

Schema: tackle-observability/2

New workspaces append one lifecycle row per observed role event. The exact column order is:

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

`Event` is `start`, `finish`, or `observe-incomplete`. Append `start` before substantive work and
one terminal `finish` at role close. If a role ends abruptly, append `observe-incomplete` when it is
observed; never invent an end time or duration. `Run ID` defaults to
`<YYYY-MM-DD-sN>/<task>/<role>/<ordinal>` and is unique within the workspace. Unavailable
Harness, Model, Effort, Attempts, Rework, and Verification values are `n/a`, never estimated.
Attempts and rework retain the shared Run counters across actors and resumptions; they never reset
for a new role or session. Lifecycle recording is informative and never gates task closure.

Optional exact telemetry is an additive `resource-usage.telemetry.jsonl` sidecar described in
`references/guides/usage-observability.md`; the lifecycle table remains useful when the sidecar is
absent.
