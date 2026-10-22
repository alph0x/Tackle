# AGENTS — workspace `docs/plans/locker-pickup/`

**Methodology: Tackle 10.1.0**

Conventions for any agent or person that picks up this plan, whatever tool it runs in. The workspace
inherits the repository contract where one exists.

## Learning intake (session start)

If `.tackle/profile.md` or `~/.tackle/user-profile.md` exists, read active hypotheses before
proposing defaults and tag proposals `(from your profile)`. If the host repo has `docs/seeds/`,
check it for pending items when planning. Profiles are written only by the `retro` workflow; seeds are
deliberate writes.

## Context in one line

Let customers collect parcels from the lockers with a code, and send back what nobody collects.

## File map

```
docs/plans/locker-pickup/
├── README.md          <- index, objective, reading order
├── plan.md            <- objective, non-goals, task decomposition, acceptance criteria
├── task-board.md      <- canonical status board for execution
├── history.md         <- append-only session history
├── resource-usage.md  <- lifecycle ledger
├── questions.md       <- single source of questions
├── decisions.md       <- closed decisions register
├── tasks/             <- self-contained task briefs
├── reports/           <- task reports
└── AGENTS.md          <- this file
```

## Rules

1. **State**: `history.md` is append-only; `task-board.md` is the execution status. Maintain projections and archive under the authorized local policy; STATUS remains read-only.
2. **Single source**: questions go in `questions.md`; closed decisions go in append-only
   `decisions.md` and are superseded by a new D-id.
3. **Reference verification**: ground claims in verified `file:line` citations.
4. **Scope**: write only the declared Write scope; non-goals are explicit exclusions and must not be
   written.
5. **Execution**: Tackle’s run workflow governs authorization, preflight, state transitions,
   target/surround and integrated acceptance, persistent correction budgets, recovery, evidence,
   and closure. The Task acceptance check and `plan.md` §6.1 remain required inputs.
6. **Ownership**: the `run` request follows `task-board.md` in dependency order. The Coordinator owns
   task board/history state; the Executor owns scoped source changes and observations.

## History maintenance

**History maintenance policy**: when `history.md` is over 400 lines at a RUN session boundary, move every session entry older than the newest five, verbatim and in order, to `history-archive.md`, keep the newest State snapshot, and record the before and after sizes once.

## Autonomy

**Autonomy level: L2 (assisted)**

- **L2 (assisted)** — default: explicit Run intent precedes source mutation.

## Validation

Readiness is settled by the project validator, not by reading: run it against this workspace before any task is called Ready to run, and it must exit 0. It only looks at the board and the briefs, so it is safe to run at any time.

Acceptance validator: python3 tools/plan_lint.py

## Harness map

| Generic operation | Harness tool / command in this repo | Notes |
|---|---|---|
| Read code at `file:line` | Read, cat | |
| Search code | grep | |
| Run tests / acceptance check | `python3 -m unittest discover -s tests` | planning-repository root |
| Run lint / typecheck | none | |
| Readiness check | `python3 tools/plan_lint.py` | see Validation |
| Spawn parallel agents | none | manual |
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

## Status / next

Resume by reading this file, then `task-board.md`, then the newest State snapshot in `history.md`.
