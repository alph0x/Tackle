# Plan lint spec — mechanical checks

This table specifies the 17 mechanical checks; [`scripts/lint.py`](../../scripts/lint.py) holds each row's program and runs it with `sh -c` from the **repo root**: `python3 -I <skill>/scripts/lint.py [--row N] <slug>`, where `<slug>` is the initiative directory name (workspace = `docs/plans/<slug>/`). Running it falls under [script consent](../../scripts/README.md#consent). Every row reads only the current workspace layout; an older one is refused with `migrate first` ([forward only](migrate.md#forward-only)).

For Full without equivalent harness automation, use the connected extraction/capture script in
[full-checks.md](full-checks.md#execute-canonical-lint-faithfully). It compares actual saved script
bytes before interpreting a row; a successful altered command cannot count as canonical PASS.

- Pass conditions are mechanical — an output count or an exit code, no judgment. Any output line is a finding to report verbatim.
- Row 1 skips content inside fenced code blocks — done-signals legitimately grep for literal `{{…}}` placeholder patterns there.
- Row 2 reads `tasks/` with T ids and requires `plan.md` §5. It rejects mixed identities, missing briefs and unresolved dependencies, and an older artifact beside the board fails as mixed workspace paths. Row 2 also resolves a dependency written T-NN [sibling] and a brief under a declared sibling's tasks/ against the siblings declared in AGENTS.md.
- Row 4 resolves citation paths from the repo root first, then retries with the `docs/plans/<slug>/` prefix. A citation pinned to a revision (`path@<rev>:NN — "fragment"`) records grounding at that revision and is not re-checked: pin only a citation whose target the Task itself changes, and verify it with `git show <rev>:path`.
- Row 8 reads activity only from the trimmed Status field. Write scope may be inline (plain or backtick-quoted, comma-separated) or a multiline bullet list headed by `**Write scope**`; annotations after quoted paths are ignored. Empty or unsupported declarations, globs, parent traversal and any existing symlink component (including dangling links, read from one `find . -type l` listing) report unresolved scope, never a clean comparison. Ordinary future paths are compared lexically without requiring existence.
- Row 9 reads `**Type**` on its field line and counts `Rounds`, `Metric` and `Threshold` only as declarations outside fenced code: a bold field (`**Rounds**: 3` or `**Rounds:** 3`, also inline after the Type) or a line that starts with `Rounds: 3` — backtick-quoted prose mentions neither trigger nor satisfy it.
- Row 11 refuses a board below `/5` first, like the other board rows; on a `/5` board without `resource-usage.md` it skips, because rows 2 and 16 report the missing ledger. On workspaces that carry the ledger, row 11 flags a completed task missing its usage row — a ledger defect (fix the ledger, not the row).
- Row 12 skips a brief only when a Complete, Skipped or Unverifiable row names it in the Brief column and the brief's heading names that row's task, and no open row names it; it scans the other `tasks/*.md` briefs for `**Effort**:` lines with any bullet marker (`-`, `*`, `+`): a brief carries a resolved `low`/`medium`/`high`/`max`; any other value is red. A brief whose `**Effort**:` departs from the compiled default (`low`) outside any fenced block, with neither a non-fenced `**Tier**:` nor `**Tier reason**:`, additionally reports `<file>: Effort without Tier reason`.
- Row 13 measures two things in `history.md`: the whole file against the archive threshold, and each session entry against the entry budget. An entry runs from its `## YYYY-MM-DD` heading line through the line before the next `## ` heading or the end of the file; `###` lines are inside it and trailing blank lines are left out. A finding names the file, the entry's heading line and both numbers. RUN archives or shortens under the workspace policy; STATUS never archives.
- Rows 3, 8, 10, 11, 12 and 14 read Status through one shared extractor: the column whose header cell is exactly `Status` in the row just above a delimiter row, or the fifth data column when no header names it. Row 10 reads `Verification` by name.
- Row 14 checks every Complete row, not the first; rows 11 and 14 emit every matching id through the shared Status extractor. Workspaces that are neither active nor selected fail row 14 as sweep WARN, non-gating; active or selected workspaces gate — a missing closure report blocks execution until written or explicitly waived, even for an all-complete selected board.
- Row 15's date→epoch conversion feature-detects GNU vs BSD `date` exactly as `probe()` does; both flavors cover macOS and Linux hosts.
- Row 17 reads O-ids only from `**Remains**:` receipt lines (exactly `none`, or `O-NN` ids separated by commas, one per line) and from the newest State snapshot's `Active obligations` line: the first such line under the last `### State snapshot` heading. Reports and `history.md` are read outside code fences, so a fenced example there, prose, an older snapshot and a non-task report never count; the board is read the way rows 2 and 3 read it, fenced rows included. An obligation is any row of a board table headed `Obligation`, and any other board table row whose first cell starts with `O-` or `o-` once leading markup (`*`, `_`, `~`, backticks, brackets, parentheses, `<`, `>`, `#`, `-`, `+`) is removed: that cell must be exactly `O-NN`, so `**O-01**`, `o-01`, `[O-01](#o-01)` and a backticked id are reported as malformed and the row is not registered; `State` and `Reference` are found by header name in the row's own table, and no column is named `Status`, so rows 3, 8, 10, 11, 12 and 14 never read an obligation as a task.
- Row 6 covers `history-archive.md`; the archive's newest entry must not be younger than the active history's oldest.
- Judgment-only checks (contract churn, quality dimensions, Q-guard…) stay in `decompose-and-lint.md` Step 6.5 — this table holds only what a command can decide.

Lifecycle validity semantics include duplicate starts, duplicate terminals, orphan terminal without start, mismatched Task/Role, and negative counts as invalid; an interrupted run with one `observe-incomplete` terminal is valid. The exact eight-column legacy `Point` table remains readable before v2 adoption; it is not parsed as lifecycle events. New lifecycle headers say `Task`; historical `Point` headers remain readable. `n/a` counts remain unknown and valid, as specified by `usage-observability.md`; empty, negative and nonnumeric counts still fail. A legacy header after v2 cannot hide invalid events.
| Check | Pass condition |
|---|---|
| 1 · Lite shape and unfilled placeholders — no `{{…}}` left outside fenced code blocks in shipped workspace files, `legacy-*/` snapshots skipped; a Focused workspace still on `log.md`, `log-archive.md` or `usage.md` is refused | 0 lines of output |
| 2 · Task identity and dependencies — every T id, brief path and dependency resolves in the `/5` workspace; mixed identities, absent briefs and an older layout fail | 0 lines of output |
| 3 · Invalid status vocabulary — the `Status` field in `task-board.md` uses the ten `/5` states, the nine English states and `Waiting on owner` (the field is found by its `Status` header, the fifth data column when no header names it; an emoji in another column does not count); an older board is refused | 0 lines of output |
| 4 · Malformed/stale citations — every anchored citation, including every citation of a line, passes the anchored-citation drift check; an opened citation without a non-empty, closed quoted fragment is malformed (fragment still on line NN; fix path: the two-phase re-anchor flow in `verify.md` step 0) | 0 lines of output (0 stale) |
| 5 · Status duplicated outside `task-board.md` — a `Status:` declaration, or a status emoji (incl. ⚪), in `plan.md` or `tasks/`; an older board is refused | 0 lines of output (grep exits 1) |
| 6 · History entries out of chronological order — `## YYYY-MM-DD` headings ascending (append-only); covers `history-archive.md` when present; the archive's newest entry must not be younger than `history.md`'s oldest | 0 lines of output and exit 0; invalid chronology or missing history prints a diagnostic and exits nonzero |
| 7 · SEALED ids — every `SEALED: D-xx` marker resolves as an exact decision heading in `decisions.md` that is not marked superseded (`⤴`, or a `· superseded by D-` segment) | 0 lines of output |
| 8 · Cross-initiative collision — two active initiatives (a `task-board.md` with ≥ 1 active **data row**; the legend line does not count) declare intersecting Write scope; lexical equality, normalized equality, or directory/descendant containment is a collision, while unsupported scope forms are reported as unresolved | 0 lines of output — any line is a **warn** |
| 9 · Loop-task budget fields — every `Type: discovery` task declares `Rounds:`, every `Type: experiment` task declares `Metric:`, `Threshold:` and `Rounds:`, each as a field (bold, or at the start of its line), never in quoted prose | 0 lines of output |
| 10 · Terminal rows carry a verification reference, and a Ready to run row cites its readiness — every `task-board.md` row whose status is Complete, Blocked or Unverifiable carries exactly `reports/<id>-report.md` in Verification (the status is read like row 3), and a `Ready to run` row's Verification cell starts with `ready: ` plus a non-empty reference; an older board is refused | 0 lines of output |
| 11 · Usage rows for completed tasks — every `task-board.md` row whose status is Complete has at least one `resource-usage.md` row (`grep -q "\| $id "`); a workspace without `resource-usage.md` guard-skips (rows 2 and 16 report it); an older board is refused | 0 lines of output and exit 0; an older board or a done task without its usage row prints a diagnostic and exits nonzero; a missing `resource-usage.md` is a checked skip |
| 12 · Effort, Tier and Escalation vocabulary — every `**Effort**:` declaration in the `tasks/` brief of a task that is not closed (the board shows it neither Complete, Skipped nor Unverifiable) is exactly a §3 level (`low`/`medium`/`high`/`max`), checked even inside a fenced block; outside any fenced block, a present `**Tier**:` is `fast`/`standard`/`frontier` and requires a `**Tier reason**:` (which may also appear alone, recording an Effort-only deviation from the compiled default), and an Effort other than `low` needs one of the two; a present `**Escalation**:` is `declared` and never present without `**Tier**:`; fenced examples (`` ``` `` or `~~~`, as row 1 also skips) exempt only the Tier/Tier reason/Escalation checks, never Effort; peripheral whitespace and any bullet marker (`-`, `*`, `+`) are allowed; an older board is refused | 0 lines of output |
| 13 · History over archive threshold or entry budget — `history.md` exceeds the archive threshold (default 400 lines; workspace-overridable via `Log archive threshold: N` in the workspace `AGENTS.md`), or a session entry (from its `## YYYY-MM-DD` heading through the line before the next `## ` heading, trailing blank lines excluded, `###` lines inside) runs past the entry budget (default 120 lines; workspace-overridable via `History entry budget: N`); a missing `history.md` is an error; fix path: RUN archives or shortens under the workspace's maintenance policy (default in `AGENTS.md`, recoverable maintenance in `context-lifecycle.md`), never STATUS | 0 lines of output — any line is a **warn** |
| 14 · Closure reports for done tasks — every `task-board.md` row whose status is Complete has `reports/T-0N-report.md` (the report may be a stub naming its reviewer, ending with the receipt described in `run.md` §Run record); explicit Lite workspaces guard-skip after row 1 validates their shape; an older board is refused | 0 lines of output |
| 15 · Reference-doc staleness — every `reference-docs/*.md` carrying a `captured: YYYY-MM-DD` first-line header is younger than the staleness window (default 14 days; workspace-overridable via `Reference staleness window: N` in the workspace `AGENTS.md`); undated files skip (the header convention lands in `reference-docs-README.tmpl.md`); fix path: re-snapshot from the live source and update `captured:` | 0 lines of output — any line is a **warn** |
| 16 · Lifecycle validity — exactly one start, at most one legal terminal after it, stable Task/Role, valid Outcome and nonnegative or unknown counters; a positive Attempts count requires task-linked failed correction or one authorized escalation rather than a count label; legacy Point remains readable | 0 lines of output and exit 0; malformed state or unsupported known Attempts prints row16, line and Run ID diagnostics and exits nonzero |
| 17 · Post-task obligations — every Complete task's report carries a receipt line, `**Remains**: none` or `**Remains**: O-NN[, O-NN…]` (code fences are not read); every `O-NN` cited in a receipt or in the newest State snapshot's `Active obligations` line has a row in the board's obligations table; every `Open` row is named in that snapshot line; a row's state is `Open`, `Discharged` or `Withdrawn`, and a `Discharged` or `Withdrawn` row cites a reference (a decision id, or a report or record path); every row of the table headed `Obligation`, and any row whose first cell starts with `O-`, is an obligation, and a first cell that is not exactly an `O-NN` id, whatever its decoration, is malformed; explicit Lite workspaces guard-skip after row 1 validates their shape; an older board is refused | 0 lines of output |

Per citation, row 4 is equivalent to the canonical anchored-citation check (`sed -n 'NNp' path` piped to `grep -Fq "fragment"`), run as one loop over every citation.

For optional exact extraction, row-specific interpretation and dependency-aware reuse during
Full execution, see [execution checks](full-checks.md). Saved canonical command bytes and raw
stdout/stderr/exit remain authoritative; no generated PASS counter substitutes for them.

The release sweep and the self-lint gates are documented in the repository's
`MAINTAINING.md`.

## Score line

Run all 17 rows. The script's `lint: K/17 rows silent` line counts silent rows and is not this score
line: the agent computes the numerator and denominator from the observed row results; this **agent-computed summary** closes the lint digest with exactly:

`lint: N/M checks passed`

- **M** = rows run (17 for this table; more if the workspace adds rows).
- **N** = rows whose pass condition held.

- Row 8 filters unmatched board/task globs before scanning; no boards means no board-based collision finding. Park seeds separately (`docs/seeds/`).
- Discussing scanned symbols inside workspaces (status glyphs, placeholder braces): use U+XXXX prose notation and `$'\uXXXX'` shell escapes so rows 1/3/5 don't self-flag the discussion.
- Rows 8, 13 and 15 are warn-severity: they lower N and are reported, but block nothing by themselves; a failure in rows 1–7, 9–12, 14, 16 and 17 blocks execution until fixed or explicitly waived by the user.
- This score line is what a human skims in a pulse or handoff for readiness (the pulse digest carries it); a lint digest without it is incomplete.

## Workspace format

Task boards declare `Schema: tackle-workspace/5` in `task-board.md`; rows 2, 3, 5, 10, 11, 12, 14 and 17 refuse a Coordinated workspace without one with `migrate first`, and row 3 validates the ten `/5` states, including `Waiting on owner`. Row 10 requires terminal checked/blocked tasks to reference `reports/T-id-report.md` and a `Ready to run` row to cite `ready: <reference>`; the report carries method/result/observed independence and actual raw-record references. Row 14 still requires every Complete task report; RUN verifies its contents and deliverable acceptance. Rows 2/8 read only Task headings and Write scope. Row 8 treats In progress, Checking, Interrupted and Waiting on owner as active scope. State labels alone never establish readiness, current proof or closure. Row 12 checks only the briefs of tasks that are not closed, so a migrated workspace's closed briefs need no Tier reason.

Indexed history is an additional triggered validation: when a workspace adopts `context-lifecycle.md`, run its archive-integrity check over every selected/required segment as well as row 6. Row 6 still verifies active and archived history ordering; an unverified/missing segment cannot be hidden by its passing result.

## Lite applicability

Only the exact first line `Gate: Lite` in `plan.md` declares Lite. Missing board/tasks, prose and
fenced examples never do. The marker records an authorized route; it cannot waive risk precedence
or be added by a read-only audit. Unmarked workspaces receive the Full checks.

Row 1 requires Focused plan/history/resource usage, refuses `log.md`, `log-archive.md` or `usage.md` with `migrate first`, and rejects both task-board.md and board.md, any `tasks/` or legacy `points/` entry
(including dangling symlinks), and a Full Task or legacy Point decomposition heading outside fences. Run it before accepting
the checked Lite skips in rows 2, 3, 5, 9, 10, 11, 12, 14 and 17. All seventeen commands still execute;
row 5 retains its empty-output exit 1. A guard-skipped row alone never approves a workspace.
Shared placeholders, citations in plan/optional reference, seals, chronology and lifecycle remain
mandatory. Optional AGENTS overrides default when absent; read errors are not PASS. Row 8 keeps
board-based activity; selected Lite still requires mandatory lint and current global acceptance.
Do not create fake Full artifacts. Route changes invalidate all row applicability observations.
