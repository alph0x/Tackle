"""Render this cohort's report from its records.

    python3 report.py           # writes report.md beside this file
    python3 report.py --check   # exit 0 only if report.md matches, byte for byte

It reads only this cohort's own tracked records, under its own directory: manifest.json,
episodes.jsonl, judgments/ and smoke/ -- never audits/, and never a scratchpad or an episode path.
decision.py's own report-only line is reproduced here from the same records, never recomputed
differently. Prints ids, labels, counts and costs only: never a prompt, a fixture or a test.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'protocol-v2'))
import check  # noqa: E402

sys.path.insert(0, str(HERE))
import decision  # noqa: E402

NA = 'n/a'
ORDER_WORDS = ('ordered', 'unordered', 'n/a no-marker', 'not run')

LIMIT = ('Development-grade evidence. Each episode ran as a single Claude Code subagent session, at the '
        'fast tier only, on the operator\'s machine and login, not in an isolated install: it started in '
        'the host repository, and both arms could reach the installed skill and that repository. The '
        'ordering check matches literal substrings against one recorded field per tool call, never a '
        'resolved path: a wildcard read such as `cat dir/*.md` names neither tracked file literally and '
        'registers no touch at all, a symmetric bias toward the unordered reading for both required '
        'files equally. This figure is report-only and gates nothing.')


class Failure(Exception):
    pass


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_optional(path):
    return load(path) if path.is_file() else {}


def judgment_for(directory, episode_id):
    return load_optional(directory / 'judgments' / ('%s.json' % episode_id))


def read_cohort(directory):
    """(manifest, records); raises Failure when the directory's records fail the protocol checker."""
    report = check.Report()
    context = check.read_manifest(directory, report)
    records = check.read_episodes(directory, context, report) if context is not None else []
    if report.errors or context is None:
        raise Failure('%s fails the protocol checker (%d error(s))' % (directory.name, len(report.errors)))
    manifest = load(directory / 'manifest.json')
    return manifest, records


def variant_arm_table(manifest, records):
    out = ['| Variant | Arm | Episodes | Valid | Avoided | Fell | Invalid |',
          '|---|---|---|---|---|---|---|']
    for variant in manifest['variants']:
        key = (variant['scenario_id'], variant['variant_id'])
        for arm in manifest['arms']:
            mine = [r for r in records if (r['scenario_id'], r['variant_id']) == key and r['arm'] == arm]
            valid = [r for r in mine if r['outcome'] in ('fell', 'avoided')]
            out.append('| %s/%s | %s | %d | %d | %d | %d | %d |' % (
                key[0], key[1], arm, len(mine), len(valid),
                sum(r['outcome'] == 'avoided' for r in valid),
                sum(r['outcome'] == 'fell' for r in valid),
                sum(r['outcome'] == 'invalid' for r in mine)))
    return out


def ordering_section(directory, manifest, records):
    """Each judgments/<episode id>.json may carry order: {result, folded}. result is one of the four
    canonical words below; anything else (including an entirely missing order key, or an unrecognized
    word) counts as missing and is printed, never hidden. folded is true when the ordering check turned
    an avoided into a fell."""
    out = ['Ordering check:', '']
    for arm in manifest['arms']:
        mine = [r for r in records if r['arm'] == arm]
        counts = {word: 0 for word in ORDER_WORDS}
        counts['missing'] = 0
        folded = []
        for record in mine:
            judgment = judgment_for(directory, record['episode_id'])
            order = judgment.get('order') if isinstance(judgment, dict) else None
            result = order.get('result') if isinstance(order, dict) else None
            if result in counts:
                counts[result] += 1
            else:
                counts['missing'] += 1
            if isinstance(order, dict) and order.get('folded'):
                folded.append(record['episode_id'])
        out.append('- %s: %s.' % (arm, ', '.join(
            '%s=%d' % (word, counts[word]) for word in ORDER_WORDS + ('missing',))))
        out.append('  Folded: %s.' % (', '.join(sorted(folded)) if folded else 'none'))
    out.append('')
    return out


