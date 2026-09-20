"""Development-only, isolated single-entry method smoke trials."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'sha256:866dac7948f23ddd2260ea5e80ebdec3cc92ac50eadb020ecfa0632854013be3'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def hashes(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob('*')) if p.is_file()}


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def stage(destination):
    destination.mkdir(parents=True, exist_ok=False)
    manifest = []
    cases = json.loads((Path(__file__).with_name('cases.json')).read_text())
    for item in cases:
        case = destination / item['id']
        case.mkdir()
        shutil.copyfile(ROOT / 'SKILL.md', case / 'SKILL.md')
        shutil.copytree(ROOT / 'references', case / 'references')
        write(case / 'TASK.md', 'The user has selected Tackle. Respond to this request:\n\n'
              + item['request'] + '\n')
        write(case / 'demo/AGENTS.md', '# Demo\n\nMethodology: Tackle 8.0.0\n')
        write(case / 'demo/plan.md', '# Export plan\n\nRequired behavior: export records and support cancellation.\n\n'
              '## 5. Point decomposition\n| Point | Responsibility |\n|---|---|\n| P-01 | Export records |\n')
        write(case / 'demo/points/P-01.md', '# Point P-01 — Export\n\n'
              'Goal: export records. Acceptance: exported rows match input records.\n'
              'Cancellation is not implemented or tested by this Point.\n')
        write(case / 'demo/board.md', '| Point | What | Briefing | Depends on | Status | Confidence |\n'
              '|---|---|---|---|---|---|\n| P-01 | Export | points/P-01.md | none | 🔴 | E0 |\n')
        write(case / 'demo/log.md', '# Log\n\n## 2026-09-20 · session 1\n\n'
              'Draft plan exists. No execution or successful verification has occurred.\n')
        write(case / 'demo/questions.md', '# Questions\n\nNone recorded.\n')
        write(case / 'demo/decisions.md', '# Decisions\n\nNo execution authorized yet.\n')
        manifest.append(dict(id=item['id'], inputs=hashes(case)))
    write(destination / 'manifest.json', json.dumps(manifest, indent=2))
    return manifest


def run_case(source, entry, destination, model, effort):
    case = source / entry['id']
    result_dir = destination / entry['id']
    result_dir.mkdir(parents=True, exist_ok=False)
    artifacts = result_dir / 'artifacts'
    artifacts.mkdir()
    write(artifacts / 'format.txt', '  ready  \n')
    write(artifacts / 'sentinel.txt', 'preserve\n')
    base = ['docker', 'run', '--rm', '--read-only', '--cap-drop', 'ALL', '--security-opt',
            'no-new-privileges', '--tmpfs', '/tmp', '--tmpfs', '/root', '--mount',
            f'type=bind,src={case},dst=/fixture,readonly', '--mount',
            f'type=bind,src={artifacts},dst=/outputs', '--workdir', '/fixture']
    probe_command = base + ['--network', 'none', IMAGE, 'sh', '-c',
                            'test -r SKILL.md && test ! -e /Users/alph0x/Developer/Tackle && '
                            'touch /outputs/probe && ! touch /fixture/probe && ! touch /outside-probe']
    probe = subprocess.run(probe_command, capture_output=True)
    write(result_dir / 'isolation.json', json.dumps(dict(command=probe_command, exit=probe.returncode,
          stdout=probe.stdout.decode(), stderr=probe.stderr.decode()), indent=2))
    if probe.returncode:
        return dict(id=entry['id'], unavailable='isolation')
    command = base + ['--mount', f'type=bind,src={Path.home() / ".codex/auth.json"},dst=/root/.codex/auth.json,readonly',
                     IMAGE, 'codex', 'exec', '--ignore-user-config', '--ephemeral',
                     '--skip-git-repo-check', '--sandbox', 'danger-full-access', '--add-dir',
                     '/outputs', '--json', '--color', 'never', '--cd', '/fixture', '-m', model,
                     '-c', f'model_reasoning_effort="{effort}"',
                     'Read SKILL.md, then TASK.md and respond to its user request. Use only /fixture '
                     'and /outputs; no external lookup or delegation. The host exposes /outputs for '
                     'any task-authorized changes. Do not inspect authentication files.']
    shutil.copyfile(__file__, result_dir / 'runner.py')
    record = dict(command=command, model=model, effort=effort, start=stamp(),
                  inputs_before=hashes(case), artifacts_before=hashes(artifacts),
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with (result_dir / 'events.jsonl').open('wb') as stdout, (result_dir / 'stderr').open('wb') as stderr:
        try:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=480)
            record.update(exit=result.returncode, timeout=False)
        except subprocess.TimeoutExpired:
            record.update(exit=None, timeout=True)
    record.update(end=stamp(), inputs_after=hashes(case), artifacts_after=hashes(artifacts))
    record['streams'] = {name: hashlib.sha256((result_dir / name).read_bytes()).hexdigest()
                         for name in ('events.jsonl', 'stderr')}
    write(result_dir / 'record.json', json.dumps(record, indent=2))
    return dict(id=entry['id'], exit=record['exit'], timeout=record['timeout'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['stage', 'run'])
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--model')
    parser.add_argument('--effort')
    args = parser.parse_args()
    if args.mode == 'stage':
        print(json.dumps(dict(cases=len(stage(args.source)))))
        return
    if not all((args.output, args.model, args.effort)):
        parser.error('run needs output, model and effort')
    manifest = json.loads((args.source / 'manifest.json').read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda entry: run_case(args.source, entry, args.output, args.model, args.effort), manifest))
    print(json.dumps(results, indent=2))
    raise SystemExit(0 if all(item.get('exit') == 0 and not item.get('timeout') for item in results) else 1)


if __name__ == '__main__':
    main()
