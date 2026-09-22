"""Reproducible logical-byte measurement; real inventories are read-only."""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
BASELINE = '61f9b4b'


def measure(directory):
    classes = defaultdict(lambda: dict(files=0, logical_bytes=0, unique={}))
    roles = defaultdict(set)
    for path in directory.rglob('result.json'):
        try:
            record = json.loads(path.read_text())
        except (ValueError, OSError, UnicodeError):
            continue
        for key in ('inputs_before', 'inputs_after', 'before', 'after'):
            mapping = record.get(key, {})
            if isinstance(mapping, dict):
                for name, digest in mapping.items():
                    if isinstance(digest, str):
                        roles[digest].add('scripts' if Path(name).suffix in ('.py', '.sh') else 'inputs')
        for key in ('artifacts', 'streams'):
            mapping = record.get(key, {})
            if isinstance(mapping, dict):
                for digest in mapping.values():
                    if isinstance(digest, str):
                        roles[digest].add(key)
    hashes, total, files, aliases, allocated = {}, 0, 0, 0, 0
    for path in directory.rglob('*'):
        if path.is_symlink():
            aliases += 1
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        if any(p.startswith(('.pending-', '.write-', '.export-', '.restore-')) for p in relative.parts):
            category = 'temporary'
        elif any('archive' in p for p in relative.parts) or path.suffix in ('.gz', '.zip', '.tar'):
            category = 'archives'
        elif any(p in ('objects', 'blobs', 'inputs') for p in relative.parts):
            category = next((r for r in ('scripts', 'inputs', 'artifacts', 'streams')
                             if r in roles[path.name]), 'retained_content_unclassified')
        elif path.suffix in ('.stdout', '.stderr', '.bin') or path.name in ('stdout', 'stderr'):
            category = 'streams'
        elif path.suffix in ('.py', '.sh'):
            category = 'scripts'
        elif path.suffix in ('.json', '.md', '.jsonl'):
            category = 'metadata'
        else:
            category = 'artifacts_or_unclassified'
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        size = len(content)
        hashes[digest] = size
        total += size
        files += 1
        allocated += getattr(path.stat(), 'st_blocks', 0) * 512
        classes[category]['files'] += 1
        classes[category]['logical_bytes'] += size
        classes[category]['unique'][digest] = size
    for counts in classes.values():
        counts['unique_content_bytes'] = sum(counts.pop('unique').values())
    return dict(files=files, aliases=aliases, logical_bytes=total,
                unique_content_bytes=sum(hashes.values()), identical_copy_bytes=total-sum(hashes.values()),
                allocated_bytes=allocated, classes=dict(classes),
                class_rule='Shared objects counted once: scripts, inputs, artifacts, streams precedence; unknown bytes remain unclassified',
                current_vs_historical='Requires an obligation/retention policy; not inferred from size',
                agent_read_bytes=None, billed_tokens=None)


