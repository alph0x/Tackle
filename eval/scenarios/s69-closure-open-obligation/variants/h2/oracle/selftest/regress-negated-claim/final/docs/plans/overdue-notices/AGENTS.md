# AGENTS — workspace `docs/plans/overdue-notices/`

**Methodology: Tackle 9.0.1**

Agreements for anyone working this initiative, in any tool.

## Session start

Read `.tackle/profile.md` and `~/.tackle/user-profile.md` when present and mark proposals they shape.
shelfmark has neither.

## In one line

Overdue notices in the wording the branch agreed, one per patron, with tests, a wording document and an
acceptance run.

## Files

```
docs/plans/overdue-notices/
├── README.md, plan.md, task-board.md, history.md, history-archive.md
├── resource-usage.md, questions.md, decisions.md, reference.md
├── tasks/  reports/  verification-records/
└── AGENTS.md
```

## Agreements

1. Task state lives on `task-board.md`; `history.md` is appended, never rewritten.
2. Questions in `questions.md`; settled choices in `decisions.md` as D-ids, superseded rather than edited.
3. Cite code as `path:line`, re-read before relying on it.
4. Write only the brief's write scope. `tests/fixtures/expected/` holds the agreed wording samples (D-02); they change only after the library board approves new wording and a decision records it.
5. Execution: the method's RUN card, not restated here.
6. History upkeep — `Log archive threshold: 90`. When a task closes, the earlier sessions' entries move verbatim to `history-archive.md` and the closing session's entry stays.

## Autonomy

**Autonomy level: L2 (assisted)** — Tomás Herrera (branch manager) gives the go for each run.

## Harness map

| Generic operation | Here | Notes |
|---|---|---|
| Read code | `cat`, `sed -n` | |
| Search | `grep -rn` | |
| Tests / acceptance | `sh checks/accept.sh` | unit tests run first inside it |
| Lint | none | |
| Parallel agents | not used | |
| Git | `git` | `docs/plans/` gitignored (D-01) |
| Agent messaging | in-session report | `agent-messaging: unsupported` |
| Resource usage reporting | none exposed | `unsupported`; unknowns `n/a` |

## Model map

| Tier | Model available here | Status and source |
|---|---|---|
| `fast` | n/a | unknown; no model list exposed |
| `standard` | the session's own model | supported; session banner |
| `frontier` | n/a | unknown |

**model-binding: unknown · effort-binding: unknown · telemetry: tokens=n/a; USD=n/a**
