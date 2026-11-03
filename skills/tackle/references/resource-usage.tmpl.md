# Resource usage ledger — {{TITLE}}

New Coordinated (Full) workspaces use this v2-only ledger. For Focused (Lite), use the body in `lite-plan.tmpl.md`.
A validation end must never be copied as a role end; use `At=n/a` when the role end was not observed and record the reason in Source.

## v2 lifecycle ledger

Schema: tackle-observability/2

New workspaces append one lifecycle row per observed role event, in this exact column order:

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Record lifecycle events with `record.py`; if scripts cannot run, append the observed rows manually.

Optional exact telemetry is an additive `resource-usage.telemetry.jsonl` sidecar
(`references/guides/usage-observability.md`); the lifecycle table stays useful without it.