def invalid_section(records):
    out = ['Invalid episodes:', '']
    invalid = [(r['episode_id'], r.get('invalid_reason')) for r in records if r['outcome'] == 'invalid']
    if not invalid:
        out.append('- none.')
    else:
        for episode_id, reason in sorted(invalid):
            out.append('- %s: %s.' % (episode_id, reason))
    out.append('')
    return out


def dollar_cost_section(manifest, records, prices):
    out = ['Median per-episode dollar cost:', '']
    for arm in manifest['arms']:
        value = decision.dollar_median(records, arm, prices)
        out.append('- %s: %s.' % (arm, 'n/a' if value == NA else '$%.4f' % value))
    out.append('')
    return out


def artifact_section(manifest):
    match = decision.SEAL_CLAUSE.search(manifest.get('decision_rule') or '')
    decision_sha = match.group(1) if match else NA
    price_sha = match.group(2) if match else NA
    artifacts = manifest.get('artifacts') or {}
    return ['Artifact hashes:', '',
           '- decision.py (sealed): `%s`.' % decision_sha,
           '- price-table.json (sealed): `%s`.' % price_sha,
           '- manifest artifacts.baseline_sha256: `%s`.' % artifacts.get('baseline_sha256', NA),
           '- manifest artifacts.candidate_sha256: `%s`.' % artifacts.get('candidate_sha256', NA),
           '- manifest oracle_sha256: `%s`.' % manifest.get('oracle_sha256', NA), '']


def smoke_section(directory):
    """The two smoke episodes and whether the protocol checker accepts the smoke directory as a whole --
    never a Failure, since the smoke result is itself what this section reports, not a precondition for
    rendering the rest of the report."""
    out = ['Smoke:', '']
    smoke_dir = directory / 'smoke'
    if not smoke_dir.is_dir() or not (smoke_dir / 'manifest.json').is_file():
        out += ['- no smoke directory found.', '']
        return out
    report = check.Report()
    context = check.read_manifest(smoke_dir, report)
    records = check.read_episodes(smoke_dir, context, report) if context is not None else []
    accepts = not report.errors and context is not None
    out.append('- checker accepts: %s (%d error(s)).' % ('yes' if accepts else 'no', len(report.errors)))
    valid_records = [r for r in records if isinstance(r, dict)]
    for record in sorted(valid_records, key=lambda r: r.get('order_index') or 0):
        out.append('- %s: %s/%s %s -> %s.' % (
            record.get('episode_id', NA), record.get('scenario_id', NA), record.get('variant_id', NA),
            record.get('arm', NA), record.get('outcome', NA)))
    out.append('')
    return out


def render():
    manifest, records = read_cohort(HERE)
    prices = load(HERE / 'price-table.json')['prices']
    summary = decision.resume_summary(records, prices)
    out = ['# Resume cohort: the 9.0.0 candidate against the 8.4.1 method on a staged mid-task workspace',
          '', '- Cohort `%s`, seal `%s`, created %s.' % (
              manifest['cohort_id'], manifest['seal_sha256'], manifest['created_at']),
           '', 'Hypothesis: %s' % manifest['hypothesis'], '',
           'Decision: resume: report-only: %s' % summary, '']
    out += variant_arm_table(manifest, records) + ['']
    out += ordering_section(HERE, manifest, records)
    out += invalid_section(records)
    out += dollar_cost_section(manifest, records, prices)
    out += artifact_section(manifest)
    out += smoke_section(HERE)
    out += [LIMIT, '']
    return '\n'.join(out).rstrip('\n') + '\n'


def main(argv):
    try:
        text = render()
    except (Failure, decision.Refusal, OSError, ValueError, KeyError) as problem:
        print('report: %s' % problem, file=sys.stderr)
        return 1
    target = HERE / 'report.md'
    data = text.encode('utf-8')
    if argv == ['--check']:
        if not target.exists() or target.read_bytes() != data:
            print('report: report.md differs from the records', file=sys.stderr)
            return 1
        return 0
    if argv:
        print(__doc__, file=sys.stderr)
        return 2
    target.write_bytes(data)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
