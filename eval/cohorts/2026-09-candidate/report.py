"""Render the 2026-09 candidate cohort's report from its records.

    python3 eval/cohorts/2026-09-candidate/report.py           # writes report.md beside this file
    python3 eval/cohorts/2026-09-candidate/report.py --check   # exit 0 only if report.md matches

It reads manifest.json, episodes.jsonl, judgments/ and audits/ of this cohort and of its sealed smoke
cohort(s) (any sibling directory named smoke*), and prints ids, labels, counts and costs only: never a
prompt, a fixture or a test (word for word the restriction the 2026-09 baseline cohort's own report.py
states for itself). decision.py's own two verdicts (candidate, routing) are reproduced here from the
same tracked records, never recomputed differently.
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
COSTS = ('tokens_in', 'tokens_out', 'wall_seconds', 'tool_calls', 'files_written')
ROLE_FIELDS = ('role', 'tier', 'model', 'tokens_in', 'tokens_out')

LIMIT = ('Development-grade evidence. Each episode ran as a Claude Code subagent of the coordinating '
        'session, on the operator\'s machine and login, not in an isolated install: it started in the host '
        'repository, and every arm could reach the installed skill and that repository. The contamination '
        'audit sees only what the transcript\'s tool calls name; an episode it flags is invalid and leaves '
        'the counts. The method and method:candidate arms are asked to read and follow their staged skill, '
        'as a user who invokes it would; triggering is not measured. The method:routed arm\'s planner '
        'session is asked to write a paper plan instead of running the skill\'s own PLAN scaffolding, a '
        'disclosed fidelity simplification. One seed per arm and variant (n_min 1) can reach only inert or '
        'inconclusive for a variant that is observed alone, so this report reads the pooled difference '
        '(over the two pre-registered primary variants only) and the costs, not a per-variant claim. The '
        'held-out third variant is a binary tripwire on every comparison, never pooled. For 9.0.0 there is '
        'no live third (escalated) session in any episode; that path is proven only by the tool\'s own unit '
        'tests, a disclosed gap. The routing comparison changes both the session split and the tier '
        'selected at once, so it cannot isolate which one helps; a fifth arm that would is a named, '
        'un-built future refinement. The price table\'s fresh-input pricing of a blended tokens_in is a '
        'disclosed, conservative approximation, not a precise dollar figure.')


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
        judgment_path = directory / 'judgments' / ('%s.json' % record['episode_id'])
        audit_path = directory / 'audits' / ('%s.json' % record['episode_id'])
        judgment = load(judgment_path) if judgment_path.is_file() else {}
        audit = load(audit_path) if audit_path.is_file() else {'verdict': NA, 'reason': None, 'outside_paths': [],
                                                                'skill_used': NA}
        rows.append((record, judgment, audit))
    return manifest, context, records, rows


def total(values):
    values = list(values)
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
            audit.get('verdict', NA), ' | '.join(cell(record['cost'][key]) for key in COSTS),
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


def role_table(rows, prices):
    """One line per role entry across every episode (blank for a single-session arm, whose roles[] is
    empty), plus the per-episode dollar cost decision.py's routing verdict actually gates on."""
    out = ['| Episode | Arm | Role | Tier | Model | Tokens in | Tokens out | Episode $ |',
           '|---|---|---|---|---|---|---|---|']
    for record, _, _ in rows:
        dollars = decision.episode_dollars(record, prices)
        dollars_text = 'n/a' if dollars is None else '%.4f' % dollars
        roles = record['roles'] or [{'role': NA, 'tier': NA, 'model': record['executor']['model'],
                                     'tokens_in': record['cost']['tokens_in'], 'tokens_out': record['cost']['tokens_out']}]
        for role in roles:
            out.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (
                record['episode_id'], record['arm'], role.get('role', NA), role.get('tier', NA), role['model'],
                cell(role['tokens_in']), cell(role['tokens_out']), dollars_text))
    return out


