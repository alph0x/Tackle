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
    if sorted(rows) != list(range(1, 18)):
        raise ValueError('expected exactly rows 1 through 17')
    return rows


def lint_verdict(row, record, stdout, stderr):
    if row not in range(1, 18):
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
    trusted_capture_sha256 = 'bcbcef803e188090fa5c60372cefe0cd9504b6babb1131c79ec7668301dee34c'
    def local(name):
        path = (root / name).resolve()
        path.relative_to(root)
        return path
    config = json.loads(local(config_path).read_text())
    source = Path(config['source']).read_bytes()
    rows = canonical_rows(source, config['source_sha256'], config['slug'])
    if 'capture_script' in config:
        capture_script = local(config['capture_script'])
    else:
        capture_script = Path(__file__).resolve().with_name('capture.py')
    if hashlib.sha256(capture_script.read_bytes().rstrip(b'\n')).hexdigest() != trusted_capture_sha256:
        raise ValueError('capture script revision changed')
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
    destination = workspace / ('verification-records' if (workspace / 'task-board.md').is_file() else 'evidence')
    destination.resolve().relative_to(workspace)
    destination.mkdir(parents=True, exist_ok=True)
    batch = Path(tempfile.mkdtemp(prefix='lint-', dir=destination))
    (batch / 'lint-spec.md').write_bytes(source)
    selectors = list(config['selectors'])
    for path in [config_path, batch / 'lint-spec.md', __file__, capture_script]:
        resolved = (root / path).resolve()
        if root in resolved.parents:
            selectors.append(dict(glob=str(resolved.relative_to(root)), required=True))
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
        result = subprocess.run([sys.executable, str(capture_script), str(spec_path)],
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
                   complete=len(results) == 17 and all(r['verdict'] in ('PASS', 'WARN') for r in results.values()))
    summary_path = batch / 'summary.json'
    summary_path.write_text(json.dumps(summary, indent=2))
    print(summary_path)
    return all(r['verdict'] in ('PASS', 'WARN') for r in results.values())


if __name__ == '__main__':
    raise SystemExit(0 if run_lint(sys.argv[1]) else 1)
