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

<a id="v84--v90-checklist"></a>
## v8.4 → v9.0 checklist

This major release replaces the RUN and PLAN guides with cards, keys migration on the board
schema and retires the 8.x action-name aliases. Adopt it only for a selected active workspace, on
a disposable copy at a task boundary; installing 9.0 migrates nothing by itself.

1. Before updating the install, move any file you added under `references/archetypes/` to
   `.tackle/archetypes/` or `~/.tackle/archetypes/`. The install no longer carries
   self-development archetypes, and an update drops files left there.
2. Record the pinned procedure and the current lint result (`lint: N/16`), with hashes of the
   board, briefs and history. Preserve neighboring workspaces.
3. Migrate the board through the [schema-keyed migration](#schema-keyed-migration) and its
   [steps](#migration-steps). A board whose fenced example never closes is refused; close the
   fence and run the step again.
4. Run rows 1–16 on the migrated copy. On a `/5` board, row 12 reports `Effort without Tier
   reason` for an older brief whose Effort is not `low` and that has no Tier and no Tier reason.
   This is expected: add a `**Tier reason**` line to that brief saying why its Effort departs
   from the default, as the [task template](../task.tmpl.md) shows.
5. Replace retired 8.x action names in forward-looking prompts with the current request words;
   [terminology.md](../terminology.md) maps each old name. Preserve historical records verbatim.
6. Profiles need no action: an entry without an id stays readable, and the next retro that
   touches it assigns an id and computes its confidence.
7. The routing fields (`Tier`, `Tier reason`, `Escalation`) are optional; a brief without them
   keeps the default. Planning runs on a more capable tier than the Executor's whenever the
   model map binds more than one tier.
8. Adopt only the validated copy at the boundary. Record the path mapping, the checks and the
   rollback result; a failed check leaves the original active and unchanged.

<a id="schema-keyed-migration"></a>
## Schema-keyed migration (9.0.0)

Migration keys on the board's `Schema:` line, or on structure when the line is absent — never on the
free-text `Methodology:` stamp, which is display-only. [`recipes/migrate/schema.md`](../recipes/migrate/schema.md)'s
`schema_of(files)` reads only the workspace root (top-level files; nested paths are ignored for
detection) and ignores any `legacy-*/` directory, so a stray legacy snapshot next to a current board
never changes the bucket. A workspace matching more than one row below is `unknown`; its scan for the
`Schema:` line skips fenced code blocks.

| Bucket | Detected by | Next step |
|---|---|---|
| `pre-3` | a `board.md` with no `Schema:` line, and a header row with `Point` or `Task` and a `Status` column | [`step-pre3-to-3`](../recipes/migrate/step-pre3-to-3.md) |
| `3` | a `board.md` whose line is `Schema: tackle-workspace/3` | [`step-3-to-4`](../recipes/migrate/step-3-to-4.md) |
| `4` | a `task-board.md` whose line is `Schema: tackle-workspace/4` | [`step-4-to-5`](../recipes/migrate/step-4-to-5.md) |
| `5` | a `task-board.md` whose line is `Schema: tackle-workspace/5` | none (current in 9.0.0) |
| `lite` | a `plan.md` whose first line is `Gate: Lite` | none (no board schema) |
| `unknown` | anything else | none; report and stop |

<a id="migration-steps"></a>
## Migration steps

Each step is one idempotent detect → transform → verify recipe; a second run of any step on its own
output is a byte-identical no-op. Standard library only. To run a step: execute
[`schema.md`](../recipes/migrate/schema.md)'s fenced block first into a namespace, then execute the
chosen step's fenced block into a namespace seeded with `schema.md`'s names (each step's `detect`,
`transform` and `verify` call `schema_of`, `parse_board` and the other shared helpers by name, and
resolve them from that shared namespace, not a copy). Advance a real workspace with
`schema.md`'s `adopt(files, context, transform)`, never by calling a step's `transform` directly on a
workspace's full file mapping: `transform`'s `files` argument must already exclude any `legacy-*/`
directory, and only `adopt` supplies that, then reassembles the result with every pre-existing
`legacy-*/` directory preserved and the step's own new snapshot added. Passing a mapping that still
holds `legacy-*/` straight to `transform` risks that step's rename or id-mapping logic reaching inside
the legacy snapshot and rewriting it.

- [`step-pre3-to-3`](../recipes/migrate/step-pre3-to-3.md) — generalizes `candidate_board()`
  (`maintaining/migrations.md`) three ways: it accepts P- and T-ids, it maps the legacy states exactly
  as [terminology.md](../terminology.md)'s States table does, and it never infers `Ready to run`. A
  `/3` board (or later) returns unchanged.
- [`step-3-to-4`](../recipes/migrate/step-3-to-4.md) — the v8.3 → v8.4 layout, done mechanically: renames
  the artifacts that exist (see the checklist above), maps every P-id to one T-id and rewrites the ids
  in the contents — not only the file names — of `plan.md`, every brief, the board and its dependencies,
  every report, and the usage ledger's rows (its column format, 8-column legacy or v2 lifecycle, is
  preserved; only the ids inside it are mapped). `history.md` keeps whichever of `log.md`'s or its own
  original bytes was already there, plus one appended adoption entry, written exactly once even when
  the workspace already carries it; `log.md` and `history.md` both present at once is a rename-target
  collision (see below), refused by name rather than silently picked between. `decisions.md` and
  `design-contract.md` are never rewritten; an interrupted, pinned task surfaces as residue for review
  at that task's own boundary (R-MIGRATE-02), never a silent rewrite or a silent restart. An empty P→T
  map and an absent `points/`
  are valid inputs — a `/3` workspace already on `tasks/` and T-ids only gets its board renamed and
  restamped. A `/4` board (or later) returns unchanged.
- [`step-4-to-5`](../recipes/migrate/step-4-to-5.md) — sets `Schema: tackle-workspace/5` and gives every
  `Ready to run` row without a citation the Verification text `ready: legacy /4 readiness`. It changes
  nothing else: a row that already carries some other, non-placeholder Verification text is left alone
  and reported for review rather than overwritten. A `/5` board returns unchanged.

Each step's `verify(before, after)` takes the same `legacy-*/`-excluding `files` shape as `transform`
(`schema.md`'s `workspace_files(files)` of the pre- and post-adoption mappings, not the adopted result
itself, which still carries the legacy snapshots) and is self-contained Python, checked against this
guide's own reading of each schema: state vocabulary, `Verification` references and, for `step-4-to-5`,
the `ready:` rule.
It does not shell out to this repository's lint rows, which reject `/5` until the board-schema task
lands. `errors` gate adoption: the wrong bucket after the step, a second `transform` that is not
byte-identical, a board invariant, or an old artifact name left in the root — each a check `verify`
itself performs and reports. A rename-target collision is a separate, transform-time refusal, not a
`verify` error: an old artifact name and its new name both already present (`usage.md` and
`resource-usage.md`, `board.md` and `task-board.md`, `log.md` and `history.md`, or a `points/<id>`
brief and a `tasks/<id>` one) makes `transform` itself raise by name before anything is written, so
adoption never reaches `verify` for that workspace. `residue` lists what the agent must review before
adoption, for example a stray id mention in rewritten prose.

<a id="read-compatibility-promise"></a>
## Read compatibility

The install reads, and operates on, every workspace in a bucket above; it offers a migration only when
the requested action needs a newer format. Below the `pre-3` bucket nothing is promised, and this
repository's historical checklists above and in `maintaining/migrations.md` apply.

<a id="pre-migration-originals"></a>
## The pre-migration original's home

Each step's adoption writes the new content plus every `legacy-*/` directory that existed before,
unchanged, and adds its own `legacy-<bucket>/` snapshot: the workspace root exactly as the step read it,
byte-identical and read-only, before that step's transform ran. By construction this is
outside every row that reads a board or history by its path. Row 1's placeholder scan still reaches one
level into every subdirectory, including a `legacy-*/` one — noted here for the task that next edits
that row.

<a id="migration-rollback"></a>
## Rollback

A failed `verify` leaves the workspace active and unchanged: nothing is written. To undo an already
adopted step, restore the checkpoint taken before that step ran; the pre-migration original is also
available, byte-identical, at that step's own `legacy-<bucket>/` snapshot.
