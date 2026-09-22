<a id="full--executable-observations-and-bounded-closure"></a>
# Coordinated — verification records and bounded completion

Use an equivalent complete harness export when available. Otherwise save this Python 3 recipe
inside the authorized workspace before running checks. This is an optional documentation recipe,
not an installed runner or a new product dependency. This is Coordinated's direct-capture entry from
`run.md` and `evidence-capture.md`; Direct and Focused keep their own procedures.

## Establish the boundary first

Record allowed writes, protected fixtures and the actual harness policy. Configure native
filesystem restrictions for shell children as well as patch tools; a container protects its host,
not necessarily the task's Touches inside the container. Put script revisions, evidence and
TMPDIR under authorized paths. TMPDIR routes cooperative tools; it does not prohibit an explicit
`/tmp/name`, a sibling path or a symlink escape. Before the first PLAN write or check, use disposable sentinels to
prove an allowed write succeeds and outside/protected writes are denied. Never probe by changing
a real protected file. Preserve the observed policy and results. If effective confinement is a
required capability and is unavailable, block that scope; do not disable it or claim that an
instruction/audit enforces it. Post-run hashes remain necessary for protected expectations.

## Prepare once, then capture

During PLAN, select a capture destination, exact command and input selectors for each obligation.
Include source, **all selected tests including additive files**, contract, input data, config and
dependencies. Selectors come from the acceptance/check's actual dependency surface, not merely
task Touches. Review completeness before execution; no generic helper can infer every dynamic
input. A glob records its membership, including an intentionally optional empty match; a required
selector matching nothing is an error. Do not select credentials, home directories or generated
evidence. Save compound scripts before invoking them and include every called script/config;
the recipe automatically includes itself, its JSON specification and existing file arguments after argv[0]. The executable/runtime is
observed separately; absolute interpreter paths are valid. External read-only scripts need an
authorized local snapshot or equivalent harness capture; do not widen write permissions to copy them.
A copied module loaded by an inline interpreter still needs its selector.

The recipe below saves exact input bytes once per initiative in immutable content-addressed
objects, with compatible per-record blob aliases, binary streams and actual
child status. It does not decide whether a shell wrapper's logic is sound. Prefer direct runner
argv; check each required child in compound scripts. A printed PASS or a trailing successful
command must never mask failure. A script correction gets a new verification record; previous snapshots
are never replaced. The recipe is for foreground children that join their own children. It cannot
certify process-tree shutdown: on timeout, interrupt or background work, use the harness to stop
all writers and record that confirmation before closing evidence.

Save the block as a workspace-local `capture.py`. Invoke it with one JSON specification path,
for example `python3 docs/plans/demo/capture.py docs/plans/demo/product-check.json`. The JSON has
`argv`, `selectors` (objects with `glob` and `required`), `artifacts` (relative file names),
`workspace` (the already authorized initiative directory) and `timeout_seconds`. Optional
`destination` must stay inside that workspace's `evidence/` store; the default is the store itself.
Optional `prior_records` names exact prior record directories inside this same store, never a
glob. New specifications must declare workspace. Legacy specifications with only `destination`
still use that explicitly selected directory as their storage root; do not generate new implicit
cwd destinations. See [record lifecycle](record-lifecycle.md) for retention/export and compatibility. Use an authorized absolute cwd as the
process cwd; paths resolve from it. For example selectors can cover `src/**/*.py`, `test*.py`,
`SPEC.md`, and the exact validation/config files. Adapt to the real repository, not this example.

```python
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
        store = workspace / 'evidence'
        store.resolve().relative_to(workspace)
        destination = local(root, spec.get('destination', str(store)))
        destination.resolve().relative_to(store.resolve())
    else:
        store = destination = local(root, spec['destination']).resolve()
    extra = [str(spec_path.relative_to(root)), str(Path(__file__).resolve().relative_to(root))]
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
```

Before reusing a verification record, reject any retirement tombstone, then open its result and verify stream/blob hashes, relevant final input
hashes **and selector membership**, produced artifacts and the actual successful child result.
Missing or altered bytes invalidate the record. `read_record` checks retained bytes and actual
child status for both old per-observation blobs and the shared layout; it does not infer that
current source/configuration/runtime or semantic coverage is unchanged. A start without a complete result is
incomplete. Retain the old record and run only dependent checks again. Hashes identify bytes;
review of the declared selectors establishes whether those bytes cover the obligation.

## Execute canonical lint faithfully

