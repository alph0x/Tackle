# AGENTS — workspace `docs/plans/column-totals/`

**Methodology: Tackle 9.1.0**

Conventions for any agent or person that picks up this plan. The workspace inherits the repository
`AGENTS.md`.

## Context in one line

Let the tally skip a header line so exported CSV files can be summed as delivered.

## File map

```
docs/plans/column-totals/
├── README.md          ← index and reading order
├── plan.md            ← objective, non-goals, tasks, acceptance
├── task-board.md      ← task status
├── history.md         ← append-only session history
├── resource-usage.md  ← lifecycle ledger
├── questions.md       ← open questions
├── decisions.md       ← closed decisions (D-01…)
├── reports/           ← task reports
├── verification-records/ ← raw check records, one directory per task
├── tasks/             ← task briefs
└── AGENTS.md          ← this file
```

## Rules

1. **State**: `history.md` is append-only; `task-board.md` is the execution status.
2. **Single source**: questions go in `questions.md`; closed decisions go in append-only `decisions.md`
   and are superseded by a new D-id.
3. **Reference verification**: ground claims in verified `file:line` citations.
4. **Scope**: write only the declared Write scope; non-goals are exclusions and are not written.
5. **Execution**: the Run protocol in `references/guides/run-card.md`, with depth in
   `references/guides/run.md`. The task acceptance check and `plan.md` §6.1 are required inputs.
6. **Ownership**: the coordinator owns board and history state; the executor owns scoped source
   changes and observations.

## History maintenance

**History maintenance policy**: when `history.md` is over 400 lines at a RUN session boundary, move every session entry older than the newest five, verbatim and in order, to `history-archive.md`, keep the newest State snapshot, and record the before and after sizes once.

## Autonomy

**Autonomy level: L2 (assisted)**

## Harness map

| Generic operation | Harness tool / command in this repo | Notes |
|---|---|---|
| Read code at `file:line` | Read, cat | |
| Search code | grep | |
| Run tests / acceptance check | `sh tests/run.sh` | repository root |
| Run lint / typecheck | none | |
| Verification record capture | none | `unsupported`: the harness keeps no exportable tool log after the session |
| Spawn parallel agents | none | manual |
| Git operations | git | local only |
| Agent messaging | report | `agent-messaging: unsupported` |
| Resource usage reporting | none | `unsupported`; unknowns are `n/a` |

## Model map

| Tier | Concrete model actually available in this harness | Capability status and observed source |
|---|---|---|
| `fast` | n/a | unknown; not observed |
| `standard` | n/a | unknown; not observed |
| `frontier` | n/a | unknown; not observed |

**model-binding: unknown; observed source: n/a**
**effort-binding: unknown; observed source: n/a**
**Telemetry:** tokens=n/a; USD=n/a.

Resume in the order of `references/guides/status.md#cold-resume-read-order`.
