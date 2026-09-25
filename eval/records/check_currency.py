"""Check that behavioral claims rest on tracked, pinned and leak-free records.

Usage: python3 eval/records/check_currency.py --repo <dir>
Exit 0 current, 1 violations (one ``error:`` line each), 2 usage or not a git work tree.
Tracked inputs are read from the git index, so the check covers what a commit would contain; only
local-only originals are read from the working tree. The checker never writes inside the repository.
The layout it checks is described in ``eval/records/README.md``.
"""
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

USAGE = 'usage: check_currency.py --repo <dir>'
HERE = Path(__file__).resolve().parent
PROTOCOL = HERE.parent / 'protocol-v2' / 'check.py'
HASHES, CLAIMS = 'eval/records/historical-hashes.json', 'eval/records/claims.json'
INDEX, LEDGER = 'eval/rules/historical-index.json', 'eval/rules/ledger.json'
SOURCES = ('CHANGELOG.md', 'README.md')
RECORD_DIRS = ('eval/runs/', 'eval/records/sanitized/')
SCANNED_DIRS = RECORD_DIRS + ('eval/cohorts/',)
ANSWER_SHEET = re.compile(r'eval/scenarios/([^/]+)/GROUND-TRUTH\.md')
METHOD_PATH = '~/.tackle/'
UNIT = re.compile(r'(?<![A-Za-z0-9_])s(\d{1,2})(?:`?\s*[–-]\s*`?s(\d{1,2}))?(?![0-9])')
OUTCOME = re.compile(r'\b(verdicts?|discriminat\w*|nulls?|inert|inconclusive|avoid(?:ed|s)|fell|falls|fired|fires|'
                     r'caught|passed|(?:re)?validated|trap-hit|flaky|method-worse|contaminated)\b', re.I)
SECTION_VERSION = re.compile(r'Tackle (\d+)\.(\d+)(?:\.(\d+))?$')
DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
FILE_DATE = re.compile(r'(\d{4}-\d{2}-\d{2})-')
HEX = re.compile(r'[0-9a-f]{64}')
ENTRY_FIELDS = {'sha256', 'bytes', 'tracked', 'recorded_on', 'retired_scenarios'}
KINDS = {'record': 'records', 'cohort': 'cohort', 'no-record': 'reason', 'mention': 'reason'}
NOTE = 'note: deterministic checks verify records, fixtures and harnesses, not agent behavior'


class Errors(list):
    def add(self, path, code, text):
        self.append('error: %s: %s: %s' % (path, code, text))


class Index:
    """The git index of the checked repository: paths, and the staged bytes of any path."""

    def __init__(self, repo):
        self.repo = repo
        child = subprocess.run(['git', '-C', str(repo), 'ls-files', '-s', '-z'], capture_output=True)
        self.ok = child.returncode == 0
        self.blobs = {}
        for row in child.stdout.split(b'\0') if self.ok else []:
            if row:
                meta, _, path = row.partition(b'\t')
                mode, blob, stage = meta.split(b' ')
                if stage == b'0':
                    self.blobs[path.decode('utf-8', 'surrogateescape')] = blob.decode()
        self.cache = {}

    def __contains__(self, path):
        return path in self.blobs

    def paths(self):
        return sorted(self.blobs)

    def read(self, path):
        if path not in self.cache:
            child = subprocess.run(['git', '-C', str(self.repo), 'cat-file', 'blob', self.blobs[path]],
                                   capture_output=True, check=True)
            self.cache[path] = child.stdout
        return self.cache[path]

    def text(self, path):
        return self.read(path).decode('utf-8', 'replace')

    def export(self, prefix, destination):
        """Write every staged file under ``prefix`` to ``destination`` (for tools that read directories)."""
        names = [path for path in self.paths() if path.startswith(prefix)]
        subprocess.run(['git', '-C', str(self.repo), 'checkout-index', '-z', '--stdin', '--prefix=%s/' % destination],
                       input='\0'.join(names).encode(), capture_output=True, check=True)


