<a id="status--read-only-queries-and-handoff-projection"></a>
# STATUS — read-only queries and handoff

STATUS answers the requested question about an initiative: status, available plans, the next
Ready task, or a cold-session resume. It never executes a task or edits source, task board,
history, decisions, questions, verification records, or readiness.

Only an explicit handoff request may write `handoff-brief.md` and its requested portable export. This
projection changes no canonical state. STATUS never archives history or appends a status event.
A status question during an already authorized RUN answers the question without cancelling that
RUN; a standalone status/resume request does not authorize execution.

## Queries

- **Status** reads the relevant canonical task board, applicable decisions, open questions, and
  latest history checkpoint, or a verified current-work projection backed by those sources.
  Answer the question first. Include stale reference verification, failed checks, blockers, or
  missing records when they affect that answer; observations grant no mutation permission. List
  any `Waiting on owner` row with its owner action (`waiting: <Q-id or prerequisite>`); RUN itself
  skips those rows when picking the next task. List every `Open` obligation (`O-NN`) with its owner
  and trigger.
- **List** scans available workspaces and gives one line per plan.
- **Next** selects a Ready task and provides its purpose, dependencies, write scope, and starting
  prompt. Selection is not execution. Draft tasks cannot be selected as Ready. When no task is
  Ready, Next reports the open obligations (id, owner, trigger) rather than nothing.
- **Resume** reads workspace instructions, verified current work, the relevant task brief and
  named inputs/depth artifacts. Report current state, reusable verification records, relevant
  changes, and the next authorized action. Ask only when a user-owned decision actually blocks
  affected work. Plain resume remains STATUS.

Write a digest the reader can take in at a glance: lead with what changes their next action (a
blocker, a failure, an owner decision, the next authorized task), and never omit a material
failure or constraint. Digest text follows [controlled writing](controlled-writing.md).
When requested or relevant, report reference age, checks actually run, task/blocker counts,
weakest required verification, resource coverage, and history size. Missing telemetry is `n/a`.
Report a workspace's migration bucket from its board's `Schema:` line, per
[migrate.md](migrate.md#schema-keyed-migration)'s table; a bucket other than `5`, or a Focused plan on
older paths, reads `migrate first`, with its next step. STATUS never migrates automatically. All
tasks Complete is insufficient to claim deliverable acceptance.

<a id="handoff-projection"></a>
## Handoff brief projection

On a workspace that reads `migrate first`, the handoff writes nothing and reports that refusal.
Verify current work using [context-lifecycle.md](context-lifecycle.md#current-work): scope, required
source membership/revisions, state revision, and last fully recorded event. Reuse it with the
necessary source records; do not unconditionally read complete closed history. If stale or
incomplete, reconstruct affected context from authoritative sources and expand when completeness
is uncertain.
An explicitly requested audit may require complete history.

The portable handoff contains context; current task state and checkpoint; applicable decisions,
blockers, unresolved questions, and failure budgets; verified dependency/check references; and up
to three next authorized actions with prompts and reading order. Carry all still-binding
constraints even if their original decision is old. Include the source context and retained check
objects the recipient needs, following [portable export](context-lifecycle.md#portable-handoff).
Keep stable IDs when their meanings and referenced objects travel with them; local links alone do
not make context portable. Regeneration may replace the projection, never its authoritative sources.

<a id="archive-explicit-request-only"></a>
## Archive

Archive only under an explicit user request or an initiative-scoped maintenance policy already
covered by authorized RUN. The policy names paths, observable triggers, retained active sessions,
and recovery. A new workspace's `AGENTS.md` carries that policy as a default line, so RUN may
archive without a separate request. STATUS may recommend maintenance but never performs it.

Preserve closed entries verbatim, ascending, including failed attempts. The ordinary legacy path
keeps the newest five sessions in `history.md` and older entries in `history-archive.md`; do not silently
rewrite existing archives. When a single archive becomes unwieldy, use the indexed immutable
segments and recoverable rotation in [context-lifecycle.md](context-lifecycle.md#maintenance-and-interruption).
Keep the newest State snapshot, stable event references/original-heading lookup, and one bounded
maintenance record with before/after sizes and the committed checkpoint. Never replace originals
with a paraphrase. Archive placement does not authorize evidence retirement.

## Older workspaces

STATUS reads only the current layout and reports any older workspace as `migrate first`
([forward only](migrate.md#forward-only)). The retired 8.x action-name
aliases that used to reach STATUS keep their historical targets in
[terminology.md](../terminology.md)'s Routes and actions section.
