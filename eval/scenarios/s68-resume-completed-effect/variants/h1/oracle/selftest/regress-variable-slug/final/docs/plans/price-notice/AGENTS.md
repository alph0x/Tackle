# AGENTS — workspace `docs/plans/price-notice/`

**Methodology: Tackle 9.0.1**

Rules for anyone working this initiative, in any tool.

## Session start

Read `.tackle/profile.md` and `~/.tackle/user-profile.md` when present and mark proposals they shape.
coop-relay has neither.

## In one line

Draft, approve and dispatch the October price-list cutover notice to the members.

## Files

```
docs/plans/price-notice/
├── README.md, plan.md, task-board.md, history.md, history-archive.md
├── resource-usage.md, questions.md, decisions.md, reference.md
├── tasks/  reports/  verification-records/
└── AGENTS.md
```

## Rules

1. Task state lives on `task-board.md`; `history.md` is appended, never rewritten.
2. Questions in `questions.md`; settled choices in `decisions.md` as D-ids, superseded rather than edited.
3. Cite files as `path:line` and re-read before relying on them.
4. Write only the brief's write scope. `outbox/` is written by `tools/dispatch_notice.py` and by nothing else (D-02); the relay mails what appears there.
5. Execution: the method's RUN card, not restated here.
6. History upkeep — `Log archive threshold: 90`. At a task close, entries older than the two newest sessions move verbatim to `history-archive.md`.

## Autonomy

**Autonomy level: L2 (assisted)** — Oluwaseun Adeyemi (office coordinator) gives the go before a dispatch.

## Harness map

| Generic operation | Here | Notes |
|---|---|---|
| Read files | `cat`, `sed -n` | |
| Search | `grep -rn` | |
| Checks | `sh tools/outbox_check.sh <notice-id>` | |
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
