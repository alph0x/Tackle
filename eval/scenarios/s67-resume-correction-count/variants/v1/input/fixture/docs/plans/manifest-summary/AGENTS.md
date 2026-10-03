# AGENTS — workspace `docs/plans/manifest-summary/`

**Methodology: Tackle 9.0.1**

Working agreements for whoever picks this initiative up, person or agent, in any tool.

## Before you start

If `.tackle/profile.md` or `~/.tackle/user-profile.md` exists, skim the active hypotheses first and mark
proposals they shape. Neither exists for depot-tools today.

## What this is

One new subcommand, `python3 -m manifest summarize <export.csv>`, printing a single summary line that the
shift leads' nightly digest quotes.

## Files

```
docs/plans/manifest-summary/
├── README.md, plan.md, task-board.md, history.md, history-archive.md
├── resource-usage.md, questions.md, decisions.md, reference.md
├── tasks/                 one brief per task
├── reports/               task reports, closed or in progress
├── verification-records/  raw check captures, never edited
└── AGENTS.md
```

## House rules

1. A task's state lives in `task-board.md` and nowhere else; `history.md` is appended to, never rewritten.
2. Questions go to `questions.md`; settled choices to `decisions.md` as D-ids, superseded by a newer D-id
   rather than edited.
3. Cite code as `path:line` and look at the line again before relying on it.
4. Write only inside the write scope the brief declares. `tests/` and `checks/acceptance.sh` are protected
   for every task of this initiative; touching them needs a recorded decision first.
5. Execution follows the method's RUN card; this file does not restate it.
6. History maintenance — `Log archive threshold: 80`. When a task closes, the entries of the earlier sessions
   move verbatim to `history-archive.md` and the closing session's entry stays here; moved entries are never
   edited and keep their headings.

## Autonomy

**Autonomy level: L2 (assisted)** — nothing under `manifest/` changes without an explicit go from the
owner, Imogen Hartley.

## Harness map

| Generic operation | Here | Notes |
|---|---|---|
| Read code | `cat`, `sed -n` | |
| Search | `grep -rn` | |
| Tests / acceptance | `sh checks/acceptance.sh` | runs the unit tests first |
| Lint / typecheck | none configured | |
| Parallel agents | not used | |
| Git | `git` | `docs/plans/` is gitignored (D-01) |
| Agent messaging | report in the session | `agent-messaging: unsupported` |
| Resource usage reporting | nothing exposed | `unsupported`; unknown values stay `n/a` |

## Model map

| Tier | Model available here | Status and source |
|---|---|---|
| `fast` | n/a | unknown; the host lists no models |
| `standard` | the session's own model | supported; session banner |
| `frontier` | n/a | unknown |

**model-binding: unknown · effort-binding: unknown · telemetry: tokens=n/a; USD=n/a**
