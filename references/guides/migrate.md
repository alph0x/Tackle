# Step 8.5 — Migrate

Migration is a **copy-first, selected-active-work** operation. It never structurally rewrites a live
workspace or its history during the migration trial,
automatically migrates unrelated or closed work, upgrades historical evidence, or turns a query into
execution. Select the 8.3 → 8.4 checklist for a workspace that will adopt T identifiers. An active
8.4.0 workspace adopts 8.4.1 at a task boundary with the 8.4.0 → 8.4.1 patch checklist below.
Historical checklists for older workspaces are in the repository's
`maintaining/migrations.md`; they remain readable historical context and cannot bypass the
current selection, pinning, history or rollback guards.

Only a selected active workspace is migrated, and only on a disposable copy. Closed P tasks retain
their recorded state and evidence; future execution uses the RUN protocol at a task boundary.

`improve this plan`, `migrate`, and `upgrade` route to PLAN's migration preparation. An unstructured
source is ingested fresh through PLAN.

Current interaction uses one skill entry: select Tackle, then state a request such as `plan`,
`run`, `status` or `verify`. Update forward-looking prompts to that form when migrating selected
work; preserve historical records verbatim. Old slash spellings in the checklists below are
historical text aliases, not separately registered menu commands. See [invocation.md](invocation.md).

<a id="v840--v841-checklist"></a>
## v8.4.0 → v8.4.1 checklist

This patch makes the lint rows stricter and restores template clauses; it renames nothing. Adopt
only for a selected active workspace, on a disposable copy at a task boundary.

1. Record the pinned procedure and the current lint result (`lint: N/16`), with hashes of the
   board, briefs and history. Preserve neighboring workspaces.
2. Run rows 1–16 of 8.4.1 on the copy. New findings are expected and name real defects:
   - a stale second citation on a line (row 4);
   - a seal whose decision is superseded (row 7);
   - a loop budget written only in prose (row 9);
   - `inherit`, or a non-dash bullet, on an Effort line in `tasks/` (row 12);
   - Write scope lines that row 8 cannot parse (warn).

   Fix each in the workspace's own records and re-anchor citations with `verify.md` step 0. A
   citation of a line the task itself changed may be pinned as `path@<rev>:NN`.
3. Remove `**tackle-gate: on**` from `AGENTS.md` when present; no current guide reads it. Existing
   briefs keep their pinned text. Briefs compiled after adoption use the new template, with the
   E2E-first and replay clauses and the loop-budget fields.
4. When `design-contract.md` has compiled clauses, add each clause id to its heading
   (`## C01 · …`). Do it only through a superseding decision with regenerated clause hashes, then
   run the seal command in `verify.md` step 8.
5. Record a `D-xx`, append the adoption to `history.md`, and bump the `Methodology:` stamp to
   8.4.1. Roll back by restoring the checkpoint copy.

<a id="candidate-workspace-format"></a>
## v8.3 → v8.4 checklist

New Coordinated workspaces use `T-01`, `tasks/`, `task-board.md`, `history.md`,
`resource-usage.md`, `task.tmpl.md` and the corresponding new templates. New Focused workspaces
use `plan.md`, `history.md` and `resource-usage.md`. Triggered artifacts use
`history-archive.md`, `current-work.md`, `handoff-brief.md` and `verification-records/`.
The board declares `Schema: tackle-workspace/4`. Existing P workspaces and v3 T candidates
remain readable with their original paths, links and recorded history. Installing 8.4 does not
rename any workspace or relax the 8.3 test-selection and E2E replay-evidence rules.

1. Select an active workspace and record its pinned procedure, task boundary, exact file/brief
   links, history and raw-record hashes. Keep an unchanged checkpoint and neighbor sentinel.
   A read-only request cannot select a migration.
2. Continue started or interrupted work under its pinned procedure. At a deliberate boundary,
   prepare a separate candidate on a disposable copy with an explicit old→new path and P→T
   obligation map. Preserve completed task identities and original history as external sources;
   never rewrite original bytes or reset attempt counts.
3. In the new candidate, instantiate `task-board.tmpl.md`, `history.tmpl.md`,
   `resource-usage.tmpl.md` and `task.tmpl.md`. Make plan §5, task board, every brief,
   dependency, ledger and report agree on T IDs and the v4 paths. Do not keep old-name
   duplicates or mix `points/` into the new workspace. Link verified old outputs with source
   revision and recheck inherited readiness against the new contract.
   - Rename every legacy artifact and update each link to it:
     `board.md` → `task-board.md`, `log.md` → `history.md`,
     `log-archive.md` → `history-archive.md`, `usage.md` → `resource-usage.md`,
     `coordinator.md` → `current-work.md`, `HANDOFF.md` → `handoff-brief.md`,
     `evidence/` → `verification-records/`, `points/` → `tasks/`.
   - Map each P id to one T id (`P-01` → `T-01`) in file names, dependencies, the ledger and
     reports, and record the mapping. Brief headings name the Task: `# Point` → `# Task`.
   - Declare `Schema: tackle-workspace/4` on the board, convert every Status cell with the
     mapping in `terminology.md`, name the last column `Verification`, and point each Complete,
     Blocked or Unverifiable row at `reports/T-NN-report.md`.
   - A legacy `usage.md` table stays readable as `resource-usage.md`; append new rows in the v2
     lifecycle table of `resource-usage.tmpl.md`.
4. Run canonical lint on both unchanged source and candidate. Exercise missing briefs, dangling
   dependencies, mixed old/new paths, malformed state, history/archive order and resource usage.
   Preserve the 8.3 E2E replay artifacts. Compare original history and neighbor hashes byte for
   byte, then restore a separate checkpoint copy to prove rollback.
5. Adopt only the validated continuation at the boundary. Append the path/identity mapping,
   input revisions, observed checks and rollback result; keep the original workspace readable.
   A failed check leaves it active and unchanged.
