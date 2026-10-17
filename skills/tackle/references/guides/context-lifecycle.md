# Current work and original history

Use this extension only when measured history growth or a milestone boundary justifies it.
Direct and ordinary Focused work keep their normal artifact size. In new Coordinated work,
`task-board.md` owns current task state; the task brief/contract owns requirements,
`decisions.md` owns decisions, `questions.md` owns pending questions, and verification records
own observations. `history.md` and its original archives own history. `current-work.md` and
`handoff-brief.md` are disposable projections. The script reads only these current paths and
refuses an older workspace with `migrate first` ([forward only](migrate.md#forward-only)).

## Current work

Compile the current view from the active tasks, applicable decisions (including old ones),
unresolved blockers, failure identities and spent budgets, required dependency revisions, and
next authorized action. Keep the complete requirement/owner map discoverable in `plan.md`; a
digest need not list every closed task. The task brief remains self-contained. Do not make a
worker reconstruct its contract from summaries.

The checkpoint records semantic scope, exact required source membership and content revisions,
the archive index revision, and the last fully recorded event. Obtain required membership from
the current task brief and authoritative dependency map, never from the cache itself. Verify it
before reuse. A changed contract, reopened task, new blocker, input selection change, event, or
unfinished maintenance makes the affected projection stale. Rebuild from original sources,
starting with affected partitions and expanding when completeness is uncertain; do not summarize
earlier summaries as the only source. No checkpoint grants authorization or resets a failure budget.

The script hashes current authoritative files on each verification. Therefore a large
task board or decision file still costs bytes to verify. It avoids reading sealed unrelated
historical bodies; it does **not** claim constant total cost or cache trust without validation.
The projection in this conservative example contains exact source text rather than an unverified
summary. A coordinator can present a shorter digest after reading it. If active obligations
exceed a working-context target, load them or split the work; never truncate them.

## Maintenance and interruption

Record an initiative-scoped policy in the existing workspace instructions: authorized paths,
trigger (measured growth or milestone boundary), retained active sessions, segment target, and
recovery owner. The legacy 400-line warning is a prompt to assess cost, not permission to delete
history. RUN may refresh projections and perform reversible archival within that recorded policy.
STATUS is read-only; explicit handoff writes its projection/export only. Without a policy or an
explicit archive request, report the need without archiving. A new workspace's `AGENTS.md` carries
a default policy line (the trigger is history over the archive threshold at a RUN session boundary,
the newest five sessions stay active, and recovery follows this section); record a different policy
only to depart from it.

Archive **original bytes in chronological order**. `history/index.md` routes stable event numbers
and original headings to immutable segments; `history.md` retains its introduction and active tail.
Archives use `history-archive.md`. Original
heading references remain resolvable through the index/lookup. This is logical reference
resolution, not an automatic redirect in a Markdown browser. Before selected segmentation, check
live history-anchor consumers and retarget them to the segment/original heading, or retain the
legacy layout. Do not declare migration complete while a required live link is broken; keep
original historical text unchanged. Closed and unrelated workspaces are not migrated automatically.
Failed attempts and their failure identities survive archival. Retrieve the named original event
when diagnosing or transferring a failure; the current task/report retains its live spent budget.
Renaming, splitting, or reopening tasks cannot give that unresolved failure a fresh allowance.

All cooperating history/projection writers use one workspace lock. Sealed segments accept no
appends. A durable transaction records both expected revisions before index/tail replacement;
interruption leaves detectable pending maintenance. Recovery verifies the segment and exact
before/after revisions, then completes the same transaction once. An unexpected concurrent edit
blocks recovery without overwriting it. Copying/archiving is not retirement; retention and deletion
follow [record-lifecycle.md](record-lifecycle.md) and their separate authorization.

For interrupted completion, compare actual output, check records, report, task board, and last
fully recorded event. A stale projection cannot flip a task Complete. Preserve an observed effect
and complete missing bookkeeping when its checks support it; do not rerun a completed side effect
just because its final event is missing. Missing checks leave Checking/Interrupted or Unverifiable
as appropriate. Finish maintenance already required by the run before deliverable acceptance;
do not start another bookkeeping/check cycle after acceptance.

## Portable handoff

A handoff contains verified current source context, scope/revisions, authorization boundaries,
failure lineage/budgets, next authorized action, and original historical events actually needed.
Export required check records, including transitively retained prior records and their content objects,
through an equivalent harness export or, with the owner's explicit authorization, the record lifecycle script. Local paths alone are insufficient. Verify every exported
inventory after copying and again at the recipient. A context inventory proves its copied bytes,
not check success or semantic completeness; validate required check records with their own reader.
An explicit audit may load full history. Routine handoff does not do so without a named reason.

## Optional local script

This is a Python standard-library module, [`scripts/context_bundle.py`](../../scripts/context_bundle.py), not an
installed executable or new workflow engine; it has no command line. Prefer an equivalent harness
capability. With the owner's explicit authorization, put `<skill>/scripts/` first on `sys.path`, import
`context_bundle` and instantiate `Context(workspace)`.
`project(scope, sources)` is an authorized RUN write; `current(scope, sources)`, `history()`,
`event(number)`, and `lookup(original_heading)` are reads. `append_event(data, expected_event,
expected_revision)` appends one event under authorized RUN and detects an already-completed
identical append without repeating it. It atomically rewrites the bounded active tail, and that
rewrite cost is included in the measurements; a process crash cannot publish half an event. `archive()` and `recover()` require the
recorded maintenance authorization. `export()` requires handoff/export intent and a fresh destination.
For record bundles, first call the record script’s `export_records`, then pass the checked
directories as `record_bundles={"evidence": exported_directory}`. They are copied under the named
relative prefix and included in the context inventory; validate them with `verify_bundle` after
export as well. Context hashing alone never promotes a failed check.
The scope is an English-keyed object such as `tasks`, `requirements`, `milestone`; sources are exact
workspace-relative authoritative paths, including task briefs and required dependency outputs.
Do not list projections as their own inputs. This POSIX example needs advisory file locking; if
unavailable, use an equivalent observed lock capability or report the script unavailable.

`segment_bytes` is a tuning parameter, not a context limit. The synthetic benchmark uses 64 KiB
segments and five active sessions, measures its setup/rebuild/export costs, and makes no claim
that this target suits every initiative. A single large original event remains intact; import or run
the script only with the owner's explicit authorization for this use ([script consent](../../scripts/README.md#consent)).

The script does not validate user intent, semantic source selection, check acceptance, or all
milestone coverage. Those remain the existing PLAN/RUN obligations. Missing/corrupt selected
history fails lookup; an unrelated segment is not rehashed on every resume. Immutable storage is
a cooperation rule plus verified content addressing, not a defense against a hostile filesystem.
Measure logical content bytes read/written separately from metadata calls, retained bytes, and
unobserved filesystem journal/cache costs. Include initial indexing, every archive/recovery,
projection rebuilding, and export verification when comparing complete costs.
