"""Development-only strict suite registry; retained raw outcomes, no model calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def safe_path(root, relative):
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != 'eval':
        raise ValueError('registry path must remain inside eval: ' + str(relative))
    result = root / path
    if result.is_symlink() or not result.resolve().is_relative_to((root / 'eval').resolve()):
        raise ValueError('registry path escapes eval: ' + str(relative))
    return result


def validate(root, manifest):
    if manifest.get('version') != 1 or not manifest.get('suites'):
        raise ValueError('missing nonempty version 1 suite registry')
    excluded = []
    for relative in manifest.get('excluded_directories', []):
        if relative not in ('eval/scenarios', 'eval/scratch', 'eval/runs') and Path(relative).name != 'fixtures':
            raise ValueError('only explicit synthetic fixture or trial-output trees may be excluded')
        excluded.append(safe_path(root, relative))
    expected, paths = set(), set()
    for suite in manifest['suites']:
        directory = safe_path(root, suite['path'])
        if not directory.is_dir() or suite['path'] in paths:
            raise ValueError('missing or duplicate suite: ' + suite['path'])
        paths.add(suite['path'])
        if not suite.get('files') or type(suite.get('tests')) is not int or suite['tests'] <= 0:
            raise ValueError('suite needs explicit files and positive expected test count')
        for filename in suite['files']:
            if Path(filename).name != filename or not filename.startswith('test_') or not filename.endswith('.py'):
                raise ValueError('invalid test filename: ' + filename)
            path = directory / filename
            if not path.is_file() or path.is_symlink() or path in expected:
                raise ValueError('missing, symlinked or duplicated test: ' + str(path))
            if any(path.is_relative_to(exclusion) for exclusion in excluded):
                raise ValueError('registered test is excluded: ' + str(path))
            expected.add(path)
    actual = {path for path in (root / 'eval').rglob('test_*.py')
              if not any(path.is_relative_to(exclusion) for exclusion in excluded)}
    if actual != expected:
        raise ValueError('test inventory mismatch: unregistered=' + repr(sorted(str(p.relative_to(root)) for p in actual - expected))
                         + '; missing=' + repr(sorted(str(p.relative_to(root)) for p in expected - actual)))
    return expected


def run(root, manifest, output):
    root = root.resolve()
    files = validate(root, manifest)
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for suite in manifest['suites']:
        command = [sys.executable, '-m', 'unittest', 'discover', '-s', suite['path'], '-p', 'test_*.py', '-v']
        start = stamp()
        child = subprocess.run(command, cwd=root, capture_output=True)
        matches = re.findall(rb'^Ran (\d+) tests? in ', child.stderr, re.M)
        count = int(matches[-1]) if matches else 0
        skipped = re.search(rb'\bskipped=(\d+)', child.stderr)
        skipped_count = int(skipped[1]) if skipped else 0
        name = suite['path'].removeprefix('eval/').replace('/', '-')
        record = dict(path=suite['path'], command=command, cwd=str(root), start=start, end=stamp(),
                      exit=child.returncode, tests=count, expected_tests=suite['tests'], skipped=skipped_count,
                      passed=child.returncode == 0 and count == suite['tests'] and count > 0 and skipped_count == 0)
        for stream, data in (('stdout', child.stdout), ('stderr', child.stderr)):
            filename = name + '.' + stream
            (output / filename).write_bytes(data)
            record[stream] = filename
            record[stream + '_sha256'] = digest(data)
        results.append(record)
        print(name, 'PASS' if record['passed'] else 'FAIL', 'tests=' + str(count), 'expected=' + str(suite['tests']), flush=True)
    report = dict(passed=all(item['passed'] for item in results), tests=sum(item['tests'] for item in results),
                  runtime=platform.platform(), python=platform.python_version(),
                  registry_sha256=digest(json.dumps(manifest, sort_keys=True).encode()),
                  inputs={str(path.relative_to(root)): digest(path.read_bytes()) for path in sorted(files)}, suites=results)
    (output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = args.manifest or args.root / 'eval/suite-manifest.json'
    try:
        report = run(args.root, json.loads(manifest.read_text()), args.output)
    except (ValueError, KeyError, OSError) as error:
        message = 'suite discovery rejected: ' + str(error) + '\n'
        if not args.output.exists():
            args.output.mkdir(parents=True)
            (args.output / 'discovery.stderr').write_text(message)
            (args.output / 'results.json').write_text(json.dumps({
                'passed': False, 'phase': 'discovery', 'tests': 0, 'error': str(error),
                'command': [sys.executable] + sys.argv, 'cwd': str(Path.cwd()),
                'stderr': 'discovery.stderr', 'exit': 2}, indent=2) + '\n')
        parser.exit(2, message)
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
