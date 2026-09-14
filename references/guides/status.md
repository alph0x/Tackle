# STATUS — read-only queries and handoff projection

STATUS is the read-only query surface for an initiative. `/tackle-status` may report status, list
plans, select the next ready Point, or resume with a cold-session digest. It never edits source,
board, log, questions, decisions, evidence, or a Point, and it never executes or fixes work.

`--handoff` is the sole exception: only an explicit request for a handoff may write the portable
`HANDOFF.md` projection. It does not change canonical state. A status invocation never appends a
status log row, archives history, or changes readiness. Archiving remains an explicit user action
under the archive protocol below.

## Queries

- **Status** reads the canonical `board.md`, active `questions.md`, `decisions.md`, and newest log
  State snapshot. Report stale grounding, lint and regression results when their documented checks
  are run; observations do not authorize a mutation.
- **List** scans available workspaces and gives one line per plan.
- **Next** selects the next ready Point and prints its pre-attack summary and starting prompt. It
  is selection only; execution requires explicit RUN intent.
- **Resume** reads a workspace cold: `AGENTS.md`, newest log entry, `decisions.md`, open
  `questions.md`, the relevant Point and named depth artifacts. It reports the state and asks only
  user-owned questions. Plain resume is a STATUS query; it is not RUN.

The query digest has at most 12 lines: stale citations and grounding age, lint score, regression
sweep, cross-initiative collisions, blocked Points and evidence packets, next ready Point, the
weakest-link evidence line, optional usage coverage, and log size versus its archive threshold.
Missing telemetry is `n/a`. A Methodology stamp older than the current release yields a migration
offer pointing to `migrate.md`; it does not migrate the workspace.

## Handoff projection

On an explicit `--handoff` request, read the complete current board, log, decisions and questions
before generating `HANDOFF.md`. The projection contains, in order: context, the newest State
snapshot with board counts, decisions, open questions, up to three next actions with prompts, and
portable reading order. Carry state inline: do not expose local plan paths, ids or references that
the receiving session cannot access. Regeneration may replace this projection because canonical
state remains in board and log.

## Archive (explicit request only)

When the user explicitly requests archival, move entries older than the newest five sessions
verbatim from `log.md` to `log-archive.md` in ascending order. Preserve every byte, confirm the
newest log entry retains its State snapshot, and append one bounded archive record with line counts
before and after. A status digest may recommend this when the configured threshold is exceeded;
the recommendation itself never writes.

## Compatibility

During 8.x, `pulse`, `list`, `next`, `resume` and `handoff` forward here while preserving their
read or explicitly requested projection intent. The aliases retire in 9.0; this forwarding text is
retained so an old request can be interpreted safely during migration.