Run all 16 rows during PLAN before Ready. Read the current `lint-spec.md`; extract the literal
command cell of each numbered row, respecting its backtick delimiter (some use two or four), and
substitute only a validated single-component slug (`[a-z0-9][a-z0-9.-]*`). Save the canonical source snapshot/hash,
row number, command bytes and pass condition. Reject missing/duplicate rows, malformed cells and
an unexpected source revision. Do not invent an equivalent short validator, replace a row with
`true`, or paste the table into an interpolated shell string. Execute each saved command using
`['sh', saved_script]`; retain a separate raw check record for each row. The snapshot of the saved
script must match the extracted bytes. A script's trailing `printf` cannot supply the row result.

For an existing orchestrator, these two pure Python functions provide exact extraction and row
interpretation. Save the extracted UTF-8 bytes verbatim as each script; capture that saved script
with the recipe above. Supply the canonical source hash recorded at preflight, not a hash silently
recomputed after a change. Check that all 16 returned rows are scheduled before initial execution.
Each result carries `row`, `command_sha256`, `source_sha256`, raw check record path and verdict;
build the index from those records. Equivalent harness automation is valid.

Use the connected path below when equivalent harness automation is absent: save this second
block as workspace-local `lint.py` beside `capture.py`, then run `python3 <lint.py> <lint.json>`.
The JSON specifies `source` (current lint-spec path), preflight `source_sha256`, `slug`,
`capture_script`, `selectors`, `workspace` and `timeout_seconds`. The workspace must already
exist. Legacy `destination`-only configurations are still accepted as an explicit workspace
location; newly generated configurations name workspace. Optional `rows` selects
affected checks; omission runs all 16. Initial PLAN still requires all 16. Include citation targets
and other actual dependencies in selectors. An authorized read-only source outside cwd is read
and hash-verified, then snapshotted locally; helpers and outputs remain inside cwd. The recipe extracts, saves, captures and verifies
each command itself; do not manually transcribe command cells into another script. A custom
composition remains possible, but compare its actual captured script bytes with the extracted
canonical bytes before claiming canonical coverage. A source/command mismatch or absent script
snapshot is ERROR even if the command exited zero. A subset score is never a full-plan approval.

```python
import hashlib
import re
from pathlib import Path
import json
import subprocess
import sys
import tempfile


def canonical_rows(source, expected_sha256, slug):
    if hashlib.sha256(source).hexdigest() != expected_sha256:
        raise ValueError('canonical source revision changed')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]*', slug):
        raise ValueError('invalid slug')
    rows = {}
    for line in source.decode('utf-8').splitlines():
        if not re.match(r'^\| [0-9]+ ·', line):
            continue
        head, cell, condition = line.split(' | ', 2)
        number = int(head.split(' ·', 1)[0][2:])
        match = re.fullmatch(r'(`+)(.*?)\1', cell)
        if number in rows or not match or not condition.endswith(' |'):
            raise ValueError('duplicate or malformed row')
        command = match[2]
        # Markdown code spans with padding remove one surrounding space.
        if command.startswith(' ') and command.endswith(' ') and command.strip():
            command = command[1:-1]
        command = command.replace('<slug>', slug).encode('utf-8')
        rows[number] = dict(command=command, condition=condition[:-2],
                            command_sha256=hashlib.sha256(command).hexdigest())
    if sorted(rows) != list(range(1, 17)):
        raise ValueError('expected exactly rows 1 through 16')
    return rows


def lint_verdict(row, record, stdout, stderr):
    if row not in range(1, 17):
        raise ValueError('unknown row')
    code = record['child_exit']
    if type(code) is not int or any(type(record.get(key)) is not bool
            for key in ('timeout', 'inputs_stable', 'artifacts_present')):
        return 'ERROR'
    allowed = (0, 1) if row in (5, 6, 11, 15, 16) else (0,)
    if (record['timeout'] or record['launch_error'] or record['signal'] is not None
            or stderr or code not in allowed or not record['inputs_stable']
            or not record['artifacts_present']):
        return 'ERROR'
    if stdout:
        return 'WARN' if row in (8, 13, 15) else 'FAIL'
    if (row == 5 and code != 1) or (row != 5 and row != 15 and code != 0):
        return 'ERROR'
    return 'PASS'


