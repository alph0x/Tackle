# Current work — {{TITLE}}

**Generated projection, never canonical.** Refresh only within authorized RUN or explicit handoff.
The task board `board.md` owns current state; `log.md` and original archives own history; task
briefs/contracts, decisions, questions, and verification records keep their own authority.
Follow `references/guides/run.md`; use `guides/context-lifecycle.md` only when its size/risk trigger
applies. Do not put secrets or unobserved outcomes here.

<a id="current-point--wave"></a>
## Checkpoint and scope

- Active task / milestone: {{P-0N — title; optional milestone}}
- Wave: {{parallel set or none}} · Team: {{Solo | Pair | Pod | Squad}}
- Run state: {{preflight | implementing | validating | integrating | accepting | complete | blocked}}
- Semantic scope: {{requirements/tasks/dependencies represented, and why complete for the next action}}
- Authoritative state revision: {{content hash or revision, with exact source membership}}
- Relevant inputs: {{source path, revision/hash, consumer; include applicable decisions and blockers}}
- Last fully recorded event: {{stable event reference and hash; archive index revision if segmented}}
- Verification status: {{current after source comparison | stale | incomplete}}

A copied revision label is not a validity check. Before reuse, compare authoritative source
membership/content and history head with this checkpoint. Changed contracts, reopened tasks, new
blockers, changed input selection, and interrupted updates invalidate affected content. Rebuild
from original sources; read additional partitions when required context is uncertain.

## Active capabilities

| Capability | Actor | Binding / isolation |
|---|---|---|
| Implementation | {{agent id}} | {{tier/model/effort or n/a}} |
| Mechanical observation | {{agent id}} | {{context and runtime}} |
| Semantic review (if required) | {{agent id or human}} | {{observed independence or unavailable}} |

<a id="open-findings-and-budgets"></a>
## Decisions, findings, and budgets

- Applicable decisions/constraints: {{stable references and operative clauses, regardless of age}}
- Blockers/pending decisions: {{owner, effect, and source; informational questions remain distinct}}
- Findings: {{failure identity, owner, cause, severity, and raw-record pointer; or none}}
- Task correction cycles: {{spent}} / 3; identical no-progress observations: {{count}}
- Initiative unowned-integration cycles: {{spent}} / 2
- Failure lineage: {{renamed/split/merged predecessors and original attempt references, including archives}}

<a id="recent-closures--next-ready"></a>
## Recent closures and next authorized work

- {{P-0N: Complete | Blocked | Skipped | Unverifiable | Interrupted — report/raw-record pointer}}
- {{next Ready task; consumed outputs and readiness revisions satisfied}}
- {{next action within recorded authorization; Draft milestone work remains unready}}
- Requirement/owner map: {{plan.md section; retain complete discoverable scope}}

The projection cannot authorize a retry, state change, replan, model upgrade, or initiative close.
Keep raw records and necessary original source context portable when producing a handoff.
