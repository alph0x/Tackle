"""Check the scenario index: every scenario classified, every input tree sealed, held-out variants sealed first.

Usage: python3 eval/scenario-index/check_index.py --repo <dir>
       python3 eval/scenario-index/check_index.py --digest <dir>
Exit 0 valid (one summary line) or digest printed, 1 violations (one ``error:`` line each), 2 usage or not a
git work tree. The checker never writes; variant inputs are read from the git index. The index format is described in ``eval/scenario-index/README.md``;
the tree digest is the one PROTOCOL.md's ``fixture_sha256`` uses.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

USAGE = 'usage: check_index.py --repo <dir> | --digest <dir>'
INDEX, LEDGER = 'eval/scenarios/INDEX.json', 'eval/rules/ledger.json'
CLASSES = ('outcome-trap', 'procedure', 'tripwire', 'retired')
GAPS = ('invocation-help-aliases', 'sizing', 'correction-budget-stop', 'resume-across-sessions',
        'communication-policy', 'coordinated-independence')
ENTRY_FIELDS = {'scenario_id', 'class', 'harm', 'covers', 'authored', 'variants'}
VARIANT_FIELDS = {'variant_id', 'split', 'path', 'prompts', 'fixture', 'stageable', 'fixture_sha256', 'control_exposure'}
VARIANT_ID = re.compile(r'([vh])[0-9]+')
HEX = re.compile(r'[0-9a-f]{64}')
HELD_OUT_TRAPS = (8, 10)
INSTALL_NAME = re.compile(r'^name:\s*tackle\s*$', re.I | re.M)


class Symlink(Exception):
    pass


class Errors(list):
    def add(self, where, code, text):
        self.append('error: %s: %s: %s' % (where, code, text))


def mapping_digest(mapping):
    return hashlib.sha256(json.dumps(mapping, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def tree_files(root, prefix=''):
    files = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise Symlink(str(path.relative_to(root)))
        if path.is_file():
            files[prefix + path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def tree_digest(root):
    return mapping_digest({name: hashlib.sha256(data).hexdigest() for name, data in tree_files(root).items()})


def normalized(text):
    return re.sub(r'\s+', ' ', text).strip().lower()


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo)] + list(args), capture_output=True, text=True)


class Tracked:
    """The git index: every variant input is read from it, so a digest seals what a commit contains."""

    def __init__(self, repo):
        self.repo = repo
        child = subprocess.run(['git', '-C', str(repo), 'ls-files', '-s', '-z'], capture_output=True)
        self.entries = {}
        for row in child.stdout.split(b'\0'):
            if row:
                meta, _, path = row.partition(b'\t')
                mode, blob, stage = meta.decode().split(' ')
                if stage == '0':
                    self.entries[path.decode('utf-8', 'surrogateescape')] = (mode, blob)
        self.cache = {}

    def under(self, prefix):
        return sorted(path for path in self.entries if path.startswith(prefix))

    def load(self, paths):
        """Read the staged bytes of many paths with one ``git cat-file --batch``."""
        wanted = [p for p in paths if p in self.entries and p not in self.cache and self.entries[p][0] != '120000']
        if not wanted:
            return
        request = ''.join(self.entries[p][1] + '\n' for p in wanted).encode()
        out = subprocess.run(['git', '-C', str(self.repo), 'cat-file', '--batch'], input=request, capture_output=True,
                             check=True).stdout
        position = 0
        for path in wanted:
            header_end = out.index(b'\n', position)
            size = int(out[position:header_end].split()[2])
            self.cache[path] = out[header_end + 1:header_end + 1 + size]
            position = header_end + 1 + size + 1

    def read(self, path):
        mode, blob = self.entries[path]
        if mode == '120000':
            raise Symlink(path)
        if path not in self.cache:
            self.load([path])
        return self.cache[path]


RUNTIME = re.compile(r'(^|/)__pycache__/|\.py[co]$')


def input_tree(tracked, variant):
    """The variant's staged input files, {relative path: bytes}, or raises Symlink / FileNotFoundError."""
    root = variant['path'] + '/'
    files = {}
    for prompt in variant['prompts']:
        if root + prompt not in tracked.entries:
            raise FileNotFoundError(prompt)
        files[prompt] = tracked.read(root + prompt)
    fixture = root + variant['fixture'] + '/'
    names = tracked.under(fixture)
    if not names:
        raise FileNotFoundError(variant['fixture'])
    tracked.load(names)
    for name in names:
        files[variant['fixture'] + '/' + name[len(fixture):]] = tracked.read(name)
    return files


