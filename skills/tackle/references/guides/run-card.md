# RUN card

RUN starts only after explicit execution intent, including a scoped PLAN+RUN request.

1. **Read.** Read `task-board.md` and record its sha256; stop with `migrate first` before any write unless it
   declares `Schema: tackle-workspace/5` ([forward only](migrate.md#forward-only)).
2. **Pick.** A named task takes the fast path. Otherwise, take the first `Ready to run` row in board order whose
   dependencies are Complete and write scope intersects no In progress, Checking, Interrupted or `Waiting on owner`
   row. With none, report what is waiting, on whom, and stop.
3. **Claim.** Before work, re-read the board; reconcile a changed hash and never overwrite. Set the row to In
   progress, append the start row with the Run ID. A row already claimed by another run is skipped, never retried.
4. **Preflight.** Check the pinned procedure, which never changes silently; the brief, decision and
   contract revisions; the dependency outputs; the environment; the write scope; and a compiled Tier's
   [model-map binding](run.md#tier-dispatch-and-escalation-limits). Also check the row's `ready:`
   citation. A stale input goes back to
   Draft or to Blocked.
5. **Intent, then work.** Write the INTENT line before any mutation, then work only inside the write
   scope. Protected expectations change only by a prior superseding decision; protected test files
   stay byte-identical, so add coverage in a new file.
6. **Check.** Run the checks PLAN selected (`testing.md`): the task check and related regression
   checks, then, after merge, the affected integration checks on the merged tree, with raw records.
   Every required assertion propagates failure. Validators take expected values and
   valid equivalents from the contract, never the candidate's output, and never modify real outputs or
   inputs.
7. **Correct within budget.**
   - Classify each failure: implementation; missing or ambiguous requirement; incomplete output;
     required edge case; dependency or integration; contradictory spec; validator; environment;
     capability; or undetermined. An implementation fault is corrected; a capability failure
     declared in the brief is corrected only once, one tier up ([limits](run.md#tier-dispatch-and-escalation-limits)).
   - **Task pool.** At most three failed correction-validation cycles per task, in one pool shared
     across the executor, reviewer, checker, interruptions, resumptions and sessions. The first
     validation of an implementation fault is not a cycle, and a successful correction resets no counter.
   - **Unowned integration.** One pool of two cycles per initiative, shared by all unowned integration
     faults.
   - **No progress.** Two identical no-progress observations stop the task immediately, even with
     fewer than three cycles spent. Identical means the same signature: command, failure class, failing
     assertion and normalized output, with timestamps, paths and durations removed.
   - **Other causes** produce an escalation packet. The task becomes Blocked, or `Waiting on owner` when
     the owner must act.
8. **Close.** A [reviewer's verdict](run.md#adversary-checkpoints) is its own artifact; the coordinator decides. The report ends with
   a receipt: what is complete, what remains (the `**Remains**:` line), and who owns the next step. Update the board with
   hash-before-write, then append one history line and the usage row. Loop. When no task remains,
   deliverable acceptance precedes initiative completion.
   Before declaring the initiative closed, open every Complete task's brief and report, each record a report
   cites, and the history, and read them as prose: an owner request or follow-up not yet done becomes an `Open`
   obligation raised with the owner. A missing `O-NN` row or `**Remains**:` line never means nothing remains.

## State transitions

Entry state: the state held before. A blank budget cell spends nothing; no transition resets spent
cycles.

| From | To | Trigger | Budget effect |
|---|---|---|---|
| Draft | Ready to run | Current readiness passes | |
| Ready to run | In progress | Claimed | |
| In progress | Checking | Checks start | |
| Checking | In progress | Implementation fault | One cycle; none for the first validation |
| Checking | In progress | Declared capability escalation (once per task) | One cycle, always |
| Checking | Complete | Every mandatory task obligation passed | |
| Ready to run, In progress | Draft | Stale input | |
| In progress, Checking | Blocked | Spent pool, no progress, failed dependency or another stop | |
| In progress, Checking | Interrupted | Stopped before a terminal record | |
| Interrupted | Entry state | `observe-incomplete` reconciled before any effect repeats | |
| Checking | Unverifiable | Required check cannot run | None; affected work blocked |
| Unverifiable | Checking | Capability available | |
| Blocked | Draft, In progress | Recorded decision or fix removes the cause; Draft if the brief changed | |
| Draft, Ready to run, In progress, Checking | Waiting on owner | Needs the owner's product decision, authorization, spending approval, credential or prerequisite the agent may not provide | None; an unchanged wait is no new no-progress observation |
| Waiting on owner | Entry state | Owner acts | |
| Draft, Ready to run, Blocked, Unverifiable, Waiting on owner | Skipped | Owner withdraws the work; never a completion | |
| Skipped | Draft | Owner reinstates the work | |
| Complete | In progress | Authorized reopening | Keeps spent cycles |


## Depth (on demand)

[Record fields](run.md#verification-record-fields), [capture](run.md#capture),
[failure packet](run.md#failure-classification-and-escalation-packet), [recovery](run.md#operational-recovery),
[lineage](run.md#correction-lineage) and its [recipe](../recipes/correction-lineage.md),
[independence](run.md#independence-and-historical-grades),
[acceptance](run.md#integration-and-deliverable-acceptance), [release gating](run.md#release-gating),
[run record](run.md#run-record), [testing](testing.md), [limits](run.md#tier-dispatch-and-escalation-limits),
[waiting-on-owner citation](status.md#queries), [resume](status.md#cold-resume-read-order).
