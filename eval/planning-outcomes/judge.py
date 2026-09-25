"""Judge one planning-outcome episode mechanically by its hidden acceptance tests.

Usage: judge.py --episode <harness episode dir> [--out <file>] [--repo <dir>] [--debug]
       judge.py --scenario <scenario_id> --variant <variant_id> --work <dir> --out <file> [--repo <dir>] [--debug]

The hidden tests are read from the git index of --repo, at eval/scenarios/<scenario>/variants/<variant>/hidden/,
and run through runner.py (python3 -I) against a scratch copy of the work tree; the judged tree is never
written. The output is the judgment ``harness.py record --judgment`` accepts, plus ``details`` with counts
only. Exit 0 writes the judgment; exit 2 refuses and writes nothing. See eval/planning-outcomes/README.md.
Standard library only; Python 3.10 or later.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNNER = HERE / 'runner.py'
NA = 'n/a'
SCHEMA = 'tackle-hidden-tests/1'
CHECK_RUN = re.compile(r'\b(unittest|pytest|nose2|tox|nox|make\s+(test|check))\b')
IGNORED = re.compile(r'(^|/)(\.git|__pycache__)(/|$)|\.py[co]$')


class Refusal(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mapping_digest(mapping):
    """The C06 tree digest: sha256 of the sorted {relative path: sha256} mapping as compact JSON."""
    return sha(json.dumps(mapping, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))


def git(repo, *args):
    try:
        return subprocess.run(['git', '-C', str(repo)] + list(args), capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        raise Refusal('git %s failed in %s' % (args[0], repo))


def hidden_files(repo, scenario, variant):
    """{relative name: bytes} of the staged hidden/ directory, and its hidden.json."""
    if git(repo, 'rev-parse', '--is-inside-work-tree').strip() != b'true':
        raise Refusal('--repo is not a git work tree')
    prefix = 'eval/scenarios/%s/variants/%s/hidden/' % (scenario, variant)
    names = [n for n in git(repo, 'ls-files', '-z', '--', prefix).decode('utf-8').split('\0') if n]
    if not names:
        raise Refusal('no staged hidden tests for %s/%s' % (scenario, variant))
    files = {name[len(prefix):]: git(repo, 'show', ':' + name) for name in names}
    if 'hidden.json' not in files:
        raise Refusal('%s/%s has no staged hidden.json' % (scenario, variant))
    try:
        spec = json.loads(files['hidden.json'])
    except ValueError:
        raise Refusal('hidden.json is not JSON')
    valid = (isinstance(spec, dict) and spec.get('schema') == SCHEMA
             and type(spec.get('tests')) is int and spec['tests'] > 0
             and type(spec.get('timeout_seconds')) is int and spec['timeout_seconds'] > 0
             and isinstance(spec.get('pythonpath'), list)
             and all(isinstance(p, str) and p and not os.path.isabs(p) and '..' not in Path(p).parts
                     for p in spec['pythonpath'])
             and (spec.get('visible') is None or (isinstance(spec['visible'], list)
                                                  and all(isinstance(a, str) for a in spec['visible']))))
    if not valid:
        raise Refusal('hidden.json is malformed')
    if not any(name.startswith('test_') and name.endswith('.py') for name in files):
        raise Refusal('hidden/ holds no test_*.py')
    return files, spec


def tree_mapping(root):
    mapping = {}
    for path in sorted(Path(root).rglob('*')):
        relative = path.relative_to(root).as_posix()
        if IGNORED.search(relative):
            continue
        if path.is_symlink():
            mapping[relative] = sha(os.readlink(path).encode('utf-8'))
        elif path.is_file():
            mapping[relative] = sha(path.read_bytes())
    return mapping


def copy_tree(source, target):
    shutil.copytree(source, target, symlinks=True, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))


def stop_group(child):
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def run_hidden(files, spec, work, scratch, debug=False):
    """Run the hidden suite against a copy of ``work``; returns the counts for ``details.hidden``."""
    hidden, copy, home, result = scratch / 'hidden', scratch / 'copy', scratch / 'home', scratch / 'result.json'
    for name, data in files.items():
        if name != 'hidden.json':
            (hidden / name).parent.mkdir(parents=True, exist_ok=True)
            (hidden / name).write_bytes(data)
    copy_tree(work, copy)
    home.mkdir()
    env = {'PATH': os.pathsep.join([str(Path(sys.executable).parent), '/usr/bin', '/bin']), 'HOME': str(home),
           'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONHASHSEED': '0'}
    argv = [sys.executable, '-I', str(RUNNER), str(hidden), str(copy), str(result)] + list(spec['pythonpath'])
    child = subprocess.Popen(argv, cwd=copy, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True)
    timeout = False
    try:
        stdout, stderr = child.communicate(timeout=spec['timeout_seconds'])
    except subprocess.TimeoutExpired:
        stop_group(child)
        stdout, stderr = child.communicate()
        timeout = True
    counts = {'expected': spec['tests'], 'ran': NA, 'failures': NA, 'errors': NA, 'skipped': NA,
              'exit': child.returncode if not timeout else NA, 'timeout': timeout, 'result': 'missing'}
    if not timeout and result.is_file():
        try:
            observed = json.loads(result.read_text(encoding='utf-8'))
            if all(type(observed.get(k)) is int and observed[k] >= 0 for k in ('ran', 'failures', 'errors', 'skipped')):
                counts.update({k: observed[k] for k in ('ran', 'failures', 'errors', 'skipped')}, result='written')
        except (OSError, ValueError):
            pass
    if debug:
        sys.stdout.write(stderr.decode('utf-8', 'replace'))
    return counts


def avoided(hidden):
    return (hidden['result'] == 'written' and hidden['exit'] == 0 and not hidden['timeout']
            and hidden['ran'] == hidden['expected'] and hidden['failures'] == 0 and hidden['errors'] == 0
            and hidden['skipped'] == 0)


def events(data):
    found = []
    for line in data.decode('utf-8', 'replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            found.append(event)
    return found


def claude_code_runs(found):
    pending, runs = {}, []
    for event in found:
        content = (event.get('message') or {}).get('content') if isinstance(event.get('message'), dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if event.get('type') == 'assistant' and block.get('type') == 'tool_use' and block.get('name') == 'Bash':
                command = (block.get('input') or {}).get('command')
                if isinstance(command, str) and isinstance(block.get('id'), str):
                    pending[block['id']] = command
            elif event.get('type') == 'user' and block.get('type') == 'tool_result':
                command = pending.pop(block.get('tool_use_id'), None)
                if command is not None:
                    runs.append((command, block.get('is_error') is not True))
    return runs


def codex_runs(found):
    runs = []
    for event in found:
        item = event.get('item')
        if event.get('type') == 'item.completed' and isinstance(item, dict) and item.get('type') == 'command_execution':
            if isinstance(item.get('command'), str) and type(item.get('exit_code')) is int:
                runs.append((item['command'], item['exit_code'] == 0))
    return runs


# A subagent episode's transcript is a Claude Code session transcript (D-87), so it shares that parser.
PARSERS = {'claude-code': claude_code_runs, 'subagent': claude_code_runs, 'codex': codex_runs}


def correction_counts(adapter, streams):
    """(check_runs, correction_cycles, transcript_format); n/a when the format carries no shell commands."""
    parser = PARSERS.get(adapter)
    if parser is None or not streams:
        return NA, NA, NA
    runs = []
    for data in streams:
        found = events(data)
        if not found:
            return NA, NA, NA
        runs.extend(parser(found))
    checks = [ok for command, ok in runs if CHECK_RUN.search(command)]
    cycles = sum(1 for position, ok in enumerate(checks) if not ok and position < len(checks) - 1)
    return len(checks), cycles, adapter


def judge(repo, scenario, variant, work, streams, adapter, debug=False):
    if not Path(work).is_dir():
        raise Refusal('the work tree is missing: %s' % work)
    files, spec = hidden_files(repo, scenario, variant)
    work_sha = mapping_digest(tree_mapping(work))
    with tempfile.TemporaryDirectory(prefix='tackle-judge-') as scratch:
        hidden = run_hidden(files, spec, Path(work), Path(scratch), debug)
    if mapping_digest(tree_mapping(work)) != work_sha:
        raise Refusal('the judged tree changed during judging')
    ok = avoided(hidden)
    check_runs, cycles, form = correction_counts(adapter, streams)
    return {'judge': {'kind': 'mechanical', 'model_family': NA, 'blinded': True},
            'outcome': 'avoided' if ok else 'fell', 'invalid_reason': None, 'rule_exposure': False,
            'scores': {'correct_action': 2 if ok else 0, 'evidence': None, 'verification_honesty': None,
                       'report_quality': None},
            'details': {'schema': 'tackle-outcome-judgment/1', 'scenario_id': scenario, 'variant_id': variant,
                        'hidden_sha256': mapping_digest({name: sha(data) for name, data in files.items()}),
                        'work_sha256': work_sha, 'hidden': hidden, 'check_runs': check_runs,
                        'correction_cycles': cycles, 'transcript_format': form}}


def load_json(path, what):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise Refusal('%s is missing or not JSON' % what)
    if not isinstance(value, dict):
        raise Refusal('%s is not a JSON object' % what)
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(prog='judge.py', description='Mechanical judge for planning-outcome episodes.')
    parser.add_argument('--episode')
    parser.add_argument('--scenario')
    parser.add_argument('--variant')
    parser.add_argument('--work')
    parser.add_argument('--out')
    parser.add_argument('--repo', default=str(ROOT))
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.episode:
            if args.scenario or args.variant or args.work:
                raise Refusal('--episode takes no --scenario, --variant or --work')
            episode = Path(args.episode)
            stage, ran = load_json(episode / 'stage.json', 'stage.json'), load_json(episode / 'run.json', 'run.json')
            scenario, variant = stage.get('scenario_id'), stage.get('variant_id')
            if not (isinstance(scenario, str) and isinstance(variant, str)):
                raise Refusal('stage.json names no scenario_id and variant_id')
            sessions = sorted((episode / 'sessions').glob('[0-9][0-9]/stdout')) if (episode / 'sessions').is_dir() else []
            streams, adapter, work = [p.read_bytes() for p in sessions], ran.get('adapter'), episode / 'work'
            out = Path(args.out) if args.out else episode / 'judgment.json'
        else:
            if not (args.scenario and args.variant and args.work and args.out):
                raise Refusal('direct mode needs --scenario, --variant, --work and --out')
            scenario, variant, work, out, streams, adapter = (args.scenario, args.variant, Path(args.work),
                                                              Path(args.out), [], None)
        if out.exists():
            raise Refusal('the output exists and is never overwritten: %s' % out)
        judgment = judge(Path(args.repo), scenario, variant, work, streams, adapter, args.debug)
    except Refusal as refusal:
        sys.stderr.write('judge: refused: %s\n' % refusal)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(judgment, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print('judge: %s/%s %s (ran %s of %s)' % (scenario, variant, judgment['outcome'],
                                             judgment['details']['hidden']['ran'], judgment['details']['hidden']['expected']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
