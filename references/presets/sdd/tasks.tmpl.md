---
initiative: {{INITIATIVE_NAME}}
created: {{DATE}}
source: docs/plans/{{INITIATIVE_NAME}}/plan.md §5
---

# Tasks — {{INITIATIVE_NAME}}

## How this file was produced

This checklist is derived from `docs/plans/{{INITIATIVE_NAME}}/plan.md` §5 (Point decomposition). If `plan.md` §5 is missing, suggest running `/tackle-plan` first, then produce a degraded, empty `tasks.md` scaffold with a note pointing to the missing source.

## Task checklist

<!-- One row per point from plan.md §5, numbered T-01..T-NN in dependency order. Status: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done -->

| ID | Task | Source point | Owner | Depends on | Done-signal | Status |
|---|---|---|---|---|---|---|
| T-01 | {{title from P-01 What}} | {{P-01 slug}} | {{agent or empty}} | - | {{done-signal from P-01 briefing}} | 🔴 not started |
| T-02 | {{title from P-02 What}} | {{P-02 slug}} | {{agent or empty}} | T-01 | {{done-signal from P-02 briefing}} | 🔴 not started |
| T-NN | {{...}} | {{...}} | {{...}} | {{previous task or -}} | {{...}} | 🔴 not started |

## Notes / execution log

<!-- Update during execution: blockers, handoffs, decisions, and status changes. Keep entries terse and append-only. -->

- {{DATE}} — {{note}}
