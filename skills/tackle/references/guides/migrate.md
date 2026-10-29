# Migrate

Migration uses one installed catalog route for an explicitly selected active workspace. It operates
on a disposable copy, preserves closed and neighboring work, and leaves status, consent, and release
acceptance to their existing owners. Historical sources remain available in
`maintaining/migrations.md` as provenance; they do not select the active procedure.

Historical checklists for older workspaces are in the repository's `maintaining/migrations.md`; they remain readable historical context and cannot bypass the current selection, pinning, history or rollback guards.

`improve this plan`, `migrate`, and `upgrade` route to PLAN preparation. An unstructured source is
ingested through PLAN. See [invocation.md](invocation.md) for the current skill entry.

Use the [compact migration route](#compact-migration) as the installed bridge; the historical archive does not select another execution procedure.

<a id="adopting-a-release"></a>
## Adopting a release

1. Confirm the selected active workspace, observed structure, current target and actual capability requirements through the [compact route](#compact-migration). Continue started or interrupted work under its pinned procedure. A stamp alone proves neither structural compatibility nor adoption.
2. Use a disposable copy at a task boundary for cutover. Record the original inventory, closed records, correction lineage and immutable checkpoint as described under [originals](#pre-migration-originals). `prepare` may build the isolated copy earlier; the original remains authoritative and adoption still waits for an evidenced boundary and writer quiescence.
3. Resolve current semantic work in that copy: retain the required baselines and authorized errata, prepare only the declared upcoming work, and obtain actual applicability, consent and capability evidence for requested optional features. Neither an old checklist nor a copied answer supplies current authority.
4. Validate the copy with structural verification, separate pre-stamp and post-stamp lint, read-only readiness, restoration rehearsal and independent semantic evidence. A failed check holds adoption. Adopt only the validated copy after rechecking source, candidate, resources and evidence under the cooperating locks; the next task’s writing Check remains post-adoption work.
5. Record the adopted operation, exact mappings, checks and rollback result. Roll back by restoring the checkpoint copy. Use the explicit `restore` phase through its verified sibling stage only while the adopted workspace still matches its recorded posthash; preserve the job’s original backup and evidence. A completed repeat validates identity and adds no effects.

<a id="older-stamps"></a>
<a id="compact-migration"></a>
## Compact migration route

The installed catalog is the sole active route from supported workspace structure to Tackle 10.3.1. Read the workspace structure and its `Methodology:` stamp as separate facts: structure selects only the exact existing adapter, while the stamp records methodology and never proves adoption. The closed, installed-only catalog retains every historical obligation and its source provenance at [migration-catalog.json](migration-catalog.json).

Use the five-command interface in order: `diagnose`, `prepare`, `verify`, `adopt`, and `restore`. Running the migration script requires the owner's explicit migration request under the [script consent](../../scripts/README.md#consent); an equivalent harness route may perform the same bounded operation. `diagnose` reads one explicitly selected absolute workspace and produces a complete observation manifest; pending or unknown facts remain visible. `prepare` requires a fresh external job directory on the same filesystem, records an immutable checkpoint, and creates the candidate using the existing schema adapters. Resolve listed owner decisions and semantic work in the copy. The original remains authoritative while the candidate is being prepared.

The CLI takes absolute paths for workspace, context, output, manifest, and job:

```text
python3 -I -B <installed-scripts>/migrate/compact.py diagnose --workspace <ABS_SOURCE> --target 10.3.1 --context <ABS_CONTEXT_JSON> --output <ABS_NEW_MANIFEST>
python3 -I -B <installed-scripts>/migrate/compact.py prepare --manifest <ABS_MANIFEST> --job <ABS_JOB>
python3 -I -B <installed-scripts>/migrate/compact.py verify --job <ABS_JOB>
python3 -I -B <installed-scripts>/migrate/compact.py adopt --job <ABS_JOB>
python3 -I -B <installed-scripts>/migrate/compact.py restore --job <ABS_JOB>
```

The context supplies the selected workspace basename, target, upcoming task IDs, observed boundary receipt, requested optional capabilities, date, and fixed run ID. A declaration is evidence to review, not permission by itself. `diagnose` is read-only; a false or unsubstantiated boundary remains pending. Each obligation retains its canonical source identity/hash, actual consumer/check and status: satisfied, pending, not-applicable or unknown. Required unknown facts block the affected adoption; an optional unknown stays a recommendation. Omit satisfied actions only with observed inventory proof. Consolidate actions only when effect, resolved paths, preconditions, consent source, consumer and required postconditions all agree; pre-stamp and post-stamp lint remain separate. Structural adapters receive the source methodology stamp and preserve it until the deliberate final stamp action.

`verify` checks the candidate's exact inventory, source and install identities, required manual decisions, pre-stamp and post-stamp captures, current lint rows 1–19, read-only upcoming-task readiness, restoration rehearsal, and a separate `semantic-review.json` receipt. Caller declarations, a successful stage, or a same-version stamp do not establish permission or acceptance. Missing required evidence remains pending or unknown and blocks adoption. The writing Check in the next task's brief runs only after a separately verified and completed adoption.

`adopt` is available only at an explicitly evidenced task boundary with known writer quiescence. It rechecks the original, candidate, catalog and installed artifact while holding the cooperating workspace locks, then records each same-filesystem rename phase. The original is preserved as the job's rollback source. Interrupted work reconciles only from matching recorded identities and physical hashes; conflicts and drift stop without overwriting. `restore` returns the exact checkpoint through a verified sibling stage only while the adopted workspace still matches its recorded post-adoption hash. Repeating a completed operation is a no-op.

All command paths are absolute; the installed route uses Python 3.10+ standard library and the copied installed artifact only. Commands return 0 when their own stage completes, 1 for pending, unknown, conflict or failed checks, and 2 for invalid input. They never install, download, archive a workspace, manufacture task status, copy consent, run a service, or perform a migration against an unselected source. The external checkpoint, preserved original backup, and explicit restore phase provide the rollback boundary. If the supported route is blocked or unsuitable, the owner may explicitly select a fresh workspace for remaining work and leave the old source unchanged; migration never chooses that alternative silently.

### Content link compatibility

The current placeholder and reference-staleness checkers read Markdown one directory below the workspace, outside the placeholder checker's explicit `legacy-*` snapshot exclusion. Those actual checker inputs retain the required-regular-file refusal: an uncited `raw/evidence.md` or `reference-docs/evidence.md` link is refused before native dispatch. A deeper dependency link such as `verification-records/task/baseline/node_modules/.bin/nanoid` remains inert retained content.

Nested retained evidence can contain symbolic links. Their inventory entries contain `type: symlink`, mode, `sha256: null`, and the exact UTF-8 target text. Complete tree identity includes that entry type and text; the regular-file projection remains a byte map for the existing adapters. Relative/internal, absolute/external, broken, chained, circular and directory targets are all opaque: the migrator does not resolve or open them or traverse a directory through them. Regular files independently present in the workspace are still inventoried under their own paths and existing read authority; a link grants no read authority.

Checkpoint, candidate and restoration copies retain links as links. Existing structural path mappings and legacy snapshots also carry the link entries, while their targets remain literal. Root-level links, control aliases and links needed as current regular checker inputs produce a path-specific refusal. A cited link is not silently treated as absent or read through its target. Unrepresentable UTF-8 paths/targets or a link mode the platform's no-follow interface cannot reproduce produce an explicit error, leaving the original unchanged. Logical path/type/target/mode identity is preserved; inode identity is not the persisted tree contract. Failed preparation can leave its private job evidence in place and does not authorize cleanup or adoption.

Regular-only inventory entries and hashes keep their existing form. A pending job stays bound to its recorded installation and catalog; a changed installation reports drift rather than reinterpreting that job. Recovery uses the matching original installation or a separately prepared fresh diagnosis at a safe boundary. Independent semantic admission, source/candidate freeze and the adoption-boundary requirements retain their existing meaning.

<a id="schema-keyed-migration"></a>
## Structure and current adoption

Read three independent facts: the observed workspace structure, its methodology stamp, and the
actual evidence of adopted guarantees. A missing or old stamp is not a reason to run a structural
rename, and a current stamp is not evidence that current obligations or optional capabilities hold.
The installed catalog's supported buckets are `pre-3`, `3`, `4`, `5`, and explicit `Gate: Lite`.
A schema-5 source skips satisfied renames with actual inventory proof; it still needs applicable
current-target guarantees. Historical checklists supply provenance, never a version-ordered route
or an instruction to fetch unshipped intermediate procedures.

Structural detection reads only top-level workspace files, ignores nested paths and every `legacy-*/` snapshot, and uses the board’s first unfenced `Schema:` declaration or the supported structure when that declaration is absent. A neighboring legacy snapshot cannot change the detected bucket. The `Methodology:` stamp never selects a structural adapter. The historical statement that 10.1.0 introduced no new schema applies only to that release and grants no general exemption from the observed-structure route.

| Observed source | Structural route |
|---|---|
| `pre-3`: top-level `board.md` has no unfenced `Schema:` declaration and has an unfenced header followed by a delimiter row, naming `Point` or `Task` and `Status` | installed `step_pre3_to_3`, then the supported `3` and `4` steps |
| `3`: top-level `board.md` declares `Schema: tackle-workspace/3` outside a fence | installed `step_3_to_4`, then `step_4_to_5` |
| `4`: top-level `task-board.md` declares `Schema: tackle-workspace/4` outside a fence | installed `step_4_to_5` |
| `5` | no structural adapter; diagnose current guarantees and capabilities |
| `Gate: Lite` on the first line of `plan.md` | preserve the Lite carrier and Gate; rename only existing old history/archive/usage names with collision checks |
| unknown, ambiguous, aliased, CRLF, or unclosed-fence source | diagnose and stop affected mutation; never infer a bucket, normalize history, downgrade or invent Ready |

<a id="migration-steps"></a>
The physical compact route calls each needed installed adapter through `schema.adopt`. It shares
one `schema` module with the adapters; their `transform` and `verify` receive
`schema.workspace_files` projections excluding `legacy-*/`, while adoption reassembles every
existing legacy directory unchanged and adds the exact original step snapshot. The adapter context
carries the validated date, run ID, source methodology and selected workspace name. Preserve the
recorded own path/P-to-T map across active artifacts; own forward links follow actual moves, while
external/history references remain preserved and unresolved ownership holds adoption. Do not call
a historical inline conversion recipe or pass a full legacy-bearing mapping directly to transform.

### Structural adapter contracts

Before each structural transform, retain a byte-identical snapshot of the non-legacy workspace exactly as that step read it in `legacy-<source-bucket>/`. Treat that pre-transform snapshot as read-only historical evidence. Carry every earlier `legacy-*/` directory forward unchanged; never feed snapshots back into the next transform as active workspace content.

The `pre-3` conversion accepts both P-ids and T-ids. Preserve the exact historical state mapping: 🔴 → Draft, 🟡 → In progress, ⏸ → Blocked, 🟢 → Complete, and ⚪ → Skipped, as described in [terminology.md](../terminology.md#states-and-observations). It never infers `Ready to run` or fresh verification from a legacy state.

The `3` layout conversion renames existing artifacts and maps P-ids to T-ids in file names and in `plan.md`, briefs, the board and its dependencies, reports, and usage rows. Preserve the usage ledger’s eight-column legacy or v2 lifecycle format; only its mapped ids change. Never rewrite `decisions.md` or `design-contract.md`. Keep the original `log.md` or `history.md` bytes and append the structural adoption entry exactly once; both names present is a rename-target collision. An interrupted, pinned task remains residue for review at its own boundary, never a silent rewrite or restart. An empty P→T map and absent `points/` are valid: existing `tasks/` and T-ids need no invented move; the board is still renamed and restamped, and any other old artifact actually present follows its defined rename.

The `4` conversion sets `Schema: tackle-workspace/5` without changing task statuses. For an existing `Ready to run` row, keep an existing `ready: ` citation with a nonempty reference. Default only an empty, `pending`, `—`, or `-` Verification cell to `ready: legacy /4 readiness`. Preserve any other old Verification text unchanged and report it as residue for review rather than overwrite a possible citation. A missing or nonstandard readiness citation must be resolved before adoption; preserving a Ready status does not invent readiness evidence.

Each structural adapter’s `verify(before, after)` is self-contained Python and does not shell out to the lint rows. It does not replace the compact route’s separate actual lint observations on the migrated copy; both pre-stamp and post-stamp captures remain required.

Check the target schema’s state vocabulary and Verification references before adopting a structural result. Schemas `3` and `4` use Draft, Ready to run, In progress, Checking, Complete, Blocked, Interrupted, Skipped and Unverifiable; Complete, Blocked and Unverifiable rows require exactly `reports/<id>-report.md` in Verification. The `4`→`5` path also checks the `ready: ` rule above. Pass `schema.workspace_files(before)` and `schema.workspace_files(after)` to each adapter’s self-contained Python `verify`, retaining its errors and residue for their required checks and manual review; do not pass the adopted legacy-bearing mapping or treat lint as that adapter oracle.

`errors` gate adoption: the wrong bucket after the step, a second `transform` that is not byte-identical, a board invariant, or an old artifact name left in the root. A rename-target collision is a separate, transform-time refusal, not a `verify` error; adoption never reaches `verify` for that colliding proposal. Keep these errors distinct from residue that needs its own manual review; neither an error nor unresolved required residue may be hidden by a successful wrapper.

Every structural step follows detect → transform → verify. A second call to that step’s transform on its own output must return byte-identical content and no new mapping or effects. This per-adapter idempotence is separate from recognition of a completed compact job as a no-op.

Maintain this guide, its migration scripts and their fixtures as one bridge that retains detection and transformation for every supported bucket above. The installed guide and scripts must remain sufficient for ordinary migration; fixtures verify that bridge and are not installed-route inputs or a reason to fetch unshipped intermediate procedures.

<a id="pre-migration-originals"></a>
Only the explicitly selected active source gets a candidate. Record the pinned procedure, current
source diagnostic, source/contract revisions, exact tree/type/mode/byte inventory, closed records,
usage/correction lineage and neighbor sentinel before effects. The source and immutable checkpoint
keep authority until separately validated cutover. Started or interrupted tasks retain procedure and
counters until their own deliberate boundary. Required receipt additions are only the exact
current-target baselines/errata, in their required order; there is no generic closed-history repair.
Preserve original hashes and legacy snapshots as provenance, never as current proof.

<a id="read-compatibility-promise"></a>
<a id="forward-only"></a>
## Forward-only readers and supported source boundaries

PLAN, RUN and STATUS run only bucket `5` or an explicitly selected Lite plan on current
`history.md` and `resource-usage.md` carriers. Migration and repairs require separate authorization.
Ambiguous structure, collisions, unknown required facts and CRLF/alias/fence diagnostics hold work;
never normalize original bytes silently, downgrade or infer a supported source below `pre-3`.
Closed work remains historical data; archive candidacy needs no upgrade, and archival requires separate authorization.

PLAN, RUN and STATUS refuse any other workspace with `migrate first` and point here, and lint rows 1, 2, 3, 5, 10, 11, 12, 14 and 17 print that refusal.

Before migration or an archive-related decision, read the required
[migration boundaries and capabilities](#migration-boundaries-and-capabilities).

<a id="migration-boundaries-and-capabilities"></a>
## Migration boundaries and capabilities

The current installed PLAN, RUN and STATUS readers run only bucket `5`, or an explicitly selected
Lite `plan.md` whose current history and usage carriers are `history.md` and `resource-usage.md`.
Other supported structures report `migrate first` and point to this route; reading that refusal or
asking STATUS never authorizes migration or repairs. Below `pre-3`, downgrade, ambiguous structure,
collisions and unknown required facts have no best-effort route. Closed work may be read as
historical data and requires no upgrade merely to become an archive candidate; any actual archive
is a separately authorized operation. A CRLF/alias/fence diagnostic remains a hold until its owner
resolves it in allowed scope, not permission to normalize original bytes silently.

PLAN, RUN and STATUS refuse any other workspace with `migrate first` and point here, and lint rows 1, 2, 3, 5, 10, 11, 12, 14 and 17 print that refusal.

Lint row 1’s placeholder scan skips every `legacy-*/` directory. That scan exclusion is distinct from the adapters’ legacy-excluding projections; neither exclusion makes old snapshots current evidence. See the row’s current contract in [lint-spec.md](lint-spec.md).

Required guarantees apply to selected open work; optional capabilities need an actual declared
upcoming consumer and their own applicability, consent and capability facts. Use the public name
[Judgement Layer](system-one.md#integration) while preserving TypeSafe System One/Jev backend, API and durable
`System One consent:` identifiers and old records. Migration consults no service, copies no answer,
allocates no consultation budget and never creates Ready, accepted closure or host-isolation proof.
Cooperating locks establish only their declared writer protocol; unknown capabilities remain
unknown and unavailable telemetry remains `n/a`.

<a id="migration-rollback"></a>
## Rollback

A failed `verify` leaves the original workspace active and unchanged. After adoption, `restore`
returns the exact pre-migration checkpoint through its verified sibling stage while the adopted
workspace still matches its recorded post-adoption inventory. The original backup and checkpoint
remain in the external job; history and legacy snapshots are preserved as evidence and are never
used as substitutes for a current restore receipt. Drift or a conflicting physical layout remains
pending for owner review.

## Direct adapter API compatibility

The installed `step_pre3_to_3.transform` API returns a `/3` board (or later) unchanged.

The installed `step_3_to_4.transform` API returns a `/4` board (or later) unchanged.

The installed `step_4_to_5.transform` API returns a `/5` board unchanged.

These existing API guarantees do not select a migration procedure. The compact route still invokes only the needed adapters through `schema.adopt`.

<a id="v84--v90-checklist"></a>
## Historical checklist provenance

The archived v8.4 → v9.0 checklist remains in the repository's `maintaining/migrations.md` as
historical provenance. The installed [catalog provenance](migration-catalog.json) retains its source
identities and obligations; the archived checklist is not an active procedure or an installed-route
input. Use the [compact migration route](#compact-migration) for a separately authorized current
migration, without fetching or replaying chronological checklists.
