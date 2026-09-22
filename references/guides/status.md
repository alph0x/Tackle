<a id="status--read-only-queries-and-handoff-projection"></a>
# STATUS — read-only queries and handoff

STATUS answers the requested question about an initiative: status, available plans, the next
Ready task, or a cold-session resume. It never executes a task or edits source, task board,
history, decisions, questions, verification records, or readiness.

Only an explicit handoff request may write `HANDOFF.md` and its requested portable export. This
projection changes no canonical state. STATUS never archives history or appends a status event.
A status question during an already authorized RUN answers the question without cancelling that
RUN; a standalone status/resume request does not authorize execution.

## Queries

- **Status** reads the relevant canonical task board, applicable decisions, open questions, and
  latest history checkpoint, or a verified current-work projection backed by those sources.
  Answer the question first. Include stale reference verification, failed checks, blockers, or
  missing records when they affect that answer; observations grant no mutation permission.
- **List** scans available workspaces and gives one line per plan.
- **Next** selects a Ready task and provides its purpose, dependencies, write scope, and starting
  prompt. Selection is not execution. Draft tasks cannot be selected as Ready.
- **Resume** reads workspace instructions, verified current work, the relevant task brief and
  named inputs/depth artifacts. Report current state, reusable verification records, relevant
  changes, and the next authorized action. Ask only when a user-owned decision actually blocks
  affected work. Plain resume remains STATUS.

Use a concise digest, usually within 12 lines, without omitting a material failure or constraint.
Do not print every lint result, historical grade, collision, or archive threshold on every query.
When requested or relevant, report reference age, checks actually run, task/blocker counts,
weakest required verification, resource coverage, and history size. Missing telemetry is `n/a`.
An older methodology stamp may warrant a selected migration proposal under `migrate.md`; STATUS
never migrates automatically. All tasks Complete is insufficient to claim deliverable acceptance.

## Handoff projection

Verify current work using [context-lifecycle.md](context-lifecycle.md#current-work): scope, required
source membership/revisions, state revision, and last fully recorded event. Reuse it with the
necessary source records; do not unconditionally read complete closed history. If stale or
incomplete, reconstruct affected context from authoritative sources and expand when completeness
is uncertain. Legacy workspaces without a verified projection use their original source records.
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
and recovery. STATUS may recommend maintenance but never performs it.

Preserve closed entries verbatim, ascending, including failed attempts. The ordinary legacy path
keeps the newest five sessions in `log.md` and older entries in `log-archive.md`; do not silently
rewrite existing archives. When a single archive becomes unwieldy, use the indexed immutable
segments and recoverable rotation in [context-lifecycle.md](context-lifecycle.md#maintenance-and-interruption).
Keep the newest State snapshot, stable event references/original-heading lookup, and one bounded
maintenance record with before/after sizes and the committed checkpoint. Never replace originals
with a paraphrase. Archive placement does not authorize evidence retirement.

## Compatibility

During 8.x, `pulse`, `list`, `next`, `resume` and `handoff` forward here while preserving read or
explicit projection intent. Legacy Point/board/log names and `P-xx` references remain readable.
The aliases retire in 9.0; this forwarding text remains for interpreting old requests safely.
