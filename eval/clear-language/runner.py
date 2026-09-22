"""Stage a sealed paired cohort; explicit isolated execution, never implicit spend."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASELINE = '61f9b4b142ba83a6a502cf833dd6b9b43e556253'
SMOKE = ['bounded-en', 'active-status-es', 'blocker-en', 'memory-es', 'reuse-en', 'integrated-es']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())


def document(path, value):
    write(path, json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def hashes(directory):
    found = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError('symlinks are not participant inputs: ' + str(path))
        if path.is_file():
            found[str(path.relative_to(directory))] = digest(path.read_bytes())
    return found


def installation(root):
    paths = [root / 'SKILL.md'] + sorted((root / 'references').rglob('*'))
    if any(path.is_symlink() for path in paths):
        raise ValueError('installation symlink rejected')
    return {str(path.relative_to(root)): path.read_bytes() for path in paths if path.is_file()}


def baseline_installation():
    result = subprocess.run(['git', 'archive', BASELINE, 'SKILL.md', 'references'], cwd=ROOT, capture_output=True, check=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
        return {item.name: archive.extractfile(item).read() for item in archive.getmembers() if item.isfile()}


def prepare(destination, baseline, candidate, cases, oracle, protocol, selected, seed=1):
    ids = {case['id'] for case in cases}
    if not selected or len(set(selected)) != len(selected) or not set(selected) <= ids:
        raise ValueError('selected cases must be nonempty, unique and registered')
    if set(oracle) != ids:
        raise ValueError('oracle inventory does not match cases')
    if len(ids) != len(cases) or not baseline.get('SKILL.md') or not candidate.get('SKILL.md'):
        raise ValueError('unique case IDs and both complete entry files are required')
    destination.mkdir(parents=True, exist_ok=False)
    private = destination / 'private'
    document(private / 'oracle.json', oracle)
    write(private / 'protocol.md', protocol)
    write(private / 'runner.py', Path(__file__).read_bytes())
    for arm, sources in (('baseline', baseline), ('candidate', candidate)):
        for name, data in sources.items():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts or (name != 'SKILL.md' and not name.startswith('references/')):
                raise ValueError('invalid installation input')
            write(destination / 'installations' / arm / name, data)
    order = []
    rng = random.Random(seed)
    for case in cases:
        if case['id'] not in selected:
            continue
        case_files = dict(case['files'])
        if case['id'] == 'reuse-en':
            with tempfile.TemporaryDirectory(prefix='tackle-reuse-fixture-') as temporary:
                initial = Path(temporary)
                for name, data in case_files.items():
                    write(initial / name, data)
                command = [sys.executable, 'check_format.py']
                started = datetime.now(timezone.utc).isoformat()
                child = subprocess.run(command, cwd=initial, capture_output=True)
                ended = datetime.now(timezone.utc).isoformat()
                if child.returncode or child.stdout != case_files['check.stdout'].encode() or child.stderr:
                    raise ValueError('prior verification fixture did not produce its declared actual result')
                case_files['fixture-observation.json'] = json.dumps({
                    'command': command, 'cwd': str(initial), 'start': started, 'end': ended,
                    'runtime': platform.platform(), 'exit': child.returncode,
                    'stdout_sha256': digest(child.stdout), 'stderr_sha256': digest(child.stderr),
                    'inputs': hashes(initial), 'relocation': 'These exact retained input/stream bytes are copied to /work.'}, indent=2) + '\n'
        relative = 'participants/' + case['id']
        participant = destination / relative
        write(participant / 'fixture/TASK.md', case['request'] + '\n')
        for name, data in case_files.items():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('invalid participant file')
            write(participant / 'initial' / name, data)
        arms = ['baseline', 'candidate']
        rng.shuffle(arms)
        for arm in arms:
            order.append({'case': case['id'], 'arm': arm, 'path': relative})
    manifest = {'cohort': 'CLEAR-EVAL-1', 'status': 'PENDING', 'baseline_commit': BASELINE,
                'seed': seed, 'selected': selected, 'order': order,
                'budget': {'wall_seconds': 600, 'task_correction_cycles': 3, 'unowned_integration_cycles': 2},
                'created': datetime.now(timezone.utc).isoformat(), 'files': hashes(destination)}
    document(destination / 'manifest.json', manifest)
    return digest((destination / 'manifest.json').read_bytes())


def verify(cohort, seal):
    manifest_path = cohort / 'manifest.json'
    if digest(manifest_path.read_bytes()) != seal:
        raise ValueError('cohort seal changed')
    manifest = json.loads(manifest_path.read_text())
    actual = hashes(cohort)
    actual.pop('manifest.json')
    if actual != manifest['files']:
        raise ValueError('cohort input inventory or content changed')
    return manifest


def base_command(image, fixture, method, work, name):
    return ['docker', 'run', '--rm', '--name', name, '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp', '--tmpfs', '/root',
            '--mount', f'type=bind,src={fixture.resolve()},dst=/fixture,readonly',
            '--mount', f'type=bind,src={method.resolve()},dst=/method,readonly',
            '--mount', f'type=bind,src={work.resolve()},dst=/work', '--workdir', '/work']


def preflight(image, fixture, method, work):
    if not image.startswith('sha256:') or len(image) != 71:
        return {'available': False, 'reason': 'a pinned sha256 image is required'}
    inspect = ['docker', 'image', 'inspect', image, '--format', '{{.Id}}']
    try:
        result = subprocess.run(inspect, capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'available': False, 'reason': str(error), 'command': inspect}
    if result.returncode or result.stdout.decode().strip() != image:
        return {'available': False, 'reason': 'pinned local image unavailable', 'command': inspect,
                'exit': result.returncode, 'stderr': result.stderr.decode(errors='replace')}
    name = 'tackle-probe-' + uuid.uuid4().hex
    command = base_command(image, fixture, method, work, name) + ['--network', 'none', image, 'sh', '-c',
        'test -r /method/SKILL.md && test -r /fixture/TASK.md && '
        '! test -e /private/oracle.json && ! test -e /oracle.json && '
        '! test -e /Users/alph0x/Developer/Tackle && '
        'touch /work/.isolation-probe && ! touch /fixture/.probe && ! touch /method/.probe && ! touch /outside-probe']
    try:
        result = subprocess.run(command, capture_output=True, timeout=30)
        return {'available': result.returncode == 0, 'command': command, 'exit': result.returncode,
                'stdout': result.stdout.decode(errors='replace'), 'stderr': result.stderr.decode(errors='replace')}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'available': False, 'reason': str(error), 'command': command}
    finally:
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True)
        (work / '.isolation-probe').unlink(missing_ok=True)


def audit_outputs(initial, work, oracle):
    checks = {}
    for name, expected in oracle['expected_files'].items():
        path = work / name
        checks[name] = path.is_file() and not path.is_symlink() and path.read_bytes() == expected.encode()
    for name in oracle['preserve_initial']:
        path = work / name
        checks['preserved:' + name] = path.is_file() and not path.is_symlink() and path.read_bytes() == (initial / name).read_bytes()
    for name in oracle.get('forbidden_files', []):
        path = work / name
        checks['absent:' + name] = not path.exists() and not path.is_symlink()
    return {'artifact_checks': checks, 'artifact_pass': all(checks.values()),
            'semantic_review': 'UNREVIEWED', 'behavioral_acceptance': None}


def size_observation(directory):
    entries = [(digest(path.read_bytes()), path.stat().st_size) for path in directory.rglob('*') if path.is_file() and not path.is_symlink()]
    unique = dict(entries)
    return {'stored_bytes': sum(size for _, size in entries), 'unique_bytes': sum(unique.values()), 'files': len(entries),
            'scope': 'regular output files; excludes runtime, network and inaccessible native model state'}


def execute(cohort, seal, output, image, model, effort, auth, run=False):
    manifest = verify(cohort, seal)
    if (cohort / 'private/runner.py').read_bytes() != Path(__file__).read_bytes():
        raise ValueError('execute the exact runner preserved by this cohort')
    if output.resolve().is_relative_to(cohort.resolve()):
        raise ValueError('results must stay outside sealed cohort')
    output.mkdir(parents=True, exist_ok=False)
    oracle = json.loads((cohort / 'private/oracle.json').read_text())
    summaries = []
    for entry in manifest['order']:
        participant = cohort / entry['path']
        method = cohort / 'installations' / entry['arm']
        result_dir = output / entry['case'] / entry['arm']
        result_dir.mkdir(parents=True)
        work = result_dir / 'work'
        shutil.copytree(participant / 'initial', work)
        probe = preflight(image, participant / 'fixture', method, work)
        document(result_dir / 'isolation.json', probe)
        record = {'case': entry['case'], 'arm': entry['arm'], 'status': 'PENDING', 'seal': seal,
                  'model': model, 'effort': effort, 'runtime': platform.platform(), 'inputs': hashes(participant), 'method_inputs': hashes(method),
                  'storage_before': size_observation(work), 'semantic_review': 'UNREVIEWED'}
        if not probe['available'] or not run:
            record['reason'] = 'isolation unavailable' if not probe['available'] else 'preflight only; no model invoked'
        else:
            name = 'tackle-trial-' + uuid.uuid4().hex
            command = base_command(image, participant / 'fixture', method, work, name) + [
                '--mount', f'type=bind,src={auth.resolve()},dst=/root/.codex/auth.json,readonly', image,
                'codex', 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
                '--sandbox', 'danger-full-access', '--json', '--color', 'never', '--cd', '/work',
                '-m', model, '-c', 'model_reasoning_effort=' + json.dumps(effort),
                'Read /method/SKILL.md and /fixture/TASK.md. Follow only this task with the selected '
                'installation under /method; /work contains your writable task files. Do not delegate, '
                'look up external material or access account credentials. Keep unrelated inputs intact.']
            record.update(command=command, status='STARTED', start=datetime.now(timezone.utc).isoformat())
            document(result_dir / 'record.json', record)
            start = time.monotonic()
            with (result_dir / 'events.jsonl').open('wb') as stdout, (result_dir / 'stderr').open('wb') as stderr:
                try:
                    child = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=600)
                    record.update(exit=child.returncode, status='OBSERVED' if child.returncode == 0 else 'FAILED')
                except subprocess.TimeoutExpired:
                    record.update(exit=None, status='TIMEOUT')
                except KeyboardInterrupt:
                    record.update(exit=None, status='INTERRUPTED')
                finally:
                    cleanup = subprocess.run(['docker', 'rm', '-f', name], capture_output=True)
                    record.update(wall_seconds=time.monotonic() - start, cleanup_exit=cleanup.returncode,
                                  end=datetime.now(timezone.utc).isoformat())
            record.update(audit_outputs(participant / 'initial', work, oracle[entry['case']]))
            record['inputs_after'] = hashes(participant)
            record['method_inputs_after'] = hashes(method)
            record['inputs_unchanged'] = record['inputs_after'] == record['inputs'] and record['method_inputs_after'] == record['method_inputs']
            if not record['inputs_unchanged']:
                record['status'] = 'INVALID'
            record['storage_after'] = size_observation(work)
            record['streams'] = {name: digest((result_dir / name).read_bytes()) for name in ('events.jsonl', 'stderr')}
            record['metrics_pending_independent_review'] = ['functional/integrated acceptance', 'first-run success',
                'retries/correction cycles', 'necessary/avoidable interventions', 'brief-related rework',
                'phase times', 'repeated reads/checks', 'bytes read/rewritten', 'comprehension/recoverability']
            record['tokens_cost'] = 'n/a pending comparable native usage extraction'
        document(result_dir / 'record.json', record)
        summaries.append(record)
        if not probe['available'] or record['status'] == 'INTERRUPTED':
            break
    started = sum('start' in item for item in summaries)
    report = {'status': 'UNREVIEWED' if started else 'PENDING', 'episodes_planned': len(manifest['order']),
              'episodes_started': started, 'records': summaries,
              'behavioral_improvement': 'unclaimed', 'release_approval': False}
    document(output / 'results.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    stage = sub.add_parser('stage')
    stage.add_argument('destination', type=Path)
    stage.add_argument('--case', action='append')
    trial = sub.add_parser('preflight')
    actual = sub.add_parser('run')
    for command in (trial, actual):
        command.add_argument('cohort', type=Path)
        command.add_argument('--seal', required=True)
        command.add_argument('--output', required=True, type=Path)
        command.add_argument('--image', required=True)
    actual.add_argument('--model', required=True)
    actual.add_argument('--effort', required=True)
    actual.add_argument('--auth', required=True, type=Path)
    actual.add_argument('--authorized-model-usage', action='store_true', required=True)
    args = parser.parse_args()
    if args.mode == 'stage':
        seal = prepare(args.destination, baseline_installation(), installation(ROOT),
                       json.loads((HERE / 'cases.json').read_text()), json.loads((HERE / 'oracle.json').read_text()),
                       (HERE / 'protocol.md').read_bytes(), args.case or SMOKE)
        print(json.dumps({'status': 'PENDING', 'cohort': str(args.destination), 'seal': seal}))
        return
    if args.mode == 'run' and not args.auth.is_file():
        parser.error('the existing account session file is unavailable')
    report = execute(args.cohort, args.seal, args.output, args.image, getattr(args, 'model', None),
                     getattr(args, 'effort', None), getattr(args, 'auth', None), args.mode == 'run')
    print(json.dumps({key: value for key, value in report.items() if key != 'records'}))
    if not report['episodes_started']:
        raise SystemExit(2)
    mechanical_pass = all(item.get('exit') == 0 and item.get('artifact_pass')
                          and item.get('inputs_unchanged') for item in report['records'])
    raise SystemExit(0 if mechanical_pass else 1)


if __name__ == '__main__':
    main()
