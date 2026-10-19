# Step 8.5 — Migrate

Migration is a **copy-first, selected-active-work** operation. It never structurally rewrites a live
workspace or its history during the migration trial,
automatically migrates unrelated or closed work, upgrades historical evidence, or turns a query into
execution. A workspace below bucket `5` reaches it with the 8.4 → 9.0 checklist below; a later
release is adopted with its own checklist, under [Adopting a release](#adopting-a-release).
Historical checklists for older workspaces are in the repository's
`maintaining/migrations.md`; they remain readable historical context and cannot bypass the
current selection, pinning, history or rollback guards.

Only a selected active workspace is migrated, and only on a disposable copy. Closed P tasks retain
their recorded state and evidence; future execution uses the RUN protocol at a task boundary.

`improve this plan`, `migrate`, and `upgrade` route to PLAN's migration preparation. An unstructured
source is ingested fresh through PLAN.

Current interaction uses one skill entry: select Tackle, then state a request such as `plan`,
`run`, `status` or `verify`. Update forward-looking prompts to that form when migrating selected
work; preserve historical records verbatim. Old slash spellings in historical checklists are
historical text aliases, not separately registered menu commands. See [invocation.md](invocation.md).

<a id="adopting-a-release"></a>
## Adopting a release

Each checklist below applies only to a selected active workspace, on a disposable copy at a task
boundary; neighboring workspaces stay untouched. Continue started or interrupted work under its pinned procedure.
A step that acts on the install, such as the bridge's step 1, comes first. Before any step that changes the
workspace copy, record that procedure, the current lint result under it, and hashes of
the board, briefs, reports, `AGENTS.md` and history; keep an unchanged checkpoint copy. After the release's
steps, run the lint on the copy. Adopt only the validated copy: record the adoption, its checks and the rollback
result, and bump the `Methodology:` stamp to the adopted release. A failed check holds adoption and
leaves the original active and unchanged. Adoption rewrites no closed task, no historical record and no
neighboring workspace. Roll back by restoring the checkpoint copy.

<a id="older-stamps"></a>
Apply the checklists in release order, from the workspace's `Methodology:` stamp to the current release,
skipping none. A stamp older than the 8.4 → 9.0 bridge, or from 9.0.0 through 9.2.0, needs intermediate
checklists that do not ship with the install. The owner reads them in the public repository at
https://github.com/alph0x/Tackle/blob/v10.0.0/maintaining/migrations.md; Tackle itself opens no network
connection. Or start the remaining work in a fresh workspace and leave the old one as it is.

<a id="v84--v90-checklist"></a>
## v8.4 → v9.0 checklist

This major release replaces the RUN and PLAN guides with cards, keys migration on the board
schema and retires the 8.x action-name aliases. Installing 9.0 migrates nothing by itself. 9.0 runs only
the current layout and refuses a workspace that has not been migrated
([forward only](#forward-only)).

1. Before updating the install, move any file you added under `references/archetypes/` to
   `.tackle/archetypes/` or `~/.tackle/archetypes/`. The install no longer carries
   self-development archetypes, and an update drops files left there.
2. Migrate the board through the [schema-keyed migration](#schema-keyed-migration) and its
   [steps](#migration-steps) to bucket `5`. A board whose fenced example never closes is refused;
   close the fence and run the step again. A Focused workspace has no board: rename `log.md`,
   `log-archive.md` and `usage.md` to `history.md`, `history-archive.md` and `resource-usage.md`.
3. Run rows 1–16 on the migrated copy. Row 12 checks only the briefs of tasks that are not
   closed (Complete, Skipped or Unverifiable), and reports `Effort without Tier reason` for such
   a brief whose Effort is not `low` and that has no Tier and no Tier reason.
   This is expected: add a `**Tier reason**` line to that brief saying why its Effort departs
   from the default, as the [task template](../task.tmpl.md) shows. In the same open briefs, rename `**Touches**` to
   `**Write scope**` and `Done-signal` to `Acceptance check`, and replace an `inherit` Effort with
   a level.
4. Replace retired 8.x action names in forward-looking prompts with the current request words;
   [terminology.md](../terminology.md) maps each old name. Preserve historical records verbatim.
5. Profiles need no action: an entry without an id stays readable, and the next retro that
   touches it assigns an id and computes its confidence.
6. The routing fields (`Tier`, `Tier reason`, `Escalation`) are optional; a brief without them
   keeps the default. Planning runs on a more capable tier than the Executor's whenever the
   model map binds more than one tier.
7. Record the path mapping with the adoption.

<a id="v92--v93-checklist"></a>
## v9.2 → v9.3 checklist

An active 9.2 workspace adopts 9.3.0 with this checklist. This release changes the plan view's template and
the styling of auxiliary pages, and it changes no file format.

1. If the workspace has a plan view, rebuild it under its standing view request, since the template changed.
   Without that request, build no view. Existing auxiliary pages change only on request; move one to the
   plan view's base only when the owner asks.
2. Sibling workspaces are optional. A workspace that declares none needs no change.

<a id="v93--v100-checklist"></a>
## v9.3 → v10.0 checklist

An active 9.3 workspace adopts 10.0.0 with this checklist. This release ships every program as a script under
`scripts/` (Python 3.10 or later), and it changes no file format.

1. An owner who runs a 9.3 loopback live producer stops it before updating; 10.0 retires the live view and
   ships no producer.
2. If the workspace has a plan view, rebuild it with `scripts/plan_view.py` under its standing view request,
   as the [plan view guide](plan-view.md) states. Without that request, build no view.
3. Saved copies of 9.x recipe programs are obsolete; use the scripts under `scripts/` in their place.
4. A verification record that an installed `capture.py` or `lint_runner.py` made while running from outside the working
   directory names that script's sha256, so it is refused once the install updates the script. Rerun those
   checks under the updated install.
5. [System One](system-one.md) goes through the host's `typesafe-ai` skill. A recorded `System One consent:` line keeps its
   meaning and needs no change; never copy one from a parent or neighboring workspace.

<a id="v100--v101-checklist"></a>
## v10.0 → v10.1 checklist

An active 10.0 workspace adopts 10.1.0 with this checklist.

1. Add `Gate: Full` on line 3 of an active Coordinated plan, following `plan.tmpl.md`; keep its title on line 1 and keep a Lite plan’s `Gate: Lite` on line 1.
2. Use the `history.tmpl.md` journal form `correction cycle N of 3: <failure> → <correction>; <validation command>: <result>` for new correction records; preserve older `attempt N:` records.
3. Write lifecycle `At` clocks with seconds, `YYYY-MM-DDTHH:MM:SS[.fff](Z|±HH:MM)`, as `resource-usage.tmpl.md` states; minute-only and space-separated clocks remain unmeasured.
4. Use the same `At` clock format in the ledger body of `lite-plan.tmpl.md`; keep an unobserved clock as `n/a`.
5. Use the updated `retro.tmpl.md` recipes: Attempts accepts both journal forms; Gate accuracy counts distinct sessions over the archive and current history and reports undated headings; Blocked durations excludes State snapshot lines.
6. Expect lint row 13 WARN lines for dated entries after the newest State snapshot and for undated session headings; these warnings do not become mandatory failures.
7. Build an optional `--initiative` page only under an owner request, following the [plan view guide](plan-view.md#initiative-view); it reads the root and one hop of declared sibling workspaces.
8. Name forbidden action classes in new task briefs with the `Forbidden actions` field of `task.tmpl.md`, following the design guide's brief obligations; existing briefs need no change.
9. Keep the current workspace schema and file formats; this release changes neither, and an existing recorded System One consent keeps its meaning.

<a id="schema-keyed-migration"></a>
## Schema-keyed migration (9.0.0)

Migration keys on the board's `Schema:` line, or on structure when the line is absent — never on the
free-text `Methodology:` stamp, which is display-only. [`schema.py`](../../scripts/migrate/schema.py)'s
`schema_of(files)` reads only the workspace root (top-level files; nested paths are ignored for
detection) and ignores any `legacy-*/` directory, so a stray legacy snapshot next to a current board
never changes the bucket. A workspace matching more than one row below is `unknown`; its scan for the
`Schema:` line skips fenced code blocks.

| Bucket | Detected by | Next step |
|---|---|---|
| `pre-3` | a `board.md` with no `Schema:` line, and a header row with `Point` or `Task` and a `Status` column | [`step_pre3_to_3.py`](../../scripts/migrate/step_pre3_to_3.py) |
| `3` | a `board.md` whose line is `Schema: tackle-workspace/3` | [`step_3_to_4.py`](../../scripts/migrate/step_3_to_4.py) |
| `4` | a `task-board.md` whose line is `Schema: tackle-workspace/4` | [`step_4_to_5.py`](../../scripts/migrate/step_4_to_5.py) |
| `5` | a `task-board.md` whose line is `Schema: tackle-workspace/5` | none (current in 9.0.0) |
| `lite` | a `plan.md` whose first line is `Gate: Lite` | none (no board schema) |
| `unknown` | anything else | none; report and stop |

<a id="migration-steps"></a>
## Migration steps

Each step is one idempotent detect → transform → verify script; a second run of any step on its own
output is a byte-identical no-op. Standard library only. Importing these scripts needs the owner's explicit
authorization; an explicit migration request grants it for that migration (the [script consent](../../scripts/README.md#consent)).
Prefer an equivalent harness capability. The scripts have no command line: to run a step, put
`<skill>/scripts/migrate/` first on `sys.path` and import the step by name (`step_pre3_to_3`,
`step_3_to_4` or `step_4_to_5`). Each step imports [`schema.py`](../../scripts/migrate/schema.py) from its
own folder, so each step's `detect`, `transform` and `verify` call `schema_of`, `parse_board` and the
other shared helpers from that one module, not a copy. Advance a real workspace with
`schema.adopt(files, context, step.transform)`, never by calling a step's `transform` directly on a
workspace's full file mapping: `transform`'s `files` argument must already exclude any `legacy-*/`
directory, and only `adopt` supplies that, then reassembles the result with every pre-existing
`legacy-*/` directory preserved and the step's own new snapshot added. Passing a mapping that still
holds `legacy-*/` straight to `transform` risks that step's rename or id-mapping logic reaching inside
the legacy snapshot and rewriting it.

The context passed to adopt holds date, run_id and methodology, and may hold workspace, the migrated workspace's directory name, so that the 8.3 to 8.4 step can tell its own links from links into other workspaces.

- [`step_pre3_to_3.py`](../../scripts/migrate/step_pre3_to_3.py) — generalizes `candidate_board()`
  (`maintaining/migrations.md`) three ways: it accepts P- and T-ids, it maps the legacy states exactly
  as [terminology.md](../terminology.md)'s States table does, and it never infers `Ready to run`. A
  `/3` board (or later) returns unchanged.
- [`step_3_to_4.py`](../../scripts/migrate/step_3_to_4.py) — the v8.3 → v8.4 layout, done mechanically: renames
  the artifacts that exist (see the 8.3 → 8.4 checklist in `maintaining/migrations.md`), maps every P-id to one T-id and rewrites the ids
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
- [`step_4_to_5.py`](../../scripts/migrate/step_4_to_5.py) — sets `Schema: tackle-workspace/5` and gives every
  `Ready to run` row without a citation the Verification text `ready: legacy /4 readiness`. It changes
  nothing else: a row that already carries some other, non-placeholder Verification text is left alone
  and reported for review rather than overwritten. A `/5` board returns unchanged.

Each step's `verify(before, after)` takes the same `legacy-*/`-excluding `files` shape as `transform`
(`schema.py`'s `workspace_files(files)` of the pre- and post-adoption mappings, not the adopted result
itself, which still carries the legacy snapshots) and is self-contained Python, checked against this
guide's own reading of each schema: state vocabulary, `Verification` references and, for `step_4_to_5.py`,
the `ready:` rule.
It does not shell out to the lint rows; the [9.0 checklist](#v84--v90-checklist) runs them on the
migrated copy. `errors` gate adoption: the wrong bucket after the step, a second `transform` that is not
byte-identical, a board invariant, or an old artifact name left in the root — each a check `verify`
itself performs and reports. A rename-target collision is a separate, transform-time refusal, not a
`verify` error: an old artifact name and its new name both already present (`usage.md` and
`resource-usage.md`, `board.md` and `task-board.md`, `log.md` and `history.md`, or a `points/<id>`
brief and a `tasks/<id>` one) makes `transform` itself raise by name before anything is written, so
adoption never reaches `verify` for that workspace. `residue` lists what the agent must review before
adoption, for example a stray id mention in rewritten prose.

<a id="read-compatibility-promise"></a>
<a id="forward-only"></a>
## Forward only

The install runs only a workspace in bucket `5`, or a Focused `plan.md` whose history and usage
are `history.md` and `resource-usage.md`. PLAN, RUN and STATUS refuse any other workspace with
`migrate first` and point here, and lint rows 1, 2, 3, 5, 10, 11, 12, 14 and 17 print that refusal.
A board saved with CRLF line endings reads as older: convert it to LF first, because the rows, the
scripts and this migration read LF only. This guide, its scripts and their fixtures are the one
bridge: they keep detecting and transforming every bucket above. The readability statements in the 8.x checklists describe 8.x installs.
Below the `pre-3` bucket nothing is promised, and this
repository's historical checklists in `maintaining/migrations.md` apply.

<a id="pre-migration-originals"></a>
## The pre-migration original's home

Each step's adoption writes the new content plus every `legacy-*/` directory that existed before,
unchanged, and adds its own `legacy-<bucket>/` snapshot: the workspace root exactly as the step read it,
byte-identical and read-only, before that step's transform ran. By construction this is
outside every row that reads a board or history by its path. Row 1's placeholder scan skips every
`legacy-*/` directory.

<a id="migration-rollback"></a>
## Rollback

A failed `verify` leaves the workspace active and unchanged: nothing is written. To undo an already
adopted step, restore the checkpoint taken before that step ran; the pre-migration original is also
available, byte-identical, at that step's own `legacy-<bucket>/` snapshot.
