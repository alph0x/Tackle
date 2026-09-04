# Usage ledger — {{TITLE}}

## Legacy compatibility ledger

One markdown table, one row per **role run**, appended at role close. `Point` is `PLAN`
(planning session, row appended at plan handoff), `RETRO` (retro session, appended at retro
close), or `P-xx` (execution of point P-xx). `Role` is the team role that ran (`Driver`,
`Checker`, `Coordinator`, …); planning/retro rows use `Planner` / `Retro`. `Tier`, `Model`,
and `Effort` are the bound tier, the concrete model the harness actually ran, and the effort
level actually used (vocabularies per `AGENTS.md` §Harness map / §Model map). `Tokens in` /
`Tokens out` are integers as the harness exposes them: a partial harness (cumulative total
only, no in/out split) records the total in **Tokens in** and `n/a` in **Tokens out**; any
field the harness does not expose is `n/a` — **never estimated**. `Session` is
`YYYY-MM-DD sN`, matching the `log.md` entry. Recording is informative, never gating: a
missing value is `n/a`, not a missing row.

| Point | Role | Tier | Model | Effort | Tokens in | Tokens out | Session |
|---|---|---|---|---|---|---|---|

## v2 lifecycle ledger

Schema: tackle-observability/2

New workspaces append one lifecycle row per observed role event. The exact column order is:

| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

`Event` is `start`, `finish`, or `observe-incomplete`. Append `start` before substantive work and
one terminal `finish` at role close. If a role ends abruptly, append `observe-incomplete` when it is
observed; never invent an end time or duration. `Run ID` defaults to
`<YYYY-MM-DD-sN>/<point>/<role>/<ordinal>` and is unique within the workspace. Unavailable
Harness, Model, Effort, Attempts, Rework, and Verification values are `n/a`, never estimated.
Lifecycle recording is informative and never gates point closure.

Optional exact telemetry is an additive `usage.telemetry.jsonl` sidecar described in
`references/guides/usage-observability.md`; the lifecycle table remains useful when the sidecar is
absent.
