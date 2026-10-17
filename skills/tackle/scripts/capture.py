from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid


def sha(data):
    return hashlib.sha256(data).hexdigest()


def local(root, name):
    path = root / name
    path.resolve().relative_to(root.resolve())
    return path


def sync_dir(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish(path, data):
    temporary = path.parent / ('.write-' + uuid.uuid4().hex)
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
        sync_dir(path.parent)
    finally:
        temporary.unlink()


def put_object(store, data):
    digest = sha(data)
    path = store / 'objects' / digest
    if (store / 'objects').is_symlink() or path.is_symlink():
        raise ValueError('object pool must not redirect writes')
    if path.exists():
        if sha(path.read_bytes()) != digest:
            raise ValueError('corrupt existing object: ' + digest)
    else:
        publish(path, data)
    return digest


@contextmanager
def exclusive(store):
    lock = store / '.lock'
    lock.mkdir()
    (lock / 'owner.json').write_text(json.dumps(dict(pid=os.getpid(),
        started=datetime.now(timezone.utc).isoformat())), encoding='utf-8')
    try:
        yield
    except BaseException:
        raise
    else:
        (lock / 'owner.json').unlink()
        lock.rmdir()
        sync_dir(store)


def record_hashes(record):
    hashes = set(record.get('prior_objects', []))
    for key in ('inputs_before', 'inputs_after', 'artifacts', 'streams'):
        hashes.update(record.get(key, {}).values())
    hashes.update(record.get('prior_records', {}).values())
    if any(not isinstance(h, str) or not re.fullmatch('[0-9a-f]{64}', h) for h in hashes):
        raise ValueError('malformed content hash')
    return hashes


def read_record(observation, require_pass=False):
    observation = Path(observation)
    if observation.name.startswith('.pending-') or (observation / 'retired.json').exists():
        raise ValueError('record incomplete or retired')
    record = json.loads((observation / 'result.json').read_text())
    start = json.loads((observation / 'start.json').read_text())
    if not isinstance(record, dict) or not isinstance(start, dict):
        raise ValueError('raw record and start must be objects')
    before_fields = ('argv', 'cwd', 'capture_runtime', 'actor', 'model', 'effort',
                     'selectors', 'extra_inputs', 'membership_before', 'inputs_before',
                     'timeout_seconds', 'start')
    final_fields = ('child_exit', 'signal', 'end', 'streams', 'accepted',
                    'inputs_stable', 'artifacts_present', 'timeout', 'launch_error')
    if any(key not in start or key not in record for key in before_fields) or any(key not in record for key in final_fields):
        raise ValueError('incomplete raw check provenance')
    for key in ('cwd', 'capture_runtime', 'actor', 'model', 'effort', 'start', 'end'):
        if not isinstance(record[key], str) or not record[key].strip():
            raise ValueError('nonempty provenance string required: ' + key)
    if not Path(record['cwd']).is_absolute():
        raise ValueError('observed cwd must be absolute')
    for key in ('start', 'end'):
        if datetime.fromisoformat(record[key]).tzinfo is None:
            raise ValueError('observed clock must include timezone')
    if type(record['timeout_seconds']) not in (int, float) or record['timeout_seconds'] <= 0:
        raise ValueError('positive numeric timeout required')
    if not isinstance(record['extra_inputs'], list) or not all(isinstance(v, str) for v in record['extra_inputs']):
        raise ValueError('extra inputs must be a string list')
    if not isinstance(record['selectors'], list) or not all(isinstance(v, dict) and isinstance(v.get('glob'), str) and type(v.get('required')) is bool for v in record['selectors']):
        raise ValueError('declared selectors required')
    for key in ('accepted', 'timeout', 'inputs_stable', 'artifacts_present'):
        if type(record.get(key)) is not bool:
            raise ValueError('record boolean required: ' + key)
    for key in ('child_exit', 'signal'):
        if record.get(key) is not None and type(record[key]) is not int:
            raise ValueError('record integer or null required: ' + key)
    if record.get('signal') != (-record['child_exit'] if record.get('child_exit') is not None and record['child_exit'] < 0 else None):
        raise ValueError('inconsistent process signal')
    if record.get('launch_error') is not None and not isinstance(record['launch_error'], str):
        raise ValueError('launch error must be a string or null')
    if not isinstance(record.get('argv'), list) or not record['argv'] or not all(isinstance(v, str) for v in record['argv']):
        raise ValueError('argv must be a nonempty string list')
    for key in ('inputs_before', 'inputs_after', 'streams', 'artifacts', 'prior_records'):
        mapping = record.get(key, {})
        if not isinstance(mapping, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in mapping.items()):
            raise ValueError('record hash map required: ' + key)
    if not isinstance(record.get('prior_objects', []), list) or not all(isinstance(v, str) for v in record.get('prior_objects', [])):
        raise ValueError('prior objects must be a string list')
    for key in ('membership_before', 'membership_after'):
        mapping = record.get(key, {})
        if not isinstance(mapping, dict) or not all(isinstance(k, str) and isinstance(v, list) and all(isinstance(n, str) for n in v) for k, v in mapping.items()):
            raise ValueError('selector membership map required')
    if 'program' in record:
        program = record['program']
        if (not isinstance(program, dict) or set(program) != {'path', 'sha256'}
                or not isinstance(program['path'], str) or not Path(program['path']).is_absolute()
                or not isinstance(program['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', program['sha256'])):
            raise ValueError('program identity malformed')
        if Path(program['path']).is_file() and sha(Path(program['path']).read_bytes()) != program['sha256']:
            raise ValueError('program bytes changed since the record')
    if any(record.get(key) != value for key, value in start.items()):
        raise ValueError('record disagrees with immutable start provenance')
    if record.get('inputs_stable') and (record.get('inputs_before') != record.get('inputs_after')
            or record.get('membership_before') != record.get('membership_after')):
        raise ValueError('inconsistent input-stability claim')
    if record['artifacts_present'] and 'artifacts' not in record:
        raise ValueError('missing declared artifact result')
    for digest in record_hashes(record) - set(record['streams'].values()):
        if sha((observation / 'blobs' / digest).read_bytes()) != digest:
            raise ValueError('corrupt or missing input object')
    for name, digest in record['streams'].items():
        if name not in ('stdout.bin', 'stderr.bin') or sha((observation / name).read_bytes()) != digest:
            raise ValueError('corrupt stream')
    if set(record['streams']) != {'stdout.bin', 'stderr.bin'}:
        raise ValueError('missing stream')
    actual_pass = (record['child_exit'] == 0 and not record['timeout']
                   and record['launch_error'] is None and record['inputs_stable']
                   and record['artifacts_present'])
    if record['accepted'] != bool(actual_pass) or (require_pass and not actual_pass):
        raise ValueError('record does not establish a passed check')
    return record


def select(root, selectors, extra, store):
    files = set(extra)
    membership = {}
    def outside_store(path):
        try:
            path.resolve().relative_to(store.resolve())
            return False
        except ValueError:
            return True
    for item in selectors:
        pattern = item['glob']
        if Path(pattern).is_absolute() or '..' in Path(pattern).parts:
            raise ValueError('selector outside cwd')
        names = sorted(str(p.relative_to(root)) for p in root.glob(pattern)
                       if p.is_file() and (outside_store(p) or
                          (str(p.relative_to(root)) == pattern and not any(c in pattern for c in '*?['))))
        if item['required'] and not names:
            raise ValueError('missing required selector: ' + pattern)
        membership[pattern] = names
        files.update(names)
    data = {name: local(root, name).read_bytes() for name in sorted(files)}
    return membership, data


def capture(spec_path):
    root = Path.cwd().resolve()
    spec_path = local(root, spec_path)
    spec = json.loads(spec_path.read_text())
    argv = spec['argv']
    if not argv or not all(isinstance(x, str) for x in argv):
        raise ValueError('argv must be a nonempty string list')
    if 'workspace' in spec:
        workspace = local(root, spec['workspace']).resolve()
        if not workspace.is_dir():
            raise ValueError('authorized workspace must already exist')
        store = workspace / ('verification-records' if (workspace / 'task-board.md').is_file() else 'evidence')
        store.resolve().relative_to(workspace)
        destination = local(root, spec.get('destination', str(store)))
        destination.resolve().relative_to(store.resolve())
    else:
        store = destination = local(root, spec['destination']).resolve()
    extra = [str(spec_path.relative_to(root))]
    script = Path(__file__).resolve()
    program = None
    if root in script.parents:
        extra.append(str(script.relative_to(root)))
    else:
        program = dict(path=str(script), sha256=sha(script.read_bytes()))
    for arg in argv[1:]:
        if (root / arg).is_file():
            extra.append(str(local(root, arg).relative_to(root)))
    membership, data = select(root, spec['selectors'], extra, store)
    store.mkdir(parents=True, exist_ok=True)
    if (store / 'objects').is_symlink():
        raise ValueError('object pool must not redirect writes')
    (store / 'objects').mkdir(exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    with exclusive(store):
        identity = 'observation-' + uuid.uuid4().hex
        out = destination / ('.pending-' + identity)
        out.mkdir()
        (out / 'blobs').symlink_to(os.path.relpath(store / 'objects', out), target_is_directory=True)
        def snapshot(payload):
            return {name: put_object(store, content) for name, content in payload.items()}
        prior, prior_objects = {}, set()
        for name in spec.get('prior_records', []):
            source = local(root, name)
            source.resolve().relative_to(store.resolve())
            previous = read_record(source, require_pass=True)
            prior[name] = put_object(store, (source / 'result.json').read_bytes())
            for digest in record_hashes(previous):
                path = source / 'blobs' / digest
                if not path.exists():
                    stream = next((n for n, h in previous['streams'].items() if h == digest), None)
                    path = source / stream if stream else path
                payload = path.read_bytes()
                if sha(payload) != digest:
                    raise ValueError('corrupt prior record dependency')
                prior_objects.add(put_object(store, payload))
        record = dict(layout='shared-v1', event_id=identity, store=os.path.relpath(store, out),
                      argv=argv, cwd=str(root), capture_runtime=sys.version,
                      actor='n/a', model='n/a', effort='n/a', selectors=spec['selectors'],
                      extra_inputs=extra, membership_before=membership,
                      inputs_before=snapshot(data), timeout_seconds=spec['timeout_seconds'],
                      prior_records=prior, prior_objects=sorted(prior_objects),
                      start=datetime.now(timezone.utc).isoformat())
        if program is not None:
            record['program'] = program
        def write(name, value):
            publish(out / name, (json.dumps(value, indent=2) + '\n').encode('utf-8'))
        write('start.json', record)
        code, timeout, error = None, False, None
        with (out / 'stdout.bin').open('xb') as stdout, (out / 'stderr.bin').open('xb') as stderr:
            try:
                code = subprocess.run(argv, cwd=root, stdout=stdout, stderr=stderr,
                                      timeout=spec['timeout_seconds']).returncode
            except subprocess.TimeoutExpired:
                timeout = True
            except OSError as exc:
                error = str(exc)
            stdout.flush(); os.fsync(stdout.fileno())
            stderr.flush(); os.fsync(stderr.fileno())
        record.update(end=datetime.now(timezone.utc).isoformat(), child_exit=code,
                      signal=-code if code is not None and code < 0 else None,
                      timeout=timeout, launch_error=error)
        stable, artifacts_present = False, False
        try:
            after_membership, after_data = select(root, spec['selectors'], extra, store)
            record.update(membership_after=after_membership, inputs_after=snapshot(after_data))
            stable = membership == after_membership and record['inputs_before'] == record['inputs_after']
            record['artifacts'] = snapshot({name: local(root, name).read_bytes() for name in spec['artifacts']})
            artifacts_present = True
        except (OSError, ValueError) as exc:
            record['revision_error'] = str(exc)
        record['streams'] = snapshot({name: (out / name).read_bytes()
                                      for name in ('stdout.bin', 'stderr.bin')})
        for name, digest in record['streams'].items():
            (out / name).unlink()
            (out / name).symlink_to(os.path.relpath(store / 'objects' / digest, out))
        record.update(inputs_stable=stable, artifacts_present=artifacts_present,
                      accepted=code == 0 and not timeout and error is None and stable and artifacts_present)
        write('result.json', record)
        publish(out / 'receipt.md', b'# Check summary\n\n[Raw check record](result.json); [start](start.json); '
                b'[stdout](stdout.bin); [stderr](stderr.bin).\n\n'
                b'Immutable bytes: blobs/<sha256> aliases the initiative object pool. '
                b'Check [retirement status](retired.json) before reuse. Role finish: n/a. '
                b'Check passed is not deliverable accepted.\n')
        final = destination / identity
        out.rename(final)
        sync_dir(destination)
    print(final / 'receipt.md')
    return record['accepted']


if __name__ == '__main__':
    raise SystemExit(0 if capture(sys.argv[1]) else 1)
