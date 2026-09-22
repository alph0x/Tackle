# Verification record lifecycle

Use this guide only when retained check bytes or history justify a store. Direct may use
sufficient actual tool records, and Focused may use its small explicit-workspace recipe. A complete
native export is equivalent only while all required bytes remain accessible for the retention
period. Hashes, mutable paths and potentially unavailable commits are not retained bytes.

## Scope and representation

New Coordinated captures explicitly name the already authorized `workspace`; the store is its `evidence/`
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

This recipe uses ordinary filesystem symlinks, same-filesystem atomic publication and directory
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

The optional standard-library recipe below is saved next to the Coordinated `capture.py`. It is
documentation, not an installed CLI. `preview` reads only. `maintain` requires the exact preview
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
index retired events. Readers check retirement before attempting to open retired raw metadata.

```python
from pathlib import Path
import json
import os
import re
import shutil
import tempfile
from capture import exclusive, local, publish, put_object, read_record, record_hashes, sha, sync_dir


def inventory(store):
    store = Path(store).resolve()
    return {str(p.relative_to(store)): sha(p.read_bytes())
            for p in sorted(store.rglob('*')) if p.is_file() and not p.is_symlink()
            and '.lock' not in p.relative_to(store).parts}


def record_paths(store):
    return sorted(p for p in store.rglob('observation-*') if p.is_dir() and not p.is_symlink())


def reference_versions(store, policy):
    names = policy.get('reference_sources')
    if not isinstance(names, list) or not names or len(names) != len(set(names)):
        raise ValueError('explicit authoritative reference sources required')
    result = {}
    for name in names:
        if not isinstance(name, str) or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('reference source must be workspace-relative')
        result[name] = sha(local(store.parent, name).read_bytes())
    return result


def retirement_marker(observation, record, reason, preview_hash):
    provenance = {key: record[key] for key in ('argv', 'cwd', 'capture_runtime', 'actor',
                                              'model', 'effort', 'start', 'end')}
    outcome = {key: record[key] for key in ('child_exit', 'signal', 'timeout', 'launch_error',
                                           'accepted', 'inputs_stable', 'artifacts_present')}
    return dict(state='data retired; not reusable', event_id=record.get('event_id', observation.name),
                reason=reason, preview_sha256=preview_hash, provenance=provenance,
                historical_outcome=outcome, streams=record['streams'],
                record_sha256=sha((observation / 'result.json').read_bytes()),
                start_sha256=sha((observation / 'start.json').read_bytes()),
                input_count=len(record['inputs_before']), retained_object_count=0,
                unavailable=['raw metadata', 'input/script/artifact bytes', 'original streams'])


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def preview(store, policy):
    store = Path(store).resolve()
    if (store / 'objects').is_symlink():
        raise ValueError('object pool redirects outside the selected representation')
    fields = ('current', 'pinned', 'active', 'resolved_failures', 'retire')
    if any(not isinstance(policy.get(k), list) for k in fields) or not policy.get('reason'):
        raise ValueError('complete retention policy and reason required')
    references = reference_versions(store, policy)
    selected = {k: {str(local(store, n).relative_to(store)) for n in policy[k]} for k in fields}
    records, protected, retired = {}, {}, set()
    metadata = []
    for path in record_paths(store):
        name = str(path.relative_to(store))
        if (path / 'retired.json').exists():
            tombstone = json.loads((path / 'retired.json').read_text())
            for filename, field in (('result.json', 'record_sha256'), ('start.json', 'start_sha256')):
                if (path / filename).exists():
                    if tombstone[field] != sha((path / filename).read_bytes()):
                        raise ValueError('retired history altered')
                    metadata.append(str((path / filename).relative_to(store)))
            retired.add(name)
            continue
        record = read_record(path)
        if record.get('layout') != 'shared-v1':
            raise ValueError('legacy record: export first, no in-place retirement')
        records[name] = record
        reasons = [k for k in ('current', 'pinned', 'active') if name in selected[k]]
        if not record['accepted'] and name not in selected['resolved_failures']:
            reasons.append('unresolved failure')
        if reasons:
            protected[name] = reasons
    known = set(records) | retired
    if (selected['current'] | selected['pinned'] | selected['active']) & retired:
        raise ValueError('live reference names retired data')
    pending = sorted(str(p.relative_to(store)) for p in store.rglob('.pending-*') if p.is_dir())
    for name in pending:
        protected[name] = ['interrupted capture: preserve recovery bytes']
    if pending:
        for name in records:
            protected.setdefault(name, []).append('interrupted capture dependencies not yet resolved')
        metadata = []
    for key in fields:
        if selected[key] - known - set(pending):
            raise ValueError('policy names missing record: ' + key)
    candidates = sorted(selected['retire'] & set(records) - set(protected))
    required = set()
    marker_bytes = 0
    for name, record in records.items():
        if name not in candidates:
            required.update(record_hashes(record))
        else:
            observation = local(store, name)
            metadata.extend(str((observation / f).relative_to(store)) for f in ('start.json', 'result.json'))
            marker_bytes += len(encoded(retirement_marker(observation, record, policy['reason'], '0' * 64)))
    objects = {p.name: p.stat().st_size for p in (store / 'objects').glob('*')
               if p.is_file() and not p.is_symlink() and re.fullmatch('[0-9a-f]{64}', p.name)}
    eligible = [] if pending else sorted(set(objects) - required)
    object_bytes = sum(objects[h] for h in eligible)
    metadata_bytes = sum(local(store, name).stat().st_size for name in metadata) - marker_bytes
    result = dict(scope=str(store), protected=protected, candidates=candidates,
                  reference_revisions=references, objects=eligible, metadata=sorted(metadata),
                  object_recoverable_bytes=object_bytes, metadata_recoverable_bytes=metadata_bytes,
                  recoverable_bytes=object_bytes + metadata_bytes, reason=policy['reason'],
                  total_object_bytes=sum(objects.values()), object_files=len(objects))
    identity = dict(policy=policy, inventory=inventory(store), result=result)
    result['fingerprint'] = sha(json.dumps(identity, sort_keys=True).encode())
    return result


def remove_object(path):
    path.unlink()


def remove_metadata(path):
    path.unlink()


def maintain(store, policy, expected_fingerprint, authorized=False):
    if not authorized:
        raise PermissionError('historical-data maintenance is not authorized')
    if policy.get('reference_writes_coordinated') is not True:
        raise PermissionError('reference writers must share the maintenance lease; preview only')
    store = Path(store).resolve()
    with exclusive(store):
        proposal = preview(store, policy)
        if proposal['fingerprint'] != expected_fingerprint:
            raise ValueError('store, policy or authoritative references changed: prepare a fresh preview')
        for name in proposal['candidates']:
            observation = local(store, name)
            marker = retirement_marker(observation, read_record(observation), policy['reason'], expected_fingerprint)
            publish(observation / 'retired.json', encoded(marker))
        for name in proposal['metadata']:
            path = local(store, name)
            remove_metadata(path)
            sync_dir(path.parent)
        for digest in proposal['objects']:
            remove_object(store / 'objects' / digest)
        sync_dir(store / 'objects')
    return proposal


def recover_lock(store, writers_stopped=False, authorized=False):
    if not writers_stopped or not authorized:
        raise PermissionError('confirm writer shutdown and scoped recovery authorization')
    lock = Path(store) / '.lock'
    if lock.exists():
        (lock / 'owner.json').unlink(missing_ok=True)
        lock.rmdir()
        sync_dir(Path(store))


def link_record(observation, store, record):
    (observation / 'blobs').symlink_to(os.path.relpath(store / 'objects', observation), target_is_directory=True)
    for name, digest in record['streams'].items():
        (observation / name).symlink_to(os.path.relpath(store / 'objects' / digest, observation))


def bundle_inventory(directory):
    directory = Path(directory).resolve()
    for p in directory.rglob('*'):
        if p.is_symlink():
            p.resolve(strict=True).relative_to(directory)
            if p.name not in ('blobs', 'stdout.bin', 'stderr.bin'):
                raise ValueError('unexpected export alias')
    return {str(p.relative_to(directory)): sha(p.read_bytes())
            for p in sorted(directory.rglob('*')) if p.is_file() and not p.is_symlink()
            and p.name != 'export.json'}


def verify_bundle(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'export.json').read_text())
    if bundle_inventory(directory) != manifest['files']:
        raise ValueError('incomplete or altered export')
    if not manifest['records']:
        raise ValueError('empty export')
    for name in manifest['records']:
        read_record(local(directory.resolve(), name))
    return manifest


def export_records(store, records, destination):
    store, destination = Path(store).resolve(), Path(destination).resolve()
    if destination.exists() or not records or len(set(records)) != len(records):
        raise ValueError('fresh destination and explicit unique records required')
    try:
        destination.relative_to(store)
    except ValueError:
        pass
    else:
        raise ValueError('export destination must be outside the source store')
    for name in records:
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('export record names must be relative, without traversal')
        read_record(local(store, name))
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.export-', dir=destination.parent))
    (stage / 'objects').mkdir()
    with exclusive(store):
        for name in records:
            source = local(store, name)
            record = read_record(source)
            target = local(stage, name)
            target.mkdir(parents=True)
            for filename in ('result.json', 'start.json', 'receipt.md'):
                publish(target / filename, (source / filename).read_bytes())
            for digest in record_hashes(record):
                blob = source / 'blobs' / digest
                if not blob.exists():
                    stream = next((n for n, h in record['streams'].items() if h == digest), None)
                    blob = source / stream if stream else blob
                payload = blob.read_bytes()
                if sha(payload) != digest:
                    raise ValueError('corrupt export object')
                put_object(stage, payload)
            link_record(target, stage, record)
        manifest = dict(format='verification-export-v1', records=records, files=bundle_inventory(stage))
        publish(stage / 'export.json', (json.dumps(manifest, indent=2) + '\n').encode())
        verify_bundle(stage)
        stage.rename(destination)
        sync_dir(destination.parent)
    return destination


def restore_records(bundle, destination):
    bundle, destination = Path(bundle).resolve(), Path(destination).resolve()
    manifest = verify_bundle(bundle)
    if destination.exists():
        raise ValueError('restore destination must be new; never overwrite history')
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.restore-', dir=destination.parent))
    for name in manifest['files']:
        target = local(stage, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        publish(target, local(bundle, name).read_bytes())
    for name in manifest['records']:
        observation = local(stage, name)
        record = json.loads((observation / 'result.json').read_text())
        link_record(observation, stage, record)
    publish(stage / 'export.json', (bundle / 'export.json').read_bytes())
    verify_bundle(stage)
    stage.rename(destination)
    sync_dir(destination.parent)
    return destination
```

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
