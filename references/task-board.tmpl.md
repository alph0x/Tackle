# Task board — {{TITLE}}

Schema: tackle-workspace/4

**Canonical current task state.** `task-board.md` owns task status; the plan owns requirements and
coverage; history records original events. The authorized coordinator updates this board. STATUS,
Next and plain Resume inspect only. Read legacy boards through [terminology.md](terminology.md).

States: Draft, Ready to run, In progress, Checking, Complete, Blocked, Interrupted, Skipped,
Unverifiable. The Status cell contains exactly one state token, without a reason suffix;
put blocker detail in Verification and `questions.md`. Only current readiness supports Ready to run. Complete requires task, related
regression, affected integration and mandatory review results. Initiative completion additionally
requires deliverable acceptance. Skipped needs an authorized reason; unavailable required checks
stay Unverifiable. Interrupted work must be reconciled before repeating an effect.

Verification references the task report, which records method, result, actual actor/independence,
input revisions and accessible raw records. A label is not a passing record. E0–E3 remain readable
on legacy boards; never turn them into an ordinal quality scale or infer an independent reviewer.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
<!-- Add stable T-id rows from plan.md §5. Terminal checked/blocked rows reference reports/T-0N-report.md.
     Dependency graph remains in the plan; do not copy it here. -->

<a id="dependency-graph"></a>
The dependency graph remains in `plan.md` §5; this board records its task dependencies without duplicating the graph.
