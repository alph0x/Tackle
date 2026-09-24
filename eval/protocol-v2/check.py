"""Validate a tackle-cohort/1 directory against PROTOCOL.md and print its verdicts.

Usage: python3 eval/protocol-v2/check.py <cohort-dir> [--json]
Exit 0 valid, 1 invalid, 2 usage. The cohort directory is only read.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verdict  # noqa: E402

USAGE = 'usage: check.py <cohort-dir> [--json]'
ZERO = '0' * 64
HEX = re.compile(r'[0-9a-f]{64}')
ISO = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z')
ARM = re.compile(r'control|method|method:[a-z0-9-]+|ablation:[A-Za-z0-9-]+')
COMPARISON_ID = re.compile(r'[a-z0-9-]+')
LEAKS = [re.compile(p) for p in (r'/Users/', r'/home/', r'/root/', r'/private/', r'/var/folders/', r'~/',
                                 r'[A-Za-z]:\\', r'-----BEGIN [A-Z ]*PRIVATE KEY-----', r'sk-[A-Za-z0-9]{20,}',
                                 r'[^@ ]+@[^@ ]+[.][A-Za-z]{2,}')]
MANIFEST_FIELDS = ('schema', 'cohort_id', 'hypothesis', 'primary_metric', 'decision_rule', 'n_min', 'seeds', 'variants',
                   'arms', 'comparisons', 'executor', 'judge', 'artifacts', 'oracle_sha256', 'order', 'created_at', 'seal_sha256')
EPISODE_FIELDS = ('schema', 'cohort_id', 'episode_id', 'prev_sha256', 'scenario_id', 'variant_id', 'split', 'arm', 'seed',
                  'order_index', 'artifact_sha256', 'executor', 'roles', 'judge', 'rule_exposure', 'outcome', 'invalid_reason',
                  'scores', 'cost', 'transcript_sha256', 'started_at', 'finished_at')
VARIANT_FIELDS = ('scenario_id', 'variant_id', 'split', 'class', 'fixture_sha256')
ORDER_FIELDS = ('episode_id', 'scenario_id', 'variant_id', 'arm', 'seed')
ROLE_FIELDS = ('role', 'tier', 'model', 'effort', 'tokens_in', 'tokens_out')
SCORE_FIELDS = ('correct_action', 'evidence', 'verification_honesty', 'report_quality')
COST_FIELDS = ('tokens_in', 'tokens_out', 'wall_seconds', 'tool_calls', 'files_written')
OUTCOMES = ('fell', 'avoided', 'invalid', 'unobserved', 'timeout', 'error')
SPLITS = ('development', 'held-out')
CLASSES = ('outcome-trap', 'procedure', 'tripwire')
TIERS = ('fast', 'standard', 'frontier', 'n/a')
EFFORTS = ('low', 'medium', 'high', 'max', 'n/a')
MANIFEST, EPISODES = 'manifest.json', 'episodes.jsonl'


class Report:
    """Collects `error: <file>:<line>: <code>: <text>` findings for one file position."""

    def __init__(self):
        self.errors = []

    def at(self, file, line):
        return Position(self, file, line)


class Position:
    def __init__(self, report, file, line):
        self.report, self.file, self.line = report, file, line

    def add(self, code, text):
        self.report.errors.append(dict(file=self.file, line=self.line, code=code, text=text))

    def expect(self, ok, text, code='schema'):
        if not ok:
            self.add(code, text)
        return bool(ok)

    def closed(self, obj, fields, where):
        """Require exactly `fields`; return True only when every field is present."""
        if not isinstance(obj, dict):
            self.add('schema', where + ' must be an object')
            return False
        for key in fields:
            if key not in obj:
                self.add('schema', where + ' is missing ' + key)
        for key in obj:
            if key not in fields:
                self.add('unknown-field', where + ' has unknown field ' + str(key))
        return all(key in obj for key in fields)


def is_int(value, minimum):
    return type(value) is int and value >= minimum


def count_or_na(value):
    return value == 'n/a' or is_int(value, 0)


def is_text(value):
    return isinstance(value, str) and value != ''


def is_hex(value):
    return isinstance(value, str) and HEX.fullmatch(value) is not None


def is_time(value):
    return isinstance(value, str) and ISO.fullmatch(value) is not None


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def canonical_seal(manifest):
    body = {key: value for key, value in manifest.items() if key != 'seal_sha256'}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def check_variants(entries, at):
    variants = {}
    if not at.expect(isinstance(entries, list) and entries, 'variants must be a non-empty list'):
        return variants
    for entry in entries:
        if not at.closed(entry, VARIANT_FIELDS, 'variant'):
            continue
        good = (is_text(entry['scenario_id']) and is_text(entry['variant_id']) and entry['split'] in SPLITS
                and entry['class'] in CLASSES and is_hex(entry['fixture_sha256']))
        if at.expect(good, 'invalid variant entry'):
            key = (entry['scenario_id'], entry['variant_id'])
            at.expect(key not in variants, 'duplicate variant ' + '/'.join(key), 'duplicate')
            variants[key] = entry
    return variants


def check_comparisons(entries, arms, at):
    comparisons = {}
    if not at.expect(isinstance(entries, list), 'comparisons must be a list'):
        return comparisons
    for entry in entries:
        if not at.closed(entry, ('id', 'baseline_arm', 'candidate_arm'), 'comparison'):
            continue
        if not at.expect(isinstance(entry['id'], str) and COMPARISON_ID.fullmatch(entry['id']), 'invalid comparison id'):
            continue
        at.expect(entry['id'] not in comparisons, 'duplicate comparison ' + entry['id'], 'duplicate')
        for side in ('baseline_arm', 'candidate_arm'):
            at.expect(isinstance(entry[side], str) and entry[side] in arms,
                      'comparison %s names undeclared arm %s' % (entry['id'], entry[side]), 'mismatch')
        comparisons[entry['id']] = entry
    if {'control', 'method'} <= arms:
        primary = comparisons.get('primary')
        at.expect(primary is not None and (primary['baseline_arm'], primary['candidate_arm']) == ('control', 'method'),
                  'arms control and method require comparison primary = control -> method', 'mismatch')
    return comparisons


def check_order(entries, variants, arms, seeds, at):
    order = []
    if not at.expect(isinstance(entries, list) and entries, 'order must be a non-empty list'):
        return order
    seen = set()
    for entry in entries:
        if not at.closed(entry, ORDER_FIELDS, 'order entry'):
            continue
        if not at.expect(all(is_text(entry[k]) for k in ('episode_id', 'scenario_id', 'variant_id', 'arm'))
                         and is_int(entry['seed'], 1), 'invalid order entry'):
            continue
        identity = entry['episode_id']
        at.expect(identity not in seen, 'duplicate order entry %s' % identity, 'duplicate')
        seen.add(identity)
        at.expect((entry['scenario_id'], entry['variant_id']) in variants, 'order entry %s names an unlisted variant' % identity, 'unlisted')
        at.expect(entry['arm'] in arms, 'order entry %s names an undeclared arm' % identity, 'mismatch')
        at.expect(entry['seed'] in seeds, 'order entry %s names an undeclared seed' % identity, 'mismatch')
        order.append(entry)
    return order


def check_manifest(manifest, report):
    at = report.at(MANIFEST, 0)
    if not at.closed(manifest, MANIFEST_FIELDS, 'manifest'):
        return None
    m = manifest
    at.expect(m['schema'] == 'tackle-cohort/1', 'schema must be tackle-cohort/1')
    for key in ('cohort_id', 'hypothesis', 'primary_metric', 'decision_rule'):
        at.expect(is_text(m[key]), key + ' must be a non-empty string')
    at.expect(is_int(m['n_min'], 1), 'n_min must be an integer >= 1')
    seeds = m['seeds'] if isinstance(m['seeds'], list) else []
    at.expect(seeds and all(is_int(s, 1) for s in seeds) and len(set(seeds)) == len(seeds), 'seeds must be distinct integers >= 1')
    variants = check_variants(m['variants'], at)
    arms_ok = at.expect(isinstance(m['arms'], list) and m['arms'] and all(isinstance(a, str) and ARM.fullmatch(a) for a in m['arms'])
                        and len(set(m['arms'])) == len(m['arms']), 'arms must be distinct arm names')
    arms = set(m['arms']) if arms_ok else set()
    comparisons = check_comparisons(m['comparisons'], arms, at)
    for key, fields in (('executor', ('harness', 'model', 'effort')), ('judge', ('model_family', 'blinded')),
                        ('artifacts', ('baseline_sha256', 'candidate_sha256'))):
        at.closed(m[key], fields, key)
    if isinstance(m['executor'], dict):
        at.expect(all(isinstance(v, str) for v in m['executor'].values()), 'executor values must be strings')
    if isinstance(m['judge'], dict):
        at.expect(isinstance(m['judge'].get('model_family'), str) and type(m['judge'].get('blinded')) is bool, 'invalid judge')
    if isinstance(m['artifacts'], dict):
        at.expect(all(is_hex(v) for v in m['artifacts'].values()), 'artifact hashes must be sha256 hex')
    at.expect(is_hex(m['oracle_sha256']), 'oracle_sha256 must be sha256 hex')
    at.expect(is_time(m['created_at']), 'created_at must be ISO-8601 UTC')
    order = check_order(m['order'], variants, arms, seeds, at)
    if at.expect(is_hex(m['seal_sha256']), 'seal_sha256 must be sha256 hex'):
        at.expect(m['seal_sha256'] == canonical_seal(m), 'seal_sha256 does not match the manifest', 'seal')
    return dict(variants=variants, arms=arms, seeds=seeds, order=order, comparisons=comparisons,
                n_min=m['n_min'] if is_int(m['n_min'], 1) else 1, cohort_id=m['cohort_id'])


def check_fields(r, at):
    at.expect(r['schema'] == 'tackle-episode/1', 'schema must be tackle-episode/1')
    for key in ('cohort_id', 'episode_id', 'scenario_id', 'variant_id'):
        at.expect(is_text(r[key]), key + ' must be a non-empty string')
    at.expect(is_hex(r['prev_sha256']), 'prev_sha256 must be sha256 hex')
    at.expect(r['split'] in SPLITS, 'invalid split')
    at.expect(isinstance(r['arm'], str) and ARM.fullmatch(r['arm']), 'invalid arm')
    at.expect(is_int(r['seed'], 1), 'seed must be an integer >= 1')
    at.expect(is_int(r['order_index'], 0), 'order_index must be an integer >= 0')
    if at.expect(r['artifact_sha256'] is None or is_hex(r['artifact_sha256']), 'artifact_sha256 must be sha256 hex or null'):
        at.expect(r['artifact_sha256'] is not None or r['arm'] == 'control', 'only a control record may omit artifact_sha256', 'artifact')
    if at.closed(r['executor'], ('harness', 'model', 'effort'), 'executor'):
        at.expect(all(isinstance(v, str) for v in r['executor'].values()), 'executor values must be strings')
    if at.expect(isinstance(r['roles'], list), 'roles must be a list'):
        for role in r['roles']:
            if at.closed(role, ROLE_FIELDS, 'role'):
                at.expect(is_text(role['role']) and isinstance(role['model'], str) and role['tier'] in TIERS
                          and role['effort'] in EFFORTS and count_or_na(role['tokens_in']) and count_or_na(role['tokens_out']),
                          'invalid role entry')
    if at.closed(r['judge'], ('kind', 'model_family', 'blinded'), 'judge'):
        at.expect(r['judge']['kind'] in ('mechanical', 'semantic') and isinstance(r['judge']['model_family'], str)
                  and type(r['judge']['blinded']) is bool, 'invalid judge')
    at.expect(type(r['rule_exposure']) is bool, 'rule_exposure must be a boolean')
    at.expect(r['outcome'] in OUTCOMES, 'invalid outcome')
    at.expect(r['invalid_reason'] is None or isinstance(r['invalid_reason'], str), 'invalid_reason must be a string or null')
    if r['outcome'] == 'invalid':
        at.expect(is_text(r['invalid_reason']), 'an invalid outcome needs a non-empty invalid_reason', 'invalid-reason')
    if at.closed(r['scores'], SCORE_FIELDS, 'scores'):
        values = list(r['scores'].values())
        if at.expect(all(v is None or (type(v) is int and v in (0, 1, 2)) for v in values), 'scores must be 0, 1, 2 or null'):
            if r['outcome'] == 'unobserved':
                at.expect(all(v is None for v in values), 'an unobserved episode carries numeric scores', 'placeholder')
    if at.closed(r['cost'], COST_FIELDS, 'cost'):
        at.expect(all(count_or_na(v) for v in r['cost'].values()), 'cost values must be non-negative integers or n/a')
    if at.expect(r['transcript_sha256'] is None or is_hex(r['transcript_sha256']), 'transcript_sha256 must be sha256 hex or null'):
        at.expect(r['transcript_sha256'] is not None or r['outcome'] == 'unobserved', 'transcript_sha256 is null only for unobserved')
    for key in ('started_at', 'finished_at'):
        at.expect(r[key] == 'n/a' or is_time(r[key]), key + ' must be ISO-8601 UTC or n/a')
    if any(pattern.search(text) for text in strings(r) for pattern in LEAKS):
        at.add('leak', 'a field carries a path, key or address')


def check_against_manifest(r, context, order, at):
    if not (all(isinstance(r[k], str) for k in ('episode_id', 'scenario_id', 'variant_id', 'arm')) and type(r['seed']) is int):
        return
    at.expect(r['cohort_id'] == context['cohort_id'], 'cohort_id differs from the manifest', 'mismatch')
    variant = context['variants'].get((r['scenario_id'], r['variant_id']))
    if at.expect(variant is not None, 'variant %s/%s is not in the manifest' % (r['scenario_id'], r['variant_id']), 'unlisted'):
        at.expect(r['split'] == variant['split'], 'split differs from the manifest variant', 'mismatch')
    at.expect(r['arm'] in context['arms'], 'arm is not declared in the manifest', 'mismatch')
    at.expect(r['seed'] in context['seeds'], 'seed is not declared in the manifest', 'mismatch')
    if r['episode_id'] not in order:
        at.add('extra', 'episode %s is not in the manifest order' % r['episode_id'])
        return
    index, entry = order[r['episode_id']]
    for key in ('scenario_id', 'variant_id', 'arm', 'seed'):
        at.expect(r[key] == entry[key], '%s differs from the order entry' % key, 'mismatch')
    at.expect(r['order_index'] == index, 'order_index differs from the order position', 'mismatch')


def read_manifest(directory, report):
    try:
        manifest = json.loads((directory / MANIFEST).read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as problem:
        report.at(MANIFEST, 0).add('schema', 'unreadable manifest: %s' % problem)
        return None
    return check_manifest(manifest, report)


def read_episodes(directory, context, report):
    try:
        lines = (directory / EPISODES).read_bytes().split(b'\n')
    except OSError as problem:
        report.at(EPISODES, 0).add('schema', 'unreadable episodes: %s' % problem)
        return []
    if lines and lines[-1] == b'':
        lines.pop()
    order = {e['episode_id']: (i, e) for i, e in enumerate(context['order'])} if context else {}
    records, previous, seen = [], ZERO, {}
    for number, line in enumerate(lines, 1):
        at = report.at(EPISODES, number)
        try:
            record = json.loads(line.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            record = None
        if at.closed(record, EPISODE_FIELDS, 'record'):
            check_fields(record, at)
            at.expect(record['prev_sha256'] == previous, 'prev_sha256 does not match the previous line', 'chain')
            identity = record['episode_id'] if isinstance(record['episode_id'], str) else None
            if identity is None:
                pass
            elif identity in seen:
                at.add('duplicate', 'episode_id %s repeats line %d' % (identity, seen[identity]))
            else:
                seen[identity] = number
                if context is not None:
                    check_against_manifest(record, context, order, at)
            records.append(record)
        previous = hashlib.sha256(line).hexdigest()
    if context is not None:
        for entry in context['order']:
            if entry['episode_id'] not in seen:
                report.at(EPISODES, 0).add('missing', 'missing episode %s' % entry['episode_id'])
    return records


def arm_stats(records, key, arm):
    valid = [r for r in records if (r['scenario_id'], r['variant_id']) == key and r['arm'] == arm and r['outcome'] in ('fell', 'avoided')]
    return sum(r['outcome'] == 'fell' for r in valid), len(valid)


def compare(context, records, comparison):
    rows = []
    for key in sorted(context['variants']):
        baseline = arm_stats(records, key, comparison['baseline_arm'])
        candidate = arm_stats(records, key, comparison['candidate_arm'])
        contaminated = any(r['rule_exposure'] for r in records
                           if (r['scenario_id'], r['variant_id']) == key and r['arm'] == comparison['baseline_arm'])
        observed = baseline[1] > 0 and candidate[1] > 0
        rows.append(dict(key=key, label=verdict.label(baseline, candidate, context['n_min'], contaminated),
                         baseline=baseline, candidate=candidate, cls=context['variants'][key]['class'],
                         p_better=verdict.upper_tail(*baseline, *candidate) if observed else None,
                         p_worse=verdict.upper_tail(*candidate, *baseline) if observed else None))
    qualifying = [row for row in rows if row['cls'] == 'outcome-trap' and row['label'] not in ('contaminated', 'unobserved')]
    if len(qualifying) < 2:
        return rows, None
    differences = [row['baseline'][0] / row['baseline'][1] - row['candidate'][0] / row['candidate'][1] for row in qualifying]
    d, lo, hi = verdict.pooled(differences)
    return rows, dict(d=d, lo=lo, hi=hi, seed=verdict.SEED, B=verdict.B, variants=['/'.join(row['key']) for row in qualifying])


def ablations(context, records):
    rows = []
    for arm in (a for a in context['arms'] if a.startswith('ablation:')):
        for key in sorted(context['variants']):
            k, n = arm_stats(records, key, arm)
            rows.append(dict(rule_id=arm.split(':', 1)[1], scenario_id=key[0], variant_id=key[1], k=k if n else None, n=n))
    return sorted(rows, key=lambda a: (a['rule_id'], a['scenario_id'], a['variant_id']))


def text_arm(name, stats):
    k, n = stats
    if n == 0:
        return '%s -/0 [n/a]' % name
    lo, hi = verdict.wilson(k, n)
    return '%s %d/%d [%s,%s]' % (name, k, n, verdict.fmt(lo), verdict.fmt(hi))


def text_line(prefix, row, comparison):
    p = lambda value: 'n/a' if value is None else verdict.fmt(value)
    return '%s %s %s %s %s p_better=%s p_worse=%s' % (prefix, '/'.join(row['key']), row['label'],
                                                      text_arm(comparison['baseline_arm'], row['baseline']),
                                                      text_arm(comparison['candidate_arm'], row['candidate']),
                                                      p(row['p_better']), p(row['p_worse']))


def text_pool(prefix, pool):
    return '%s %s [%s,%s] seed=%d B=%d' % (prefix, verdict.fmt(pool['d']), verdict.fmt(pool['lo']), verdict.fmt(pool['hi']),
                                           pool['seed'], pool['B'])


def rounded(value):
    return None if value is None else round(value, 4) + 0.0


def json_arm(stats):
    k, n = stats
    if n == 0:
        return dict(k=None, n=0, lo=None, hi=None)
    lo, hi = verdict.wilson(k, n)
    return dict(k=k, n=n, lo=rounded(lo), hi=rounded(hi))


def json_row(row, comparison, primary):
    base = dict(scenario_id=row['key'][0], variant_id=row['key'][1], label=row['label'],
                p_better=rounded(row['p_better']), p_worse=rounded(row['p_worse']))
    if primary:
        base.update(control=json_arm(row['baseline']), method=json_arm(row['candidate']))
    else:
        base.update(baseline=json_arm(row['baseline']), candidate=json_arm(row['candidate']),
                    baseline_arm=comparison['baseline_arm'], candidate_arm=comparison['candidate_arm'])
    return base


def json_pool(pool):
    return None if pool is None else dict(pool, d=rounded(pool['d']), lo=rounded(pool['lo']), hi=rounded(pool['hi']))


def render(context, records, as_json):
    comparisons = context['comparisons']
    primary = comparisons.get('primary')
    primary_rows, primary_pool = compare(context, records, primary) if primary else ([], None)
    secondary = {cid: compare(context, records, comparisons[cid]) for cid in sorted(comparisons) if cid != 'primary'}
    extra = ablations(context, records)
    if as_json:
        return json.dumps(dict(
            verdicts=[json_row(row, primary, True) for row in primary_rows],
            comparisons={cid: dict(verdicts=[json_row(row, comparisons[cid], False) for row in rows], pooled=json_pool(pool))
                         for cid, (rows, pool) in secondary.items()},
            ablations=extra, pooled=json_pool(primary_pool), errors=[]), ensure_ascii=False)
    out = [text_line('verdict', row, primary) for row in primary_rows]
    for cid, (rows, pool) in secondary.items():
        out += [text_line('verdict[%s]' % cid, row, comparisons[cid]) for row in rows]
        if pool:
            out.append(text_pool('pooled[%s]' % cid, pool))
    out += ['ablation %s %s/%s %s/%d' % (a['rule_id'], a['scenario_id'], a['variant_id'], '-' if a['k'] is None else a['k'], a['n'])
            for a in extra]
    if primary_pool:
        out.append(text_pool('pooled', primary_pool))
    return '\n'.join(out)


def main(argv):
    options = [a for a in argv if a.startswith('-')]
    paths = [a for a in argv if not a.startswith('-')]
    if len(paths) != 1 or any(o != '--json' for o in options) or not Path(paths[0]).is_dir():
        print(USAGE, file=sys.stderr)
        return 2
    as_json = '--json' in options
    directory = Path(paths[0])
    report = Report()
    context = read_manifest(directory, report)
    records = read_episodes(directory, context, report)
    if report.errors or context is None:
        if as_json:
            print(json.dumps(dict(verdicts=[], comparisons={}, ablations=[], pooled=None, errors=report.errors), ensure_ascii=False))
        else:
            for e in report.errors:
                print('error: %s:%d: %s: %s' % (e['file'], e['line'], e['code'], e['text']))
        return 1
    output = render(context, records, as_json)
    if output:
        print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