def load_leaks():
    spec = importlib.util.spec_from_file_location('protocol_v2_check', PROTOCOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.LEAKS


def release_dates(repo):
    child = subprocess.run(['git', '-C', str(repo), 'for-each-ref', '--format=%(refname:short) %(creatordate:short)',
                            'refs/tags'], capture_output=True, text=True)
    dates = {}
    for row in child.stdout.splitlines():
        name, _, date = row.partition(' ')
        if name.startswith('v') and DATE.fullmatch(date):
            dates[name] = date
    return dates


def read_map(index, path, errors):
    if path not in index:
        errors.add(path, 'untracked', 'required map is not in the git index')
        return None
    try:
        return json.loads(index.text(path))
    except ValueError as problem:
        errors.add(path, 'schema', 'unreadable JSON (%s)' % problem.__class__.__name__)
        return None


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def scenario_number(text):
    match = re.match(r's(\d+)', text)
    return int(match[1]) if match else None


def version_of(section):
    match = SECTION_VERSION.fullmatch(section or '')
    return None if not match else (int(match[1]), int(match[2]), int(match[3] or 0))


def scan_units(index, errors):
    units = {}
    for source in SOURCES:
        if source not in index:
            errors.add(source, 'untracked', 'claim source is not in the git index')
            continue
        section, fence = None, None
        for line in index.text(source).splitlines():
            stripped = line.strip()
            opener = re.match(r'(`{3,}|~{3,})', stripped)
            if opener:
                if fence is None:
                    fence = opener[1]
                elif set(stripped) == {fence[0]} and len(stripped) >= len(fence):
                    fence = None
                continue
            if fence:
                continue
            if line.startswith('## '):
                section = line[3:].strip()
                continue
            for match in UNIT.finditer(line):
                unit = 's%s' % match[1] + ('–s%s' % match[2] if match[2] else '')
                units.setdefault((source, section, unit), []).append(line)
    return units


def leaks_in(text, path, leaks):
    if ANSWER_SHEET.fullmatch(path) or path == LEDGER:
        text = text.replace(METHOD_PATH, '')
    return [pattern.pattern for pattern in leaks if pattern.search(text)]


def check_hashes(repo, index, hashes, leaks, errors):
    if not isinstance(hashes, dict) or hashes.get('schema') != 'tackle-historical-hashes/1' or \
            not isinstance(hashes.get('records'), dict):
        errors.add(HASHES, 'schema', 'expected {"schema": "tackle-historical-hashes/1", "records": {...}}')
        return {}
    entries = {}
    for path, entry in hashes['records'].items():
        extra = {'sanitized_copy'} if isinstance(entry, dict) and entry.get('tracked') is False else set()
        extra |= {'source', 'source_sha256'} if isinstance(entry, dict) and 'source' in entry else set()
        if not isinstance(entry, dict) or set(entry) != ENTRY_FIELDS | extra or not HEX.fullmatch(str(entry['sha256'])) \
                or not isinstance(entry['bytes'], int) or isinstance(entry['bytes'], bool) or entry['bytes'] < 0 \
                or not isinstance(entry['tracked'], bool) or not DATE.fullmatch(str(entry['recorded_on'])) \
                or not isinstance(entry['retired_scenarios'], list) \
                or not all(isinstance(s, str) and s for s in entry['retired_scenarios']):
            errors.add(path, 'schema', 'invalid hashes entry')
            continue
        entries[path] = entry
        dated = FILE_DATE.match(Path(path).name)
        if dated and dated[1] != entry['recorded_on']:
            errors.add(path, 'recorded-on', 'recorded_on must equal the file-name date %s' % dated[1])
        data = None
        if entry['tracked']:
            if path not in index:
                errors.add(path, 'untracked', 'pinned as tracked but absent from the git index')
                continue
            data = index.read(path)
            if sha256(data) != entry['sha256'] or len(data) != entry['bytes']:
                errors.add(path, 'hash', 'staged bytes differ from the pinned sha256')
                continue
        elif path in index:
            errors.add(path, 'tracked-original', 'a local-only original is in the git index')
            continue
        elif (repo / path).is_file():
            data = (repo / path).read_bytes()
            if sha256(data) != entry['sha256']:
                errors.add(path, 'hash', 'local original differs from the pinned sha256')
                continue
            if not leaks_in(data.decode('utf-8', 'replace'), path, leaks):
                errors.add(path, 'should-be-tracked', 'a local-only original must carry a leak; track it instead')
        if not dated and data is not None and entry['recorded_on'] not in data.decode('utf-8', 'replace'):
            errors.add(path, 'recorded-on', 'a record without a file-name date must state its recorded_on date')
    for path, entry in entries.items():
        if entry['tracked'] is False:
            copy = entries.get(entry['sanitized_copy'])
            if not copy or not copy['tracked'] or copy.get('source') != path:
                errors.add(path, 'sanitized', 'needs a tracked sanitized copy that names it as its source')
            elif copy['sha256'] == entry['sha256']:
                errors.add(path, 'should-be-tracked', 'its sanitized copy is identical, so nothing needed sanitizing')
        if 'source' in entry:
            origin = entries.get(entry['source'])
            if not origin or origin['tracked'] or origin.get('sanitized_copy') != path \
                    or entry['source_sha256'] != origin['sha256']:
                errors.add(path, 'sanitized', 'source must be a local-only original naming this copy')
    return entries


def scenarios_of(path, entries, index_map):
    entry = entries.get(path, {})
    origin = entry.get('source', path)
    names = [item.get('scenario_id') for item in index_map.get(origin, []) if isinstance(item, dict)]
    sheet = ANSWER_SHEET.fullmatch(origin)
    return names + [sheet[1]] if sheet else names


def check_coverage(index, entries, index_map, errors):
    for path in sorted(index_map):
        if path not in entries:
            errors.add(path, 'unledgered', 'historical-index record without a hashes entry')
    for path in index.paths():
        if path.startswith(RECORD_DIRS) and path not in entries:
            errors.add(path, 'unledgered', 'tracked record without a hashes entry')
    scenario_dirs = {path.split('/')[2] for path in index.paths() if path.startswith('eval/scenarios/') and path.count('/') >= 3}
    retired, lines = 0, []
    for path, entry in sorted(entries.items()):
        if 'source' in entry:
            continue
        missing = sorted({s for s in scenarios_of(path, entries, index_map) if isinstance(s, str) and s not in scenario_dirs})
        if missing != sorted(set(entry['retired_scenarios'])):
            errors.add(path, 'retired', 'retired_scenarios must be %s' % (missing or '[]'))
        elif missing:
            retired += 1
            lines.append('retired: %s: %s' % (path, ', '.join(missing)))
    return retired, lines


def check_leaks(index, entries, leaks, errors):
    pinned = {path for path, entry in entries.items() if entry['tracked']}
    for path in index.paths():
        if path.startswith(SCANNED_DIRS) or path in pinned or path in (HASHES, CLAIMS, INDEX, LEDGER):
            found = leaks_in(index.text(path), path, leaks)
            if found:
                errors.add(path, 'leak', 'carries a path, key or address (%s)' % ', '.join(found))


def check_cohort_dirs(index, errors):
    cohorts = sorted({path.split('/')[2] for path in index.paths() if path.startswith('eval/cohorts/') and path.count('/') >= 3})
    valid = {}
    if not cohorts:
        return valid
    with tempfile.TemporaryDirectory(prefix='tackle-currency-') as staged:
        index.export('eval/cohorts/', staged)
        for cohort in cohorts:
            directory = Path(staged) / 'eval/cohorts' / cohort
            child = subprocess.run([sys.executable, str(PROTOCOL), str(directory)], capture_output=True, text=True)
            if child.returncode:
                errors.add('eval/cohorts/%s' % cohort, 'cohort', 'protocol-v2 check exited %d' % child.returncode)
                continue
            try:
                valid[cohort] = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
            except ValueError:
                errors.add('eval/cohorts/%s' % cohort, 'cohort', 'unreadable manifest')
    return valid


def check_claims(claims, units, entries, index_map, dates, cohorts, errors):
    counts = dict.fromkeys(KINDS, 0)
    if not isinstance(claims, dict) or claims.get('schema') != 'tackle-claims/1' or \
            not isinstance(claims.get('claims'), list) or not isinstance(claims.get('gate_version'), str) or \
            version_of('Tackle ' + claims['gate_version']) is None:
        errors.add(CLAIMS, 'schema', 'expected {"schema": "tackle-claims/1", "gate_version": "X.Y.Z", "claims": [...]}')
        return counts, 0
    gate = version_of('Tackle ' + claims['gate_version'])
    seen = {}
    needs_tags = False
    for number, claim in enumerate(claims['claims']):
        where = '%s#%d' % (CLAIMS, number)
        if not isinstance(claim, dict) or claim.get('kind') not in KINDS or \
                set(claim) != {'source', 'section', 'unit', 'kind', KINDS[claim['kind']]} or \
                not all(isinstance(claim[key], str) and claim[key] for key in ('source', 'section', 'unit')):
            errors.add(where, 'schema', 'invalid claim entry')
            continue
        key = (claim['source'], claim['section'], claim['unit'])
        label = '%s [%s] %s' % key
        if key in seen:
            errors.add(where, 'duplicate', '%s is already classified' % label)
            continue
        seen[key] = claim
        if key not in units:
            errors.add(where, 'stale', '%s no longer appears' % label)
            continue
        counts[claim['kind']] += 1
        kind = claim['kind']
        version = version_of(claim['section'])
        after_gate = version is None or version > gate
        if kind in ('no-record', 'mention'):
            if not isinstance(claim['reason'], str) or not claim['reason'].strip():
                errors.add(where, kind, '%s needs a reason' % label)
            elif kind == 'no-record' and after_gate:
                errors.add(where, 'no-record', '%s is allowed only in sections released at or before %s'
                           % (label, claims['gate_version']))
            elif kind == 'mention' and after_gate and any(OUTCOME.search(line) for line in units[key]):
                errors.add(where, 'mention-outcome', '%s: a line naming it states a run result; back it with a '
                           'record or a cohort' % label)
            continue
        number_of = scenario_number(claim['unit'])
        if kind == 'cohort':
            cohort = claim['cohort']
            manifest = cohorts.get(cohort) if isinstance(cohort, str) else None
            if not manifest or manifest.get('cohort_id') != cohort or not any(
                    isinstance(v, dict) and scenario_number(str(v.get('scenario_id', ''))) == number_of
                    for v in manifest.get('variants', [])):
                errors.add(where, 'cohort', '%s needs a tracked, valid cohort listing the scenario' % label)
            continue
        records = claim['records']
        if not isinstance(records, list) or not records:
            errors.add(where, 'record', '%s needs at least one record' % label)
            continue
        release = None
        if version is not None:
            needs_tags = True
            release = dates.get('v%d.%d.%d' % version)
        for path in records:
            entry = entries.get(path) if isinstance(path, str) else None
            if not entry or not entry['tracked']:
                errors.add(where, 'record', '%s: %r is not a tracked, pinned record' % (label, path))
                continue
            names = scenarios_of(path, entries, index_map)
            if '–' in claim['unit'] or not any(isinstance(s, str) and scenario_number(s) == number_of for s in names):
                errors.add(where, 'wrong-scenario', '%s: %s does not name the scenario' % (label, path))
            if release and entry['recorded_on'] > release:
                errors.add(where, 'record-after-release', '%s: %s is dated %s, after the %s release'
                           % (label, path, entry['recorded_on'], release))
    for key in sorted(set(units) - set(seen), key=str):
        errors.add(key[0], 'unmapped', '[%s] %s has no claim entry' % (key[1], key[2]))
    if needs_tags and not dates:
        errors.add('.git', 'tags-missing', 'record claims need release tags; fetch them (fetch-depth: 0)')
    return counts, len(seen)


def main(argv):
    if len(argv) != 2 or argv[0] != '--repo':
        print(USAGE, file=sys.stderr)
        return 2
    repo = Path(argv[1])
    index = Index(repo) if repo.is_dir() else None
    if index is None or not index.ok:
        print(USAGE + ' (not a git work tree)', file=sys.stderr)
        return 2
    errors = Errors()
    leaks = load_leaks()
    hashes = read_map(index, HASHES, errors)
    claims = read_map(index, CLAIMS, errors)
    index_data = read_map(index, INDEX, errors)
    index_map = index_data.get('records') if isinstance(index_data, dict) else None
    if index_data is not None and not isinstance(index_map, dict):
        errors.add(INDEX, 'schema', 'expected {"records": {...}}')
    index_map = index_map if isinstance(index_map, dict) else {}
    entries = check_hashes(repo, index, hashes, leaks, errors) if hashes is not None else {}
    retired, retired_lines = check_coverage(index, entries, index_map, errors)
    check_leaks(index, entries, leaks, errors)
    cohorts = check_cohort_dirs(index, errors)
    units = scan_units(index, errors)
    counts, total = check_claims(claims, units, entries, index_map, release_dates(repo), cohorts, errors) \
        if claims is not None else (dict.fromkeys(KINDS, 0), 0)
    if errors:
        print('\n'.join(errors))
        return 1
    tracked_count = sum(1 for entry in entries.values() if entry['tracked'])
    print('records=%d tracked=%d local_only=%d claims=%d record=%d cohort=%d no_record=%d mention=%d retired=%d' % (
        len(entries), tracked_count, len(entries) - tracked_count, total, counts['record'], counts['cohort'],
        counts['no-record'], counts['mention'], retired))
    for line in retired_lines:
        print(line)
    print(NOTE)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
