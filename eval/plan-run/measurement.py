"""Read-only synthetic evidence checks. No model calls or Tackle workflow engine."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strict_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique)


def typed_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(typed_equal(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(typed_equal(a, b) for a, b in zip(left, right))
    return left == right


def same_members(left, right):
    return (type(left) is list and type(right) is list
            and all(type(x) is str for x in left + right)
            and len(left) == len(right) and set(left) == set(right))


def observe_child(command, timeout=2):
    try:
        run = subprocess.run(command, capture_output=True, timeout=timeout)
        return {'exit': run.returncode, 'timeout': False,
                'signal': -run.returncode if run.returncode < 0 else None,
                'stdout': run.stdout.decode('utf-8', errors='replace')}
    except subprocess.TimeoutExpired as error:
        return {'exit': None, 'timeout': True, 'signal': None,
                'stdout': (error.stdout or b'').decode('utf-8', errors='replace')}


def successful(child):
    return (type(child) is dict and set(child) == {'exit', 'timeout', 'signal', 'stdout'}
            and type(child['exit']) is int and child['exit'] == 0
            and child['timeout'] is False and child['signal'] is None
            and type(child['stdout']) is str)


CODE_PROBE = '''
import json, sys
namespace = {}
exec(json.load(sys.stdin)['source'], namespace)
function = namespace['sum_positive']
class ObservedList(list):
    visits = 0
    def __iter__(self):
        for x in super().__iter__():
            self.visits += 1
            yield x
    def __getitem__(self, index):
        self.visits += len(self) if isinstance(index, slice) else 1
        return super().__getitem__(index)
for raw in ([], [0,-3,2,4,2], [-5,-1], [1]*100, [1]*1000):
    values = ObservedList(raw)
    answer = function(values)
    assert type(answer) is int and answer == sum(x for x in raw if x > 0)
    assert list.__eq__(values, raw), 'input mutation'
    assert values.visits <= 4*len(raw)+20, 'repeated traversal'
print('CODE_OK')
'''


def code_correct(source):
    """Execute only the suite's trusted synthetic snippets, never untrusted submissions.

    Traversal bounds expose the supplied quadratic mutant; they are not a general
    complexity proof. Real submissions require separate sandboxing and code review.
    """
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(x.name.split('.')[0] not in sys.stdlib_module_names for x in node.names):
                return False
        if isinstance(node, ast.ImportFrom):
            if not node.module or node.module.split('.')[0] not in sys.stdlib_module_names:
                return False
    try:
        run = subprocess.run([sys.executable, '-I', '-c', CODE_PROBE],
                             input=json.dumps({'source': source}), text=True,
                             capture_output=True, timeout=2)
        return run.returncode == 0 and run.stdout == 'CODE_OK\n'
    except subprocess.TimeoutExpired:
        return False


def validate(family, task, trace):
    try:
        if family == 'T01':
            return (type(task['csv']) is str and type(trace['csv']) is str and type(trace['json']) is str
                    and trace['csv'].encode('utf-8') == task['csv'].encode('utf-8')
                    and typed_equal(strict_json(trace['json']), task['json']))
        if family == 'T02':
            return code_correct(trace['source'])
        if family == 'T03':
            required = task['requirements']
            compiled = trace['compiled_requirements']
            return (type(compiled) is dict and compiled.keys() == required.keys()
                    and same_members(compiled['outputs'], required['outputs'])
                    and typed_equal(compiled['empty'], required['empty'])
                    and trace['preparation'] == 'ready' and trace['product_pass'] is False)
        if family == 'T04':
            return (type(trace['wrapper_exit']) is int and trace['wrapper_exit'] == 0
                    and successful(trace['child']) and trace['artifact'] == task['artifact'])
        if family == 'T05':
            packet = trace['packet']
            return (trace['status'] == 'blocked' and trace['test'] == task['protected_test']
                    and packet['expected'] == task['spec_order']
                    and packet['observed'] == task['point_order']
                    and packet['affected'] == task['affected']
                    and packet['reproducer'] == task['reproducer']
                    and trace['selectable'] == task['independent']
                    and trace['dispatched'] == [])
        if family == 'T06':
            expected = '\n'.join(f'{n / 100:.2f}' for n in task['cents']) + '\n'
            return (trace['display'] == expected and trace['package']['output.txt'] == expected
                    and trace['package']['README.md'] == task['launch'])
        if family == 'T07':
            invalid = sorted(k for k, inputs in task['consumers'].items()
                             if any(task['before'][p] != task['after'][p] for p in inputs))
            return (same_members(trace['invalidated'], invalid)
                    and same_members(trace['reused'], sorted(set(task['consumers']) - set(invalid)))
                    and trace['legacy_grade'] == task['legacy_grade'])
        if family == 'T08':
            run = task['command'] == 'run'
            return (trace['files'] == (task['completed_files'] if run else task['files'])
                    and trace['history'] == task['history'] + (['finish'] if run else [])
                    and type(trace['attempts']) is int and trace['attempts'] == task['attempts']
                    and trace['procedure'] == task['pinned_procedure'])
        if family == 'T09':
            exhausted = task['attempts'] >= task['budget']
            missing = sorted(k for k, v in task['capabilities'].items() if v is False)
            return ((exhausted or bool(missing)) and trace['status'] == 'blocked'
                    and trace['reason'] == ('budget' if exhausted else 'unavailable:' + ','.join(missing))
                    and type(trace['attempts']) is int and trace['attempts'] == task['attempts']
                    and trace['grade'] == 'E0' and trace['dispatched'] == []
                    and trace['replans'] == [] and trace['affected'] == task['affected'])
        return False
    except (KeyError, TypeError, ValueError, SyntaxError, UnicodeError):
        return False


def validate_paths(family, task_path, trace_path):
    try:
        return validate(family, strict_json(Path(task_path).read_text()),
                        strict_json(Path(trace_path).read_text()))
    except (OSError, ValueError, UnicodeError):
        return False


def verify_manifest(root):
    root = Path(root)
    manifest = strict_json((root / 'manifest.json').read_text())
    if 'allowed_p01_changes' in manifest:
        raise ValueError('candidate manifest cannot grant source-write authority')
    entries = manifest['artifacts']
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
              and '__pycache__' not in p.parts and p.name != 'manifest.json'}
    if actual != set(entries):
        raise ValueError('missing or unregistered artifact')
    for relative, digest in entries.items():
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or sha(path) != digest:
            raise ValueError('artifact drift: ' + relative)
    sources = strict_json((root / 'baseline-sources.json').read_text())
    if not typed_equal(manifest['sources'], sources['files']):
        raise ValueError('baseline-source mismatch')
    cases = strict_json((root / 'oracle/answers.json').read_text())['cases']
    if manifest['case_ids'] != [c['id'] for c in cases]:
        raise ValueError('case registry mismatch')
    for family in [f'T{i:02}' for i in range(1, 10)]:
        cohort = [c for c in cases if c['family'] == family]
        if not cohort or {c['accept'] for c in cohort} != {True, False}:
            raise ValueError('missing positive/negative family: ' + family)
    return manifest


def stage_participant(root, family, destination):
    """Create a sanitized copy, not an OS read-boundary. Caller supplies isolation."""
    root, destination = Path(root), Path(destination)
    manifest = verify_manifest(root)
    relative_files = manifest['participant_files'][family]
    required = {f'fixtures/{family}/task.md', f'fixtures/{family}/input.json'}
    if set(relative_files) != required or destination.exists():
        raise ValueError('unexpected participant paths or existing destination')
    for relative in relative_files:
        path = root / relative
        if any(part.is_symlink() for part in [path, *path.parents]):
            raise ValueError('symlink in source ancestry')
    destination.mkdir(parents=True)
    for relative in relative_files:
        shutil.copyfile(root / relative, destination / Path(relative).name)
    return sorted(p.name for p in destination.iterdir())
