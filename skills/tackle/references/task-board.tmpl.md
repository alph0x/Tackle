# Task board — {{TITLE}}

Schema: tackle-workspace/5

**Canonical current task state.** `task-board.md` owns task status; the plan owns requirements and
coverage; history records original events. The authorized coordinator updates this board. STATUS,
Next and plain Resume inspect only. An older board is migrated before it runs
([forward only](guides/migrate.md#forward-only)).

States: Draft, Ready to run, In progress, Checking, Complete, Blocked, Interrupted, Skipped,
Unverifiable, Waiting on owner. The Status cell contains exactly one state token, without a reason suffix;
put blocker detail in Verification and `questions.md`. Only current readiness supports Ready to run,
cited in Verification as `ready: <reference>`. Complete requires task, related
regression, affected integration and mandatory review results. Initiative completion additionally
requires deliverable acceptance. Skipped needs an authorized reason; unavailable required checks
stay Unverifiable. Interrupted work must be reconciled before repeating an effect. Waiting on owner
names the awaited action in Verification as `waiting: <reference>` and differs from Blocked.

Verification references the task report, which records method, result, actual actor/independence,
input revisions and accessible raw records. A label is not a passing record; never infer an
independent reviewer from it.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
<!-- Add stable T-id rows from plan.md §5. Terminal checked/blocked rows reference reports/T-0N-report.md.
     Dependency graph remains in the plan; do not copy it here. -->

<a id="dependency-graph"></a>
The dependency graph remains in `plan.md` §5; this board records its task dependencies without duplicating the graph.

<a id="obligations"></a>
## Obligations

An obligation that outlives its task, or belongs to the initiative with no task, is recorded here when it is created. The first cell is its stable `O-NN` id (two digits). State is `Open`, `Discharged` or `Withdrawn`; a `Discharged` or `Withdrawn` row cites a Reference: a decision id, a report path or a record path. Name every `Open` id in the `Active obligations` line of the newest State snapshot in `history.md`, and in the `**Remains**:` receipt of the report that leaves it open. Initiative completion requires that no obligation is `Open`, unless the owner withdrew it.

| Obligation | What | Owner | Trigger | State | Discharge check | Reference |
|---|---|---|---|---|---|---|
<!-- Add O-NN rows only when an obligation outlives its task. No column is named Status, so the task readers skip these rows. -->

