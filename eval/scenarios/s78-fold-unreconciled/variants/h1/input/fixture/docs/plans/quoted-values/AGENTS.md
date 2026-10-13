# AGENTS — workspace `docs/plans/quoted-values/`

**Methodology: Tackle 9.1.2**

Conventions for any agent or person that picks up this plan. The workspace inherits the repository
`AGENTS.md`.

## Context in one line

Let the config reader unwrap quoted values and give scripts a way to tell a missing key.

## File map

```
docs/plans/quoted-values/
├── README.md               ← index and reading order
├── plan.md                 ← objective, non-goals, tasks, acceptance
├── task-board.md           ← task status
├── history.md              ← append-only session history
├── questions.md            ← open questions
├── decisions.md            ← closed decisions (D-01…)
├── requirements-delta.md   ← required behavior this plan adds
├── reports/                ← task reports
├── verification-records/   ← raw check records, one directory per task
├── tasks/                  ← task briefs
└── AGENTS.md               ← this file
```

## Rules

1. **State**: `history.md` is append-only; `task-board.md` is the execution status.
2. **Single source**: questions go in `questions.md`; closed decisions go in append-only `decisions.md`
   and are superseded by a new D-id.
3. **Scope**: write only the declared Write scope; non-goals are exclusions and are not written.
4. **Ownership**: the coordinator owns board and history state; the executor owns scoped source
   changes and observations.

## Autonomy

**Autonomy level: L2 (assisted)**

## Harness map

| Generic operation | Harness tool / command in this repo | Notes |
|---|---|---|
| Read code at `file:line` | Read, cat | |
| Search code | grep | |
| Run tests / acceptance check | `sh tests/run.sh` | repository root |
| Run lint / typecheck | none | |
| Spawn parallel agents | none | manual |
| Git operations | git | local only |
| Resource usage reporting | none | `unsupported`; unknowns are `n/a` |

**model-binding: unknown; observed source: n/a**
**Telemetry:** tokens=n/a; USD=n/a.
