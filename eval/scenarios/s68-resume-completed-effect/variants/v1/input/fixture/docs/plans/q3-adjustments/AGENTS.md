# AGENTS — workspace `docs/plans/q3-adjustments/`

**Methodology: Tackle 9.0.1**

Agreements for anyone working this initiative, in any tool.

## Session start

Read `.tackle/profile.md` and `~/.tackle/user-profile.md` when present and mark proposals they shape. The
books repository has neither.

## In one line

Reconcile Q3, compute and approve the true-up for ACC-1042, post it, write the quarter close report.

## Files

```
docs/plans/q3-adjustments/
├── README.md, plan.md, task-board.md, history.md, history-archive.md
├── resource-usage.md, questions.md, decisions.md, reference.md
├── tasks/  reports/  verification-records/
└── AGENTS.md
```

## Agreements

1. Task state: `task-board.md` only. `history.md`: append, never rewrite.
2. Questions in `questions.md`; settled choices in `decisions.md` as D-ids, superseded rather than edited.
3. Cite code and data as `path:line`, re-read before relying on it.
4. Write only the brief's write scope. `data/adjustments.csv` is written by `tools/post_adjustment.py` and by nothing else (D-02); hand edits are out.
5. Execution: the method's RUN card, not restated here.
6. History upkeep — `Log archive threshold: 90`. At a task close, entries older than the two newest sessions move verbatim to `history-archive.md`.

## Autonomy

**Autonomy level: L2 (assisted)** — the treasurer, Rhiannon Vale, gives the go before any posting.

## Harness map

| Generic operation | Here | Notes |
|---|---|---|
| Read code | `cat`, `sed -n` | |
| Search | `grep -rn` | |
| Checks | `python3 tools/check_adjustment.py <account> <memo>` | |
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