def audit_lines(rows):
    clean = [r['episode_id'] for r, _, a in rows if a.get('verdict') == 'clean']
    flagged = [(r['episode_id'], a) for r, _, a in rows if a.get('verdict') not in ('clean', NA)]
    out = ['- Clean: %d of %d.' % (len(clean), len(rows))]
    for episode_id, audit in flagged:
        out.append('- %s: %s (%d outside path(s), skill used: %s).' % (
            episode_id, audit.get('reason'), len(audit.get('outside_paths') or []), audit.get('skill_used')))
    used = [r['episode_id'] for r, _, a in rows if a.get('skill_used') is True and r['arm'] != 'control']
    if used:
        out.append('- Method episodes that reached the skill through the Skill tool or another copy: %s.' % ', '.join(used))
    return out


def artifact_hashes(manifest, rows):
    """Both tested trees' hashes, named: the candidate (9.0.0) tree from the manifest's own summary
    pair, and the 8.4.1 tree from any method-arm episode's own artifact_sha256 (Finding 4: the manifest's
    two-slot artifacts object cannot carry three trees, so the third rides on its own episodes)."""
    candidate_sha = manifest['artifacts']['candidate_sha256']
    method_84 = next((r['artifact_sha256'] for r, _, _ in rows if r['arm'] == 'method' and r['artifact_sha256']), NA)
    return candidate_sha, method_84


def section(title, directory, prices, level='##'):
    manifest, context, records, rows = cohort(directory)
    verdicts = check.render(context, records, False)
    models = sorted({r['executor']['model'] for r, _, _ in rows})
    candidate_sha, method_84_sha = artifact_hashes(manifest, rows)
    out = ['%s %s' % (level, title), '',
           '- Cohort `%s`, seal `%s`, created %s.' % (manifest['cohort_id'], manifest['seal_sha256'], manifest['created_at']),
           '- Variants: %s.' % ', '.join('`%s/%s` (%s)' % (v['scenario_id'], v['variant_id'], v['split'])
                                         for v in manifest['variants']),
           '- Executor: %s, `%s`; as served: %s. Judge: mechanical hidden acceptance tests, blinded.' % (
               manifest['executor']['harness'], manifest['executor']['model'], ', '.join('`%s`' % m for m in models)),
           '- Artifacts: candidate (9.0.0) `%s`; method (8.4.1) `%s`.' % (candidate_sha, method_84_sha),
           '', '```text', verdicts, '```', '']
    out += episode_table(rows) + [''] + arm_table(manifest, rows) + ['', 'Roles and per-episode dollar cost:', ''] \
        + role_table(rows, prices) + ['', 'Audit:', ''] + audit_lines(rows) + ['']
    return out, records


def render():
    pilot = load(HERE / 'manifest.json')
    prices = load(HERE / 'price-table.json')['prices']
    out = ['# Candidate cohort 2026-09: the 9.0.0 candidate against the 8.4.1 method and no skill', '', LIMIT, '',
           'Hypothesis: %s' % pilot['hypothesis'], '',
           'Arms: `control` receives the task alone; `method` receives the 8.4.1 install; `method:candidate` '
           'receives the 9.0.0 candidate at fixed tiers; `method:routed` receives the 9.0.0 candidate with '
           'per-task routing engaged (a frontier-tier planner, then an executor at the tier its brief compiles).',
           '']
    pilot_lines, pilot_records = section('Pilot: held-out variants', HERE, prices)
    out += pilot_lines
    for smoke_dir in sorted(HERE.glob('smoke*')):
        if smoke_dir.is_dir() and (smoke_dir / 'manifest.json').is_file():
            smoke_lines, _ = section('Smoke: %s' % smoke_dir.name, smoke_dir, prices)
            out += smoke_lines
    candidate, candidate_reason = decision.candidate_verdict(pilot_records)
    routing, routing_reason = decision.routing_verdict(pilot_records, prices)
    out += ['## Decision', '',
           '- `candidate`: **%s**%s' % (candidate, '' if candidate_reason is None else ' (%s)' % candidate_reason),
           '- `routing`: **%s**%s' % (routing, '' if routing_reason is None else ' (%s)' % routing_reason), '']
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
