# Usage ledger — {{TITLE}}

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
