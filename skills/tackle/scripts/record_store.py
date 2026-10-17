from pathlib import Path
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
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
