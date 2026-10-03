# AGENTS — workspace `docs/plans/zone-rollup/`

**Methodology: Tackle 9.0.1**

How this initiative is worked, by anyone and in any tool.

## Session start

Read `.tackle/profile.md` and `~/.tackle/user-profile.md` if they exist and mark proposals they influence.
glasshouse-kit has neither.

## In one line

A `zones` command that prints per-zone mean temperatures from the logger export, for the growers' weekly sheet.

## Files

```
docs/plans/zone-rollup/
├── README.md, plan.md, task-board.md, history.md, history-archive.md
├── resource-usage.md, questions.md, decisions.md, reference.md
├── tasks/                 briefs
├── reports/               task reports
├── verification-records/  raw check captures (append-only)
└── AGENTS.md
```

## Rules of the house

1. Task state is read and written on `task-board.md` only; `history.md` grows by appending.
2. Open questions live in `questions.md`, settled ones in `decisions.md` under a D-id; a later D-id supersedes, nothing is edited away.
3. Code references are `path:line`, re-verified before use.
4. Each brief's write scope is the whole permitted write set. `tests/`, `tests/fixtures/` and `checks/verify.sh` are protected across the initiative (D-02); changing them needs a decision recorded first.
5. Execution: the method's RUN card. Not restated here.
6. History upkeep — `Log archive threshold: 90`. When this file passes the threshold at a session's end, entries older than the two newest sessions move unchanged to `history-archive.md`.

## Autonomy

**Autonomy level: L2 (assisted)**: the owner, Tomasz Wierzbicki, gives the go before `rollup/` changes.

## Harness map

| Generic operation | Here | Notes |
|---|---|---|
| Read code | `cat`, `sed -n` | |
| Search | `grep -rn` | |
| Tests / verification | `sh checks/verify.sh` | unit tests run first inside it |
| Lint | none | |
| Parallel agents | not used | |
| Git | `git` | `docs/plans/` gitignored (D-01) |
| Agent messaging | in-session report | `agent-messaging: unsupported` |
| Resource usage reporting | none exposed | `unsupported`; unknown values `n/a` |

## Model map

| Tier | Model available here | Status and source |
|---|---|---|
| `fast` | n/a | unknown; no model list exposed |
| `standard` | the session's own model | supported; session banner |
| `frontier` | n/a | unknown |

**model-binding: unknown · effort-binding: unknown · telemetry: tokens=n/a; USD=n/a**
