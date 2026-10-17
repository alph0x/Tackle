# Verification record lifecycle

Use this guide only when retained check bytes or history justify a store. Direct may use
sufficient actual tool records, and Focused may use its small explicit-workspace script. A complete
native export is equivalent only while all required bytes remain accessible for the retention
period. Hashes, mutable paths and potentially unavailable commits are not retained bytes.

## Scope and representation

New Coordinated captures explicitly name the already authorized `workspace`; the store is its `verification-records/`
directory. Keep its existing gitignore decision. Never include it in the installed package.
Every actual execution creates a separate immutable raw check record and check summary, even when
commands and inputs match. `objects/<sha256>` stores shared input/script/artifact/stream bytes.
The legacy `observation-*/blobs/<sha256>`, `stdout.bin`, `stderr.bin`, `result.json` and `receipt.md`
paths remain readable through relative aliases. No mutable working file is hardlinked. New
objects are copied, hashed, privately written and synced before atomic publication. Existing
objects are verified before reuse. Records appear under their final name only after publication.

Broad selectors exclude the store, including maintenance files. Called scripts and config are
still captured explicitly. A `prior_records` list names bounded complete successful records;
the capture snapshots their raw JSON and the transitive byte closure into the new record. It
never selects a whole store recursively. Decide dependency completeness from the actual check.
Reuse also requires current input content, selector membership, configuration, interfaces,
runtime and freshness windows; integrity alone does not establish current applicability.

The scripts use ordinary filesystem symlinks, same-filesystem atomic publication and directory
sync. Confirm those capabilities on the actual filesystem or use an equivalent native export;
do not silently replace a failed durability operation with a success claim. Capture and
maintenance share an exclusive `.lock` lease. A competing writer stops with a visible busy
result. An unexpected exception leaves its lease and `.pending-*` directory intact, with partial
streams available. Before `recover_lock`, establish through the harness that all writers have
stopped; a missing PID or elapsed time alone is insufficient. Recovery removes only the lease,
never partial evidence. Complete the affected check again after resolving the cause.

## References, policy and maintenance

Keep one initiative policy alongside the obligation index. Its lists are paths relative to this
store: `current` for live obligations and retained deliverables, `pinned` for audits, `active` for
work/recovery, `resolved_failures` for failures whose diagnosis and counters are preserved
elsewhere, and `retire` for specifically selected superseded historical results. `reference_sources` names
the current authoritative obligation/pin/budget source files relative to the workspace; include
the authoritative dependency map that determines membership. The preview records their hashes
and maintenance rechecks them under the store lease. Changed sources invalidate a preview even
when the caller supplies an old policy. All cooperating edits to those references must share
the store lease; set `reference_writes_coordinated: true` only after establishing that practice.
If reference writers cannot coordinate, prepare a preview but do not run deletion. Include a
concrete `reason`. Current, pinned and active references require bytes. Ordinary historical log
mentions preserve an event's existence and outcome but do not permanently pin all its bytes.
Failed results stay protected unless explicitly resolved by policy; partial captures protect
all currently stored objects conservatively. Moving a log entry into an archive never resolves
a failure or authorizes retirement.

Choose retention criteria and optional byte/file warning budgets from measured growth and
required coverage. There is no universal age or run-count cutoff. An authorized policy can
select superseded data at a milestone or growth trigger. Status can report size and recoverable
bytes, but remains read-only. A warning does not block work by default. A chosen hard limit or
lack of disk space stops only the affected capture: keep prior data and complete streams; do
not truncate them or substitute summaries. Report the constraint and its affected obligation.

Prepare a read-only preview with scope, protected references/reasons, candidates, object hashes
and recoverable logical bytes. Confirm the current obligation/pin lists are complete before
using a policy. Preview is not authorization: historical user data needs explicit authorization
or an already authorized initiative policy. Implementation/testing may use disposable fixtures.
An authorized RUN can maintain its own policy-covered store without repeated per-file questions.
Planning, STATUS and vocabulary updates do not authorize deletion.

Prefer an equivalent harness capability. With the owner's explicit authorization, the optional
standard-library [record script](../../scripts/record_store.py) is imported from `<skill>/scripts/`
(put that folder first on `sys.path`; it imports the Coordinated [`capture.py`](../../scripts/capture.py)
beside it). It is a module with no command line, not an installed CLI. Its functions are
`inventory`, `record_paths`, `reference_versions`, `preview`, `maintain`, `recover_lock`, `link_record`,
`bundle_inventory`, `verify_bundle`, `export_records` and `restore_records`. `preview` reads only. `maintain` requires the exact preview
fingerprint and explicit authorized policy use; it rechecks under the shared lease. It first publishes
an immutable compact retirement tombstone with event identity, exact command, observed clocks,
cwd/runtime/actor facts, historical outcome, stream hashes and original raw-record/start hashes.
It then retires the bulky start/result metadata and unreferenced pool objects. The original log
entries and order stay untouched; the tombstone explicitly marks original bytes unavailable.
The check summary and tombstone remain discoverable at the original event path. A current
consumer retaining a prior-record snapshot still pins that snapshot and its required objects. A retired record cannot become current proof again. Preview reports object recovery and net metadata recovery after tombstone cost. A crash
between tombstones and metadata/object deletion leaves excess bytes, not broken live references; recovery and a
new preview can safely repeat maintenance. Unknown files and all paths outside the store remain
untouched. Legacy stores can be read and exported; in-place deletion/compaction is restricted to
`shared-v1` records. Prepare, verify and switch a new export representation before separately
authorizing removal of old duplicates. Event directories, not the presence of bulky result files,
index retired events. Readers check retirement before attempting to open retired raw metadata; import or run the
script only with the owner's explicit authorization ([script consent](../../scripts/README.md#consent)).

## Portability, migration and delivery

`read_record(path)` verifies complete actual records, including unsuccessful historical checks;
`read_record(path, require_pass=True)` additionally requires child acceptance. Retired, incomplete,
missing or corrupt data always fails. These integrity checks do not replace current-input and
semantic acceptance checks. Existing `observation/blobs/<hash>` records remain supported.
Small legacy check summaries without saved input bytes remain valid only for the narrower evidence they
actually retained; export cannot manufacture missing snapshots.

`export_records(store, names, new_directory)` includes selected original metadata and every
required object, including prior-record snapshots. `restore_records(bundle, new_directory)`
verifies the closed inventory and publishes into a fresh destination. It never depends on a
machine cache, the original repository, absolute provenance paths or another store. Include
these verified bundles with the current-view/context sources needed by a portable handoff.
Keep original IDs and provenance even when physical location changes. A verified export is a
reversible compaction representation; removing the previous representation still needs the
applicable retention authorization and a recoverable pointer switch.

Report measured logical bytes, unique hashes, file/alias counts, and capture/maintenance costs
separately. Allocated disk usage, agent reads and billed tokens are different metrics. Include
failed and interrupted records in measurement; do not count unavailable telemetry as zero.