def captured_lint_verdict(source, expected_sha256, slug, row, script, record, observation):
    try:
        if (observation / 'retired.json').exists() or observation.name.startswith('.pending-'):
            return 'ERROR'
        if type(record.get('accepted')) is not bool:
            return 'ERROR'
        expected = canonical_rows(source, expected_sha256, slug)[row]['command']
        if record['argv'] != ['sh', script]:
            return 'ERROR'
        digest = record['inputs_before'][script]
        if not re.fullmatch(r'[0-9a-f]{64}', digest) or record['inputs_after'][script] != digest:
            return 'ERROR'
        actual = (observation / 'blobs' / digest).read_bytes()
        if hashlib.sha256(actual).hexdigest() != digest or actual not in (expected, expected + b'\n'):
            return 'ERROR'
        required = set(record.get('prior_objects', []))
        for key in ('inputs_before', 'inputs_after', 'artifacts', 'prior_records'):
            required.update(record.get(key, {}).values())
        for fingerprint in required:
            if not re.fullmatch(r'[0-9a-f]{64}', fingerprint):
                return 'ERROR'
            if hashlib.sha256((observation / 'blobs' / fingerprint).read_bytes()).hexdigest() != fingerprint:
                return 'ERROR'
        streams = [(observation / name).read_bytes() for name in ['stdout.bin', 'stderr.bin']]
        for name, data in zip(['stdout.bin', 'stderr.bin'], streams):
            if hashlib.sha256(data).hexdigest() != record['streams'][name]:
                return 'ERROR'
        return lint_verdict(row, record, *streams)
    except (KeyError, OSError, ValueError, TypeError):
        return 'ERROR'


def run_lint(config_path):
    root = Path.cwd().resolve()
    def local(name):
        path = (root / name).resolve()
        path.relative_to(root)
        return path
    config = json.loads(local(config_path).read_text())
    source = Path(config['source']).read_bytes()
    rows = canonical_rows(source, config['source_sha256'], config['slug'])
    selected = config.get('rows', list(rows))
    if not selected or len(set(selected)) != len(selected) or any(n not in rows for n in selected):
        raise ValueError('invalid selected rows')
    if 'workspace' in config:
        workspace = local(config['workspace']).resolve()
        if not workspace.is_dir():
            raise ValueError('authorized workspace must already exist')
    else:
        workspace = local(config['destination']).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
    destination = workspace / 'evidence'
    destination.resolve().relative_to(workspace)
    destination.mkdir(parents=True, exist_ok=True)
    batch = Path(tempfile.mkdtemp(prefix='lint-', dir=destination))
    (batch / 'lint-spec.md').write_bytes(source)
    selectors = list(config['selectors'])
    for path in [config_path, batch / 'lint-spec.md', __file__, config['capture_script']]:
        selectors.append(dict(glob=str(local(path).relative_to(root)), required=True))
    results = {}
    for number in selected:
        script_path = batch / ('row-%02d.sh' % number)
        script_path.write_bytes(rows[number]['command'])
        script = str(script_path.relative_to(root))
        spec = dict(workspace=str(workspace.relative_to(root)), argv=['sh', script], selectors=selectors, artifacts=[],
                    destination=str((batch / ('row-%02d' % number)).relative_to(root)),
                    timeout_seconds=config['timeout_seconds'])
        spec_path = batch / ('row-%02d.json' % number)
        spec_path.write_text(json.dumps(spec, indent=2))
        result = subprocess.run([sys.executable, str(local(config['capture_script'])), str(spec_path)],
                                cwd=root, capture_output=True)
        (batch / ('capture-%02d.stdout' % number)).write_bytes(result.stdout)
        (batch / ('capture-%02d.stderr' % number)).write_bytes(result.stderr)
        observation = None
        verdict = 'ERROR'
        try:
            if not result.stdout.strip():
                raise ValueError('missing capture receipt')
            receipt = local(result.stdout.decode().strip())
            receipt.relative_to(batch)
            observation = receipt.parent
            record = json.loads((observation / 'result.json').read_text())
            if result.returncode in (0, 1) and not result.stderr:
                verdict = captured_lint_verdict(source, config['source_sha256'], config['slug'],
                                               number, script, record, observation)
        except (OSError, ValueError, UnicodeError):
            pass
        results[number] = dict(row=number, source_sha256=config['source_sha256'],
                               command_sha256=rows[number]['command_sha256'], verdict=verdict,
                               capture_exit=result.returncode,
                               observation=str(observation.relative_to(root)) if observation else None)
    summary = dict(rows=results, total=len(results),
                   passed=sum(r['verdict'] == 'PASS' for r in results.values()),
                   complete=len(results) == 16 and all(r['verdict'] in ('PASS', 'WARN') for r in results.values()))
    summary_path = batch / 'summary.json'
    summary_path.write_text(json.dumps(summary, indent=2))
    print(summary_path)
    return all(r['verdict'] in ('PASS', 'WARN') for r in results.values())