def fixture(source, candidate, input_size=1048576, extra_inputs=0):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary).resolve()
        (root / 'initiative').mkdir()
        (root / 'input.bin').write_bytes(b'x' * input_size)
        (root / 'child.py').write_text("print('checked')\n")
        (root / 'capture.py').write_text(source)
        spec = dict(argv=[sys.executable, 'child.py'],
                    selectors=[dict(glob='input.bin', required=True)], artifacts=[], timeout_seconds=3,
                    destination='initiative/evidence')
        if candidate:
            spec['workspace'] = 'initiative'
        if extra_inputs:
            (root / 'data').mkdir()
            for index in range(extra_inputs):
                (root / 'data' / ('input-%04d.txt' % index)).write_bytes(b'kept lookup data')
            spec['selectors'].append(dict(glob='data/*.txt', required=True))
        (root / 'check.json').write_text(json.dumps(spec))
        times, records, growth = [], [], []
        for _ in range(3):
            start = time.perf_counter()
            run = subprocess.run([sys.executable, 'capture.py', 'check.json'], cwd=root, capture_output=True)
            times.append(time.perf_counter()-start)
            if run.returncode:
                raise RuntimeError(run.stderr.decode())
            record = Path(run.stdout.decode().strip()).parent
            records.append(record)
            snapshot = measure(root / 'initiative/evidence')
            growth.append({k: snapshot[k] for k in ('logical_bytes', 'files', 'aliases')})
        report = measure(root / 'initiative/evidence')
        fingerprint = hashlib.sha256(b'x' * input_size).hexdigest()
        content_files = [p for p in (root / 'initiative/evidence').rglob(fingerprint)
                         if p.is_file() and not p.is_symlink()]
        report.update(events=len(records), unchanged_input_bytes=input_size, extra_input_files=extra_inputs,
                      stored_input_copies=len(content_files), stored_input_bytes=sum(p.stat().st_size for p in content_files),
                      capture_seconds=times, growth_after_each_check=growth,
                      source_sha256=hashlib.sha256(source.encode()).hexdigest())
        if candidate:
            (root / 'input.bin').write_bytes(b'current revision')
            run = subprocess.run([sys.executable, 'capture.py', 'check.json'], cwd=root, capture_output=True, check=True)
            current = Path(run.stdout.decode().strip()).parent
            store = root / 'initiative/evidence'
            policy = dict(current=[str(current.relative_to(store))], pinned=[], active=[], resolved_failures=[],
                          reference_sources=['obligations.json'], reference_writes_coordinated=True,
                          retire=[str(p.relative_to(store)) for p in records],
                          reason='Disposable fixture: first three results superseded, current revision retained')
            (root / 'initiative/obligations.json').write_text(json.dumps(dict(current=policy['current'])))
            (root / 'policy.json').write_text(json.dumps(policy))
            lifecycle = re.findall(r'```python\n(.*?)\n```',
                (ROOT / 'references/guides/record-lifecycle.md').read_text(), re.S)[0]
            (root / 'lifecycle.py').write_text(lifecycle)
            report['after_changed_capture'] = measure(store)
            script = ("from lifecycle import *; import time; s=Path('initiative/evidence'); "
                      "p=json.loads(Path('policy.json').read_text()); t=time.perf_counter(); "
                      "v=preview(s,p); maintain(s,p,v['fingerprint'],authorized=True); "
                      "print(json.dumps(dict(preview=v,maintenance_seconds=time.perf_counter()-t)))")
            run = subprocess.run([sys.executable, '-c', script], cwd=root, capture_output=True, check=True)
            maintenance = json.loads(run.stdout)
            maintenance['preview']['scope'] = 'initiative/evidence'
            report['maintenance'] = maintenance
            report['after_maintenance'] = measure(store)
            report['retired_events'] = len(list(store.rglob('retired.json')))
            report['retained_current_events'] = 1
        return report


def main():
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--inventory', type=Path, help='Read-only existing evidence directory, never maintenance')
    args = parser.parse_args()
    if args.inventory:
        result = dict(kind='existing scoped directory, no deletion inference',
                      scope=str(args.inventory.resolve()), measurement=measure(args.inventory))
    else:
        baseline = subprocess.run(['git', 'show', BASELINE + ':references/guides/full-checks.md'],
                                  cwd=ROOT, capture_output=True, check=True).stdout.decode()
        candidate = (ROOT / 'references/guides/full-checks.md').read_text()
        extract = lambda text: re.findall(r'```python\n(.*?)\n```', text, re.S)[0]
        result = dict(kind='synthetic, three actual checks, same unchanged 1 MiB input', baseline_commit=BASELINE,
                      baseline=fixture(extract(baseline), False), candidate=fixture(extract(candidate), True),
                      metadata_retirement_fixture=fixture(extract(candidate), True, input_size=1, extra_inputs=512),
                      limitations='Two bounded deterministic fixtures; no real-workspace savings, behavioral or token claim')
    result['total_measurement_seconds'] = time.perf_counter() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