def untracked_input(repo, tracked, variant):
    """Input files on disk that the index does not hold (runtime caches excepted)."""
    root = repo / variant['path']
    found = []
    for base in [root / p for p in variant['prompts']] + [root / variant['fixture']]:
        for path in ([base] if not base.is_dir() else sorted(base.rglob('*'))):
            if (path.is_file() or path.is_symlink()) and not RUNTIME.search(path.relative_to(repo).as_posix()):
                name = path.relative_to(repo).as_posix()
                if name not in tracked.entries:
                    found.append(name)
    return found


def exposure_of(files, fragments):
    install = any((name.rsplit('/', 1)[-1] == 'SKILL.md' and INSTALL_NAME.search(data.decode('utf-8', 'replace')))
                  or '/references/guides/' in '/' + name for name, data in files.items())
    text = normalized(' '.join(data.decode('utf-8', 'replace') for data in files.values()))
    found = sorted({fragment for fragment in fragments if normalized(fragment) and normalized(fragment) in text})
    return {'install': bool(install), 'fragments': found}


def load(repo, path, errors):
    try:
        return json.loads((repo / path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as problem:
        errors.add('index', 'schema', '%s unreadable (%s)' % (path, problem.__class__.__name__))
        return None


def rule_fragments(ledger):
    by_scenario = {}
    rules = ledger.get('rules') if isinstance(ledger, dict) else None
    for rule in rules if isinstance(rules, list) else []:
        evidence = rule.get('evidence') if isinstance(rule, dict) else None
        scenarios = evidence.get('scenarios') if isinstance(evidence, dict) else None
        for scenario in scenarios if isinstance(scenarios, list) else []:
            texts = [rule.get(key) for key in ('statement', 'home_fragment') if isinstance(rule.get(key), str)]
            by_scenario.setdefault(scenario, []).extend(texts)
    return by_scenario


def valid_entry(entry):
    if not isinstance(entry, dict) or set(entry) != ENTRY_FIELDS or not isinstance(entry['scenario_id'], str):
        return False
    authored = entry['authored']
    return (isinstance(entry['harm'], str) and isinstance(entry['covers'], list) and isinstance(entry['variants'], list)
            and isinstance(authored, dict) and set(authored) == {'actors', 'blind'} and isinstance(authored['blind'], bool)
            and isinstance(authored['actors'], list) and all(isinstance(a, str) and a for a in authored['actors']))


def valid_variant(variant):
    if not isinstance(variant, dict) or set(variant) != VARIANT_FIELDS:
        return False
    exposure = variant['control_exposure']
    return (all(isinstance(variant[key], str) for key in ('variant_id', 'split', 'path'))
            and isinstance(variant['prompts'], list) and all(isinstance(p, str) and p for p in variant['prompts'])
            and (variant['fixture'] is None or isinstance(variant['fixture'], str))
            and isinstance(variant['stageable'], bool)
            and (variant['fixture_sha256'] is None or (isinstance(variant['fixture_sha256'], str) and HEX.fullmatch(variant['fixture_sha256'])))
            and isinstance(exposure, dict) and set(exposure) == {'install', 'fragments'} and isinstance(exposure['install'], bool)
            and isinstance(exposure['fragments'], list) and all(isinstance(f, str) for f in exposure['fragments']))


def own_sheets(tracked, scenario, variant):
    sheets = set()
    candidates = ['eval/scenarios/%s/GROUND-TRUTH.md' % scenario]
    root = Path(variant['path'])
    if root.name == 'input':
        candidates.append((root.parent / 'GROUND-TRUTH.md').as_posix())
    for path in candidates:
        if path in tracked.entries:
            sheets.add(tracked.read(path))
    return sheets


def check_variant(repo, tracked, scenario, variant, fragments, errors):
    """Returns the recomputed exposure of a valid variant, or None when its input cannot be read."""
    where = '%s/%s' % (scenario, variant['variant_id'])
    match = VARIANT_ID.fullmatch(variant['variant_id'])
    if not match or variant['split'] != ('development' if match[1] == 'v' else 'held-out'):
        errors.add(where, 'vocabulary', 'variant ids are v<N> (development) or h<N> (held-out)')
    new = '/variants/' in variant['path']
    if not variant['stageable']:
        if variant['fixture_sha256'] is not None:
            errors.add(where, 'digest', 'a variant that is not stageable has no digest')
        if variant['split'] == 'held-out' or new:
            errors.add(where, 'input', 'held-out and new variants must be stageable')
        if variant['control_exposure'] != {'install': False, 'fragments': []}:
            errors.add(where, 'exposure', 'a variant without input has no exposure')
        return {'install': False, 'fragments': []}
    base = 'eval/scenarios/%s' % scenario
    if not (variant['path'] == base or variant['path'].startswith(base + '/')) or '..' in Path(variant['path']).parts \
            or not variant['prompts'] or not variant['fixture']:
        errors.add(where, 'input', 'a stageable variant needs prompts and a fixture under its scenario directory')
        return None
    hidden = untracked_input(repo, tracked, variant)
    if hidden:
        errors.add(where, 'untracked', 'input files on disk are not in the git index (force-add what the world\'s own '
                   '.gitignore hides): %s' % ', '.join(hidden))
    try:
        files = input_tree(tracked, variant)
        if new and Path(variant['path']).name == 'input':
            root_files = [name[len(variant['path']) + 1:] for name in tracked.under(variant['path'] + '/')]
            if set(root_files) != set(files):
                errors.add(where, 'digest', 'the input root holds files other than its prompts and fixture: %s'
                           % ', '.join(sorted(set(root_files) - set(files))))
    except Symlink as link:
        errors.add(where, 'symlink', 'input holds a symlink: %s' % link)
        return None
    except (FileNotFoundError, IsADirectoryError, NotADirectoryError) as missing:
        errors.add(where, 'input', 'missing input: %s' % missing)
        return None
    if mapping_digest({name: hashlib.sha256(data).hexdigest() for name, data in files.items()}) != variant['fixture_sha256']:
        errors.add(where, 'digest', 'fixture_sha256 does not match the input tree')
    sheets = own_sheets(tracked, scenario, variant)
    for name, data in sorted(files.items()):
        if data in sheets or name == 'GROUND-TRUTH.md':
            errors.add(where, 'answer-sheet', 'the input holds the scenario\'s own answer sheet: %s' % name)
    found = exposure_of(files, fragments)
    recorded = {'install': variant['control_exposure']['install'], 'fragments': sorted(variant['control_exposure']['fragments'])}
    if recorded != found:
        errors.add(where, 'exposure', 'recorded %s, found %s' % (json.dumps(recorded), json.dumps(found)))
    if new and (found['install'] or found['fragments']):
        errors.add(where, 'exposure', 'a new or held-out variant must be unexposed')
    elif variant['split'] == 'held-out' and (found['install'] or found['fragments']):
        errors.add(where, 'exposure', 'a held-out variant must be unexposed')
    if new:
        prompts = normalized(' '.join(files[p].decode('utf-8', 'replace') for p in variant['prompts']))
        leading = sorted({f for f in fragments if normalized(f) and normalized(f) in prompts})
        if leading:
            errors.add(where, 'prompt', 'the prompt names the decision under test: %s' % '; '.join(leading))
    return found


def first_commit(repo, digest):
    child = git(repo, 'log', '--format=%H', '--reverse', '-S' + digest, '--', INDEX)
    commits = child.stdout.split()
    return commits[0] if child.returncode == 0 and commits else None


def first_record_commit(repo, episodes, scenario, variant):
    child = git(repo, 'log', '--reverse', '--format=commit %H', '-p', '--unified=0', '--', episodes)
    current = None
    for line in child.stdout.splitlines():
        if line.startswith('commit '):
            current = line.split()[1]
        elif line.startswith('+') and not line.startswith('+++'):
            try:
                record = json.loads(line[1:])
            except ValueError:
                continue
            if isinstance(record, dict) and record.get('scenario_id') == scenario and record.get('variant_id') == variant:
                return current
    return None


def working_records(path, scenario, variant):
    if not path.is_file():
        return False
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and record.get('scenario_id') == scenario and record.get('variant_id') == variant:
            return True
    return False


def check_seals(repo, variants, errors):
    for manifest_path in sorted((repo / 'eval/cohorts').glob('*/manifest.json')):
        cohort = manifest_path.parent
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        except ValueError:
            errors.add('index', 'seal', '%s is unreadable' % manifest_path.relative_to(repo))
            continue
        for entry in manifest.get('variants', []) if isinstance(manifest, dict) else []:
            if not isinstance(entry, dict) or entry.get('split') != 'held-out':
                continue
            key = (entry.get('scenario_id'), entry.get('variant_id'))
            where = '%s/%s' % key
            indexed = variants.get(key)
            if not indexed:
                errors.add(where, 'seal', 'a cohort lists a held-out variant the index does not hold')
                continue
            if entry.get('fixture_sha256') != indexed['fixture_sha256']:
                errors.add(where, 'seal', 'the cohort digest differs from the index digest')
                continue
            episodes = (cohort / 'episodes.jsonl').relative_to(repo).as_posix()
            sealed = first_commit(repo, indexed['fixture_sha256'])
            recorded = first_record_commit(repo, episodes, *key)
            if recorded and (not sealed or sealed == recorded
                             or git(repo, 'merge-base', '--is-ancestor', sealed, recorded).returncode != 0):
                errors.add(where, 'seal', 'a record naming the variant was committed before its sealed digest (%s)' % recorded[:12])
            elif not sealed and working_records(cohort / 'episodes.jsonl', *key):
                errors.add(where, 'seal', 'records name the variant but its digest is not committed')


def check(repo):
    errors = Errors()
    index = load(repo, INDEX, errors)
    ledger = load(repo, LEDGER, errors)
    if index is None or ledger is None:
        return errors, None
    if not isinstance(index, dict) or index.get('schema') != 'tackle-scenario-index/1' or not isinstance(index.get('scenarios'), list):
        errors.add('index', 'schema', 'expected {"schema": "tackle-scenario-index/1", "scenarios": [...]}')
        return errors, None
    fragments = rule_fragments(ledger)
    tracked = Tracked(repo)
    tracked.load(tracked.under('eval/scenarios/'))
    directories = {p.name for p in (repo / 'eval/scenarios').iterdir() if p.is_dir()} if (repo / 'eval/scenarios').is_dir() else set()
    seen, variants_by_key, covered = set(), {}, set()
    counts = dict(scenarios=0, outcome_traps=0, held_out=0, stageable=0, exposed=0)
    held_out_traps = 0
    for number, entry in enumerate(index['scenarios']):
        if not valid_entry(entry):
            errors.add('index', 'schema', 'entry %d is malformed' % number)
            continue
        scenario = entry['scenario_id']
        if scenario in seen:
            errors.add(scenario, 'completeness', 'duplicate index entry')
            continue
        seen.add(scenario)
        counts['scenarios'] += 1
        if scenario not in directories:
            errors.add(scenario, 'completeness', 'no scenario directory')
        if entry['class'] not in CLASSES:
            errors.add(scenario, 'vocabulary', 'class must be one of %s' % ', '.join(CLASSES))
        unknown = sorted(set(map(str, entry['covers'])) - set(GAPS))
        if unknown:
            errors.add(scenario, 'vocabulary', 'unknown gap tags: %s' % ', '.join(unknown))
        covered |= set(entry['covers']) & set(GAPS)
        if entry['class'] == 'outcome-trap':
            counts['outcome_traps'] += 1
            if not entry['harm'].strip():
                errors.add(scenario, 'harm', 'an outcome trap states its harm')
        ids, clean_development, held = set(), False, 0
        for variant in entry['variants']:
            if not valid_variant(variant):
                errors.add(scenario, 'schema', 'a variant is malformed')
                continue
            if variant['variant_id'] in ids:
                errors.add('%s/%s' % (scenario, variant['variant_id']), 'vocabulary', 'duplicate variant id')
                continue
            ids.add(variant['variant_id'])
            variants_by_key[(scenario, variant['variant_id'])] = variant
            found = check_variant(repo, tracked, scenario, variant, fragments.get(scenario, []), errors)
            if variant['stageable']:
                counts['stageable'] += 1
            if variant['control_exposure']['install'] or variant['control_exposure']['fragments']:
                counts['exposed'] += 1
            if variant['split'] == 'held-out':
                counts['held_out'] += 1
                held += variant['stageable']
            if variant['split'] == 'development' and variant['stageable'] and found == {'install': False, 'fragments': []}:
                clean_development = True
        if not ids:
            errors.add(scenario, 'schema', 'an entry lists at least one variant')
        if entry['class'] == 'outcome-trap' and held >= 2:
            held_out_traps += 1
            if not clean_development:
                errors.add(scenario, 'exposure', 'an outcome trap with held-out variants needs an unexposed, stageable '
                           'development variant')
    for directory in sorted(directories - seen):
        errors.add(directory, 'completeness', 'no index entry')
    low, high = HELD_OUT_TRAPS
    if not low <= held_out_traps <= high:
        errors.add('index', 'count', '%d outcome traps carry two held-out variants; %d to %d are required' % (held_out_traps, low, high))
    missing = [gap for gap in GAPS if gap not in covered]
    if missing:
        errors.add('index', 'coverage', 'uncovered gaps: %s' % ', '.join(missing))
    check_seals(repo, variants_by_key, errors)
    summary = 'scenarios=%d outcome_traps=%d held_out=%d stageable=%d exposed=%d gaps=%d/%d' % (
        counts['scenarios'], counts['outcome_traps'], counts['held_out'], counts['stageable'], counts['exposed'],
        len(covered), len(GAPS))
    return errors, summary


def main(argv):
    if len(argv) != 2 or argv[0] not in ('--repo', '--digest'):
        print(USAGE, file=sys.stderr)
        return 2
    target = Path(argv[1])
    if argv[0] == '--digest':
        if not target.is_dir():
            print(USAGE, file=sys.stderr)
            return 2
        try:
            print(tree_digest(target))
        except Symlink as link:
            print('error: symlink: %s' % link)
            return 1
        return 0
    if not target.is_dir() or git(target, 'rev-parse', '--is-inside-work-tree').stdout.strip() != 'true':
        print(USAGE + ' (not a git work tree)', file=sys.stderr)
        return 2
    errors, summary = check(target)
    if errors:
        print('\n'.join(sorted(set(errors))))
        return 1
    print(summary)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