if __name__ == '__main__':
    raise SystemExit(0 if run_lint(sys.argv[1]) else 1)
```

Interpret **stdout, stderr and real exit together** using the canonical condition:

| Rows | Empty-output pass | Findings | Execution error |
|---|---|---|---|
| 5 | stdout/stderr empty, exit 1 | stdout with grep exit 0: FAIL | stderr, timeout, signal or other exit: ERROR |
| 15 | stdout/stderr empty, exit 0 or 1 | stdout: WARN if exit 0 or 1 and no stderr | stderr, timeout, signal or other exit: ERROR |
| 8, 13 | stdout/stderr empty, exit 0 | stdout with exit 0: WARN | stderr, timeout, signal or nonzero exit: ERROR |
| 6, 11, 16 | stdout/stderr empty, exit 0 | stdout with exit 0 or 1: FAIL | stderr, timeout, signal, unexpected exit or empty-output exit 1: ERROR |
| All other rows | stdout/stderr empty, exit 0 | stdout with exit 0: FAIL | stderr, timeout, signal or nonzero exit: ERROR |

Report every finding verbatim, including findings printed with exit zero. WARN keeps its existing
nonblocking severity; ERROR means the row was not validly observed, never PASS. Preserve failures
and do not let wrapper success certify them. The generic capture recipe's `accepted` means a captured zero exit with stable inputs and present
required artifacts; lint's row-specific verdict uses its captured fields, not that generic boolean.
The score is computed from these records, never a constant or a count of launched commands.

## Close against one obligation index

Before RUN, prepare the obligation → command → input selectors → evidence destination mapping,
including required reviews, runtimes, integration/global coverage and packaging. Reuse PLAN's
preparation and canonical lint records after checking their revisions. After product checks,
write the reports, board/log/usage updates and final output references once, then validate their
affected rows. Link a captured verification record from the ledger/report instead of transcribing it.
A verification record may satisfy several obligations when its actual coverage does; do not rerun a
passing product suite merely to fill separate target, integration and global headings.

Use this dependency map conservatively when selecting affected lint rows:

| Changed input | Invalidated rows |
|---|---|
| Workspace top-level or one-level Markdown content/membership | 1 |
| Points or plan, including id/dependency membership | 2, 5; Points also 7, 9, 12 |
| Board | 2, 3, 10, 11, 14; every initiative board also 8 |
| Points/plan/reference citations or their target bytes | 4 |
| Log or log-archive content/membership | 6; log also 13 |
| Design contract or decisions | 7 |
| Any initiative's Points/Touches membership/content | 8 |
| Usage membership/content | 11, 16 |
| Closure report membership | 14 |
| Workspace AGENTS | 13, 15 |
| Reference-doc membership/content, current time crossing freshness window | 15 |
| Lint source, command interpreter/tools or policy relevant to its execution | All affected rows; all 16 if impact cannot be established |

Union dependencies; the same edit can match several rows. Track glob membership, citation target
files and time as well as hashes of known files. Do not reuse row 15 without a verified expiry
boundary; rerun this inexpensive row when freshness is uncertain. Unknown dependencies invalidate
the potentially affected records. Product checks have their own input map.

The final index still accounts for all 16 canonical rows, distinguishing fresh executions from
reused current records; report `lint: N/16 checks passed` from their actual pass conditions
(and any additional workspace rows in the denominator). This is a current coverage summary;
also report how many rows were executed versus reused. A selection of custom checks is not 16/16.
The release sweep still executes every prescribed row and gate; this reuse rule does not waive it.

Finish with complete only when all mandatory obligations have current accessible evidence.
Otherwise finish with the bounded blocker packet from `run.md`, preserving completed unaffected
work and the unresolved obligation. Budget exhaustion ends with an honest incomplete/blocked
handoff. It does not justify changing acceptance, omitting global coverage or another unbounded
bookkeeping loop. Correct an observed failure within the existing recovery budget; do not restart
unchanged preparation merely because a new heading or session begins.

Explicit Focused applicability uses the first-line marker and shape checks in `lint-spec.md`, not
absence of Coordinated files. Include plan.md in selectors for every row: route changes invalidate all
applicability records. During release, execute all sixteen commands even for Focused and accept
Coordinated-only checked skips only after row 1 passes. This does not waive selected global acceptance.
