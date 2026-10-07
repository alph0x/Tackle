# AGENTS — workspace `docs/plans/fee-statements/`

**Methodology: Tackle 9.0.1**

What anyone working this initiative agrees to, whatever tool they use.

## Session start

Read `.tackle/profile.md` and `~/.tackle/user-profile.md` when present and mark the proposals they shape.
plotbook has neither.

## In one line

Printed fee statements for every plot, rendered from the plot register by one command, with the layout
written down and an acceptance run against the agreed sample.

## Files

```
docs/plans/fee-statements/
├── README.md, plan.md, task-board.md, history.md, history-archive.md
├── resource-usage.md, questions.md, decisions.md, reference.md
├── tasks/  reports/  verification-records/
└── AGENTS.md
```

## Agreements

1. Task state lives on `task-board.md` only; `history.md` is appended to, never rewritten.
2. Questions go in `questions.md`; settled choices go in `decisions.md` as D-ids and are superseded, not edited.
3. Cite code as `path:line` and re-read it before relying on it.
4. Write only inside the brief's write scope. `tests/fixtures/expected-statements.txt` is the agreed sample (D-02); it changes only after a new decision records Harriet's agreement.
5. Execution follows the method's RUN card; it is not restated here.
6. History upkeep — `Log archive threshold: 90`. When a task closes, the earlier sessions' entries move verbatim to `history-archive.md`; the closing session's entry stays.

## Autonomy

**Autonomy level: L2 (assisted)** — Harriet Mwangi (society treasurer) gives the go for each run.

## Harness map

| Generic operation | Here | Notes |
|---|---|---|
| Read code | `cat`, `sed -n` | |
| Search | `grep -rn` | |
| Tests / acceptance | `sh checks/accept.sh` | runs the unit tests first |
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
