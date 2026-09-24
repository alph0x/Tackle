"""Check the rule ledger (eval/rules/ledger.json) and the historical index against a repository.

Usage: python3 eval/rules/check_ledger.py --repo <dir>
Exit 0 prints warnings and the summary `rules=<n> hot_path=<n> untested=<n> warnings=<n>`; exit 1 prints
`error: <reason>` lines; exit 2 is a usage error. The repository is only read. LEDGER.md defines the format.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inventory  # noqa: E402

LEDGER_FIELDS = ('schema', 'rules', 'non_normative')
RULE_FIELDS = ('rule_id', 'statement', 'statement_sha256', 'home', 'home_fragment', 'units', 'mirrors', 'class',
               'hot_path', 'origin', 'evidence', 'historical')
OPTIONAL_RULE_FIELDS = ('retired_in',)
ORIGIN_FIELDS = ('added_in', 'trigger', 'discovered_by')
EVIDENCE_FIELDS = ('status', 'scenarios', 'cohort_id', 'as_of')
HISTORICAL_FIELDS = ('record', 'label', 'seeds')
NON_NORMATIVE_FIELDS = ('unit', 'reason')
INDEX_FIELDS = ('schema', 'records')
ENTRY_FIELDS = ('scenario_id', 'recorded_label', 'mapped_label', 'seeds', 'comparison', 'baseline', 'candidate',
                'contamination', 'basis')
ARM_FIELDS = ('outcome', 'seeds')
CLASSES = ('safety-invariant', 'behavioral', 'format', 'maintainer')
LABELS = ('contaminated', 'unobserved', 'method-worse', 'inert', 'discriminates', 'inconclusive')
STATUSES = LABELS + ('untested',)
RULE_ID = re.compile(r'R-(?:ENTRY|INTAKE|PLAN|RUN|EVID|STATE|STATUS|LEARN|MIGRATE|COMM|REL)-\d{2,}')
VERSION = re.compile(r'\d+\.\d+(?:\.\d+)?')
DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
SCENARIO = re.compile(r's\d+-[a-z0-9]+(?:-[a-z0-9]+)*')
SHA256 = re.compile(r'[0-9a-f]{64}')
PLACE = re.compile(r'(.+):([1-9]\d*)')
RECORD = re.compile(r'eval/runs/[^/]+\.md|eval/scenarios/[^/]+/GROUND-TRUTH\.md')
COHORT = re.compile(r'[a-z0-9][a-z0-9._-]*')


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, text):
        self.errors.append(text)


def is_text(value):
    return isinstance(value, str) and value.strip() != ''


def is_count(value):
    return isinstance(value, int) and not isinstance(value, bool)


def fields(report, owner, value, required, optional=()):
    """Report a non-object, missing fields and unknown fields; return True when all required fields exist."""
    if not isinstance(value, dict):
        report.error('%s: must be an object' % owner)
        return False
    for name in value:
        if name not in required and name not in optional:
            report.error('%s: unknown field: %s' % (owner, name))
    missing = [name for name in required if name not in value]
    for name in missing:
        report.error('%s: missing field: %s' % (owner, name))
    return not missing


def relative(path_text):
    path = PurePosixPath(path_text)
    return not path.is_absolute() and '..' not in path.parts and '\\' not in path_text and path_text == str(path)


class Files:
    """Cached line lists of repository files, read only."""

    def __init__(self, repo):
        self.repo, self.cache = repo, {}

    def lines(self, path_text):
        if path_text not in self.cache:
            target = self.repo / path_text
            self.cache[path_text] = target.read_text(encoding='utf-8').splitlines() if target.is_file() else None
        return self.cache[path_text]

    def place(self, text):
        """Return (path, line text) for a path:line reference, or (None, reason)."""
        match = PLACE.fullmatch(text) if isinstance(text, str) else None
        if not match or not relative(match.group(1)):
            return None, 'not a relative path:line'
        found = self.lines(match.group(1))
        if found is None:
            return None, 'no such file'
        number = int(match.group(2))
        if number > len(found):
            return None, 'line past the end of the file'
        return match.group(1), found[number - 1]


def check_index(report, repo, files):
    """Validate historical-index.json; return the parsed index, or None when it cannot be used."""
    path = repo / inventory.INDEX
    if not path.is_file():
        report.error('index: missing %s' % inventory.INDEX)
        return None
    try:
        index = json.loads(path.read_text(encoding='utf-8'))
    except ValueError:
        report.error('index: invalid JSON in %s' % inventory.INDEX)
        return None
    if not fields(report, 'index', index, INDEX_FIELDS):
        return None
    if index['schema'] != 'tackle-historical-index/1':
        report.error('index: schema must be tackle-historical-index/1')
    if not isinstance(index['records'], dict):
        report.error('index: records must be an object')
        return None
    usable = True
    for record, entries in index['records'].items():
        if not RECORD.fullmatch(record) or not relative(record):
            report.error('index: %s: record must be eval/runs/<name>.md or an answer sheet' % record)
        if not isinstance(entries, list) or not entries:
            report.error('index: %s: entries must be a non-empty list' % record)
            usable = False
            continue
        text = files.lines(record)
        seen = set()
        for entry in entries:
            named = isinstance(entry, dict) and isinstance(entry.get('scenario_id'), str)
            owner = 'index: %s: %s' % (record, entry['scenario_id'] if named else '?')
            if not fields(report, owner, entry, ENTRY_FIELDS):
                usable = False
                continue
            usable &= check_entry(report, owner, entry, text)
            if named:
                if entry['scenario_id'] in seen:
                    report.error('%s: duplicate scenario in the record' % owner)
                seen.add(entry['scenario_id'])
    return index if usable else None


def check_basis(report, owner, basis, text):
    """basis: [{line, quote}] with the quote on that record line when the record file is present."""
    if not isinstance(basis, list) or not basis or not all(
            isinstance(b, dict) and set(b) == {'line', 'quote'} and is_count(b['line']) and b['line'] >= 1
            and is_text(b['quote']) for b in basis):
        report.error('%s: basis must list {line, quote} objects' % owner)
        return
    if text is None:
        return
    for item in basis:
        if item['line'] > len(text):
            report.error('%s: basis line %d is past the end of the record' % (owner, item['line']))
        elif item['quote'] not in text[item['line'] - 1]:
            report.error('%s: basis line %d does not contain its quote' % (owner, item['line']))


def check_entry(report, owner, entry, text):
    ok = True
    if not isinstance(entry['scenario_id'], str) or not SCENARIO.fullmatch(entry['scenario_id']):
        report.error('%s: scenario_id must look like s<N>-<name>' % owner)
        ok = False
    if not is_text(entry['recorded_label']):
        report.error('%s: recorded_label must be text' % owner)
        ok = False
    if entry['comparison'] not in inventory.COMPARISONS:
        report.error('%s: comparison must be one of %s' % (owner, ', '.join(inventory.COMPARISONS)))
    arms = {}
    for side in ('baseline', 'candidate'):
        arm = entry[side]
        if not fields(report, '%s: %s' % (owner, side), arm, ARM_FIELDS):
            return False
        if arm['outcome'] not in inventory.OUTCOMES or not is_count(arm['seeds']) or arm['seeds'] < 0:
            report.error('%s: %s needs an outcome in %s and a seed count' % (owner, side, ', '.join(inventory.OUTCOMES)))
            return False
        if (arm['outcome'] == 'absent') != (arm['seeds'] == 0):
            report.error('%s: %s has zero seeds exactly when it is absent' % (owner, side))
        arms[side] = arm
    if (entry['comparison'] == 'method-only') != (arms['baseline']['outcome'] == 'absent'):
        report.error('%s: the baseline is absent exactly for method-only comparisons' % owner)
    contamination = entry['contamination']
    if contamination is not None and not is_text(contamination):
        report.error('%s: contamination must be null or text' % owner)
    if contamination and arms['baseline']['outcome'] in ('absent', 'placeholder'):
        report.error('%s: contamination needs an observed baseline arm' % owner)
    label = inventory.historical_label(arms['baseline']['outcome'], arms['candidate']['outcome'], contamination)
    if entry['mapped_label'] != label:
        report.error('%s: mapped_label %s, expected %s' % (owner, entry['mapped_label'], label))
    seeds = inventory.expected_seeds(arms['baseline']['seeds'], arms['candidate']['seeds'])
    if entry['seeds'] != seeds:
        report.error('%s: seeds %s, expected %s' % (owner, entry['seeds'], seeds))
    check_basis(report, owner, entry['basis'], text)
    if ok and text is not None and entry['recorded_label'] not in '\n'.join(text):
        report.error('%s: recorded_label not found in the record' % owner)
    return ok


def check_rule(report, repo, files, rule, index, position):
    named = isinstance(rule, dict) and isinstance(rule.get('rule_id'), str)
    owner = rule['rule_id'] if named else 'rules[%d]' % position
    if not fields(report, owner, rule, RULE_FIELDS, OPTIONAL_RULE_FIELDS):
        return False
    if not named or not RULE_ID.fullmatch(rule['rule_id']):
        report.error('%s: rule_id must match R-<AREA>-<NN>' % owner)
        if not named:
            return False
    statement = rule['statement']
    if not is_text(statement) or statement != ' '.join(statement.split()):
        report.error('%s: statement must be one normalized line' % owner)
    elif rule['statement_sha256'] != hashlib.sha256(statement.encode('utf-8')).hexdigest():
        report.error('%s: statement_sha256 does not match the statement' % owner)
    if not isinstance(rule['statement_sha256'], str) or not SHA256.fullmatch(rule['statement_sha256']):
        report.error('%s: statement_sha256 must be 64 lowercase hex digits' % owner)
    if rule['class'] not in CLASSES:
        report.error('%s: class must be one of %s' % (owner, ', '.join(CLASSES)))
    retired = 'retired_in' in rule
    if retired and (not isinstance(rule['retired_in'], str) or not VERSION.fullmatch(rule['retired_in'])):
        report.error('%s: retired_in must be a version' % owner)
    units, mirrors = rule['units'], rule['mirrors']
    if not isinstance(units, list) or not all(is_text(u) for u in units):
        report.error('%s: units must be a list of coverage keys' % owner)
        units = []
    home = rule['home']
    home_path = home.rsplit(':', 1)[0] if isinstance(home, str) else None
    fragment = rule['home_fragment']
    if not is_text(fragment) or len(fragment) > 60:
        report.error('%s: home_fragment must be 1 to 60 characters' % owner)
    elif not retired:
        path, line = files.place(home)
        if path is None:
            report.error('%s: unresolved home %s: %s' % (owner, home, line))
        elif fragment not in line:
            report.error('%s: unresolved home %s: fragment not on the line' % (owner, home))
    if not isinstance(mirrors, list):
        report.error('%s: mirrors must be a list' % owner)
    else:
        for mirror in mirrors:
            if files.place(mirror)[0] is None:
                report.error('%s: unresolved mirror %s' % (owner, mirror))
    if not isinstance(rule['hot_path'], bool):
        report.error('%s: hot_path must be a boolean' % owner)
    elif retired and rule['hot_path']:
        report.error('%s: hot_path must be false because the rule is retired' % owner)
    elif not retired and rule['hot_path'] != (home_path == 'SKILL.md'):
        report.error('%s: hot_path must be %s because the home is %sSKILL.md'
                     % (owner, str(home_path == 'SKILL.md').lower(), '' if home_path == 'SKILL.md' else 'not '))
    if units and (home_path != 'SKILL.md' or retired):
        report.error('%s: units need a SKILL.md home' % owner)
    scenarios = check_origin_and_evidence(report, repo, owner, rule)
    historical = rule['historical']
    if not isinstance(historical, list) or not all(isinstance(h, dict) and set(h) == set(HISTORICAL_FIELDS)
                                                   for h in historical):
        report.error('%s: historical entries need exactly record, label and seeds' % owner)
    elif index is not None and scenarios is not None and historical != inventory.projection(index, scenarios):
        report.error('%s: historical does not match the index for its scenarios' % owner)
    return True


def check_cohort(report, repo, owner, cohort):
    """A tested status must name a protocol v2 cohort directory whose manifest carries the same id."""
    manifest = repo / 'eval/cohorts' / cohort / 'manifest.json'
    if not COHORT.fullmatch(cohort) or not manifest.is_file():
        report.error('%s: cohort %s has no eval/cohorts/%s/manifest.json' % (owner, cohort, cohort))
        return
    try:
        named = json.loads(manifest.read_text(encoding='utf-8')).get('cohort_id')
    except (ValueError, AttributeError):
        named = None
    if named != cohort:
        report.error('%s: eval/cohorts/%s/manifest.json names cohort %s' % (owner, cohort, named))


def check_origin_and_evidence(report, repo, owner, rule):
    """Validate origin and evidence; return the evidence scenario set, or None when it is unusable."""
    origin, evidence = rule['origin'], rule['evidence']
    known = []
    if fields(report, '%s: origin' % owner, origin, ORIGIN_FIELDS):
        added = origin['added_in']
        if not isinstance(added, str) or not (added == 'unknown' or VERSION.fullmatch(added)):
            report.error('%s: added_in must be a version or unknown' % owner)
        if not is_text(origin['trigger']):
            report.error('%s: trigger must be text' % owner)
        known.append(('discovered_by', origin['discovered_by']))
    if not fields(report, '%s: evidence' % owner, evidence, EVIDENCE_FIELDS):
        return None
    known.append(('scenarios', evidence['scenarios']))
    for name, ids in known:
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            report.error('%s: %s must be a list of scenario ids' % (owner, name))
            return None
        for scenario in ids:
            if not SCENARIO.fullmatch(scenario) or not (repo / 'eval/scenarios' / scenario).is_dir():
                report.error('%s: unknown scenario: %s' % (owner, scenario))
    status, cohort = evidence['status'], evidence['cohort_id']
    if status not in STATUSES:
        report.error('%s: status must be one of %s' % (owner, ', '.join(STATUSES)))
    if status == 'untested' and cohort is not None:
        report.error('%s: status untested requires cohort_id null' % owner)
    if status != 'untested' and not is_text(cohort):
        report.error('%s: a tested status requires a cohort_id' % owner)
    elif status != 'untested':
        check_cohort(report, repo, owner, cohort)
    if not isinstance(evidence['as_of'], str) or not DATE.fullmatch(evidence['as_of']):
        report.error('%s: as_of must be YYYY-MM-DD' % owner)
    scenarios = set(evidence['scenarios'])
    discovered = set(origin['discovered_by']) if isinstance(origin, dict) and isinstance(origin.get('discovered_by'),
                                                                                        list) else set()
    if status == 'discriminates' and not scenarios - discovered:
        report.error('%s: discriminates rests only on discovering scenarios: %s'
                     % (owner, ', '.join(sorted(scenarios)) or 'none'))
    return scenarios


def check_coverage(report, repo, rules, non_normative):
    try:
        found = inventory.units((repo / 'SKILL.md').read_text(encoding='utf-8'))
    except OSError:
        report.error('SKILL.md: missing')
        return
    except inventory.UnitError as error:
        report.error('SKILL.md: %s' % error)
        return
    by_key = {}
    for unit in found:
        by_key.setdefault(unit['key'], []).append(unit)
    for unit_key, same in by_key.items():
        if len(same) > 1:
            report.error('ambiguous key: %s: %s' % (', '.join('SKILL.md:%d' % u['line'] for u in same), unit_key))
    owners = {}
    for owner, keys in [(r['rule_id'], r['units']) for r in rules] + [('non_normative[%d]' % i, [n['unit']])
                                                                         for i, n in enumerate(non_normative)]:
        for unit_key in keys:
            owners.setdefault(unit_key, []).append(owner)
    for unit_key, same in by_key.items():
        claimed = owners.get(unit_key, [])
        if not claimed:
            report.error('uncovered: SKILL.md:%d: %s' % (same[0]['line'], unit_key))
        elif len(claimed) > 1:
            report.error('double coverage: SKILL.md:%d: %s (%s)' % (same[0]['line'], unit_key, ', '.join(claimed)))
    for unit_key, claimed in owners.items():
        if unit_key not in by_key:
            for owner in claimed:
                report.error('stale unit: %s: %s' % (owner, unit_key))


def check(repo):
    report, files = Report(), Files(repo)
    index = check_index(report, repo, files)
    path = repo / inventory.LEDGER
    if not path.is_file():
        report.error('ledger: missing %s' % inventory.LEDGER)
        return report, None
    try:
        ledger = json.loads(path.read_text(encoding='utf-8'))
    except ValueError:
        report.error('ledger: invalid JSON in %s' % inventory.LEDGER)
        return report, None
    if not fields(report, 'ledger', ledger, LEDGER_FIELDS):
        return report, None
    if ledger['schema'] != 'tackle-rule-ledger/1':
        report.error('ledger: schema must be tackle-rule-ledger/1')
    rules, non_normative = ledger['rules'], ledger['non_normative']
    if not isinstance(rules, list) or not isinstance(non_normative, list):
        report.error('ledger: rules and non_normative must be lists')
        return report, None
    valid, seen = [], set()
    for position, rule in enumerate(rules):
        if check_rule(report, repo, files, rule, index, position):
            if rule['rule_id'] in seen:
                report.error('duplicate rule_id: %s' % rule['rule_id'])
            seen.add(rule['rule_id'])
            valid.append(rule)
    notes = []
    for i, note in enumerate(non_normative):
        if fields(report, 'non_normative[%d]' % i, note, NON_NORMATIVE_FIELDS):
            if not is_text(note['unit']) or not is_text(note['reason']):
                report.error('non_normative[%d]: unit and reason must be text' % i)
            else:
                notes.append(note)
    check_coverage(report, repo, [r for r in valid if isinstance(r['units'], list)
                                  and all(isinstance(u, str) for u in r['units'])], notes)
    for rule in valid:
        if (rule['hot_path'] is True and rule['class'] != 'safety-invariant'
                and isinstance(rule['evidence'], dict) and rule['evidence'].get('status') != 'discriminates'):
            report.warnings.append('%s: hot-path rule is neither safety-invariant nor discriminates' % rule['rule_id'])
    summary = 'rules=%d hot_path=%d untested=%d warnings=%d' % (
        len(valid), sum(1 for r in valid if r['hot_path'] is True),
        sum(1 for r in valid if isinstance(r['evidence'], dict) and r['evidence'].get('status') == 'untested'),
        len(report.warnings))
    return report, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description='Check the rule ledger against a repository.')
    parser.add_argument('--repo', required=True)
    args = parser.parse_args(argv)
    repo = Path(args.repo)
    if not repo.is_dir():
        print('usage: --repo must be a directory: %s' % repo, file=sys.stderr)
        return 2
    report, summary = check(repo)
    for warning in report.warnings:
        print('warning: ' + warning)
    for error in report.errors:
        print('error: ' + error)
    if report.errors:
        return 1
    print(summary)
    return 0


if __name__ == '__main__':
    sys.exit(main())
