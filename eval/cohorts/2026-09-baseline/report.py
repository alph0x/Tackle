"""Render the 2026-09 baseline cohort's report from its records (T-08).

    python3 eval/cohorts/2026-09-baseline/report.py           # writes report.md beside this file
    python3 eval/cohorts/2026-09-baseline/report.py --check   # exit 0 only if report.md matches

It reads manifest.json, episodes.jsonl, judgments/ and audits/ of this cohort and of its two smoke
cohorts (smoke/, smoke-2/), and prints ids, labels, counts and costs only: never a prompt, a fixture or a
test.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'protocol-v2'))
import check  # noqa: E402

NA = 'n/a'
COSTS = ('tokens_in', 'tokens_out', 'wall_seconds', 'tool_calls', 'files_written')

LIMIT = ('Development-grade evidence (D-87). Each episode ran as a Claude Code subagent of the '
         'coordinating session, on the operator\'s machine and login, not in an isolated install: it started '
         'in the host repository (D-95), and every arm could reach the installed skill and that repository. '
         'The contamination audit (D-91, D-94, D-96, D-98) sees only what the transcript\'s tool calls name; '
         'an episode it flags is invalid and leaves the counts. The method arm is asked to read and follow '
         'the staged 8.4.1 skill (D-98), as a user who invokes it would; triggering is not measured. One seed '
         'per arm and variant (n_min 1) can reach only inert or inconclusive for a variant that is observed, '
         'so this report reads the pooled difference and the costs, not a per-variant claim.')


class Failure(Exception):
    pass


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def cohort(directory):
    report = check.Report()
    context = check.read_manifest(directory, report)
    records = check.read_episodes(directory, context, report)
    if report.errors or context is None:
        raise Failure('%s fails the protocol checker (%d errors)' % (directory.name, len(report.errors)))
    manifest = load(directory / 'manifest.json')
    rows = []
    for record in sorted(records, key=lambda r: r['order_index']):
        judgment = load(directory / 'judgments' / ('%s.json' % record['episode_id']))
        audit = load(directory / 'audits' / ('%s.json' % record['episode_id']))
        rows.append((record, judgment, audit))
    return manifest, context, records, rows


def total(values):
    return NA if any(v == NA for v in values) else sum(values)


def cell(value):
    return str(value)


def episode_table(rows):
    out = ['| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | '
           'Files written | Check runs | Correction cycles |',
           '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for record, judgment, audit in rows:
        details = judgment.get('details') or {}
        out.append('| %s | %s/%s | %s | %s | %s | %s | %s | %s |' % (
            record['episode_id'], record['scenario_id'], record['variant_id'], record['arm'], record['outcome'],
            audit['verdict'], ' | '.join(cell(record['cost'][key]) for key in COSTS),
            cell(details.get('check_runs', NA)), cell(details.get('correction_cycles', NA))))
    return out


def arm_table(manifest, rows):
    out = ['| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |',
           '|---|---|---|---|---|---|---|---|---|']
    for arm in manifest['arms']:
        mine = [(r, j) for r, j, _ in rows if r['arm'] == arm]
        valid = [r for r, _ in mine if r['outcome'] in ('fell', 'avoided')]
        cycles = total([(j.get('details') or {}).get('correction_cycles', NA) for _, j in mine])
        out.append('| %s | %d | %d | %d | %s | %s | %s | %s | %s |' % (
            arm, len(mine), len(valid), sum(r['outcome'] == 'fell' for r in valid),
            cell(total([r['cost']['tokens_in'] for r, _ in mine])), cell(total([r['cost']['tokens_out'] for r, _ in mine])),
            cell(total([r['cost']['wall_seconds'] for r, _ in mine])), cell(total([r['cost']['tool_calls'] for r, _ in mine])),
            cell(cycles)))
    return out


def audit_lines(rows):
    clean = [r['episode_id'] for r, _, a in rows if a['verdict'] == 'clean']
    flagged = [(r['episode_id'], a) for r, _, a in rows if a['verdict'] != 'clean']
    out = ['- Clean: %d of %d.' % (len(clean), len(rows))]
    for episode_id, audit in flagged:
        out.append('- %s: %s (%d outside path(s), skill used: %s).' % (
            episode_id, audit['reason'], len(audit['outside_paths']), audit['skill_used']))
    used = [r['episode_id'] for r, _, a in rows if a['skill_used'] and r['arm'] != 'control']
    if used:
        out.append('- Method episodes that reached the skill through the Skill tool or another copy: %s.' % ', '.join(used))
    return out


def section(title, directory, level='##'):
    manifest, context, records, rows = cohort(directory)
    verdicts = check.render(context, records, False)
    models = sorted({r['executor']['model'] for r, _, _ in rows})
    out = ['%s %s' % (level, title), '',
           '- Cohort `%s`, seal `%s`, created %s.' % (manifest['cohort_id'], manifest['seal_sha256'], manifest['created_at']),
           '- Variants: %s.' % ', '.join('`%s/%s` (%s)' % (v['scenario_id'], v['variant_id'], v['split'])
                                         for v in manifest['variants']),
           '- Executor: %s, `%s`; as served: %s. Judge: mechanical hidden acceptance tests, blinded.' % (
               manifest['executor']['harness'], manifest['executor']['model'], ', '.join('`%s`' % m for m in models)),
           '', '```text', verdicts, '```', '']
    out += episode_table(rows) + [''] + arm_table(manifest, rows) + ['', 'Audit:', ''] + audit_lines(rows) + ['']
    return out


def render():
    pilot = load(HERE / 'manifest.json')
    out = ['# Baseline cohort 2026-09: Tackle 8.4.1 against no skill', '', LIMIT, '',
           'Hypothesis: %s' % pilot['hypothesis'], '',
           'Arms: `control` receives the task alone; `method` receives the task and the instruction to read '
           'and follow a staged copy of the 8.4.1 install (artifact `%s`).' % pilot['artifacts']['candidate_sha256'],
           '']
    out += section('Pilot: held-out variants', HERE)
    out += section('Smoke: the procedure check on a development variant', HERE / 'smoke')
    out += section('Re-smoke: the corrected procedure (D-98)', HERE / 'smoke-2')
    return '\n'.join(out).rstrip('\n') + '\n'


def main(argv):
    try:
        text = render()
    except (Failure, OSError, ValueError, KeyError) as problem:
        print('report: %s' % problem, file=sys.stderr)
        return 1
    target = HERE / 'report.md'
    if argv == ['--check']:
        if not target.exists() or target.read_text(encoding='utf-8') != text:
            print('report: report.md differs from the records', file=sys.stderr)
            return 1
        return 0
    if argv:
        print(__doc__, file=sys.stderr)
        return 2
    target.write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
