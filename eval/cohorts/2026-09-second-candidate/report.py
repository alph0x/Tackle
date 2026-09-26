"""Render this cohort's report from its records.

    python3 eval/cohorts/2026-09-second-candidate/report.py           # writes report.md beside this file
    python3 eval/cohorts/2026-09-second-candidate/report.py --check   # exit 0 only if report.md matches

It reads manifest.json, episodes.jsonl, judgments/ and audits/ of this cohort and of its sealed smoke
cohort(s) (any sibling directory named smoke*), and prints ids, labels, counts and costs only: never a
prompt, a fixture or a test (word for word the restriction the earlier cohorts' own report.py states for
itself). decision.py's own two lines (`candidate`, `split`) are reproduced here from the same tracked
records, never recomputed differently.
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
        'as a user who invokes it would; triggering is not measured. The method:split arm runs only '
        'in the smoke: its planner session is asked to write a paper plan instead of running the '
        'skill\'s own PLAN scaffolding, a disclosed fidelity simplification, and both of its sessions '
        'are pinned to the cheapest bindable tier. The pilot runs no split episodes, because planning '
        'on a more capable tier than execution is now a rule of the candidate. At three seeds per arm '
        'per variant, protocol v2\'s own native per-variant '
        'labels (`discriminates`, `method-worse`) are mathematically unreachable: the single most extreme '
        '3-vs-3 split lands exactly at the significance threshold, not below it, so those lines below can '
        'only ever read `unobserved`, `inert`, `inconclusive` or `contaminated` here. The `pooled[...]` '
        'lines below are protocol v2\'s own native pooling across all three outcome-trap variants; the '
        'Decision section\'s own pooled figure is a separate computation over only the two pre-registered '
        'primary variants, excluding the held-out tripwire variant, which is pooled only as a binary trap '
        'there instead — the real evidentiary lift comes from that pooled bound and tripwire, never from '
        'the native per-variant labels. The held-out third variant is a binary tripwire on the candidate '
        'comparison, never pooled into either arm\'s own primary figure. Two disclosed mechanism '
        'episodes carry pinned, coordinator-supplied sentences overriding their ordinary '
        'instructions, to prove the tool\'s own three-session merge and escalation mechanism live. '
        'The smoke cohort\'s first attempt is recorded invalid: its planner wrote the escalation '
        'line in its reply instead of in the brief, whose file the pinned sentence did not name. '
        'The smoke-2 cohort\'s retry, whose sentence names the brief file, completed all three '
        'sessions. Neither is pooled into, or read as, a behavioral measurement of planning '
        'quality. One pilot episode is recorded as an error: the coordinator read its transcript '
        'before the session had finished, and that episode\'s judged outcome is never used. The '
        'price table\'s '
        'fresh-input pricing of a blended tokens_in is a disclosed, conservative approximation, not a '
        'precise dollar figure.')


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
    empty), plus the per-episode dollar cost decision.py's own split line reports beside the raw figures."""
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


def escalation_model_check(rows):
    """The live escalation mechanism episode's own post-hoc model check: the only real proof that the
    model map's next bound tier actually differs from the tier before it is roles[2].model, read from
    that session's own transcript, never assumed from its --tier label alone. Finds the one record with
    three roles (an ordinary episode of either multi-session arm never has three); 'not observed' when
    none exists yet — never a pass by default."""
    for record, _, _ in rows:
        roles = record.get('roles') or []
        if len(roles) == 3:
            models = [decision.base_model_id(role['model']) for role in roles]
            ok = models[2] == 'claude-sonnet-5' and models[2] != models[1] and models[2] != models[0]
            return ('pass' if ok else 'fail'), models
    return 'not observed', None


def artifact_hashes(manifest, rows):
    """Both tested trees' hashes, named: the candidate (9.0.0, after the gap-closure tasks) tree from the
    manifest's own summary pair, and the 8.4.1 tree from any method-arm episode's own artifact_sha256 (the
    manifest's two-slot artifacts object cannot carry three trees, so the third rides on its own episodes)."""
    candidate_sha = manifest['artifacts']['candidate_sha256']
    method_841_sha = next((r['artifact_sha256'] for r, _, _ in rows if r['arm'] == 'method' and r['artifact_sha256']), NA)
    return candidate_sha, method_841_sha


def section(title, directory, prices, level='##'):
    manifest, context, records, rows = cohort(directory)
    verdicts = check.render(context, records, False)
    models = sorted({r['executor']['model'] for r, _, _ in rows})
    candidate_sha, method_841_sha = artifact_hashes(manifest, rows)
    out = ['%s %s' % (level, title), '',
           '- Cohort `%s`, seal `%s`, created %s.' % (manifest['cohort_id'], manifest['seal_sha256'], manifest['created_at']),
           '- Variants: %s.' % ', '.join('`%s/%s` (%s)' % (v['scenario_id'], v['variant_id'], v['split'])
                                         for v in manifest['variants']),
           '- Executor: %s, `%s`; as served: %s. Judge: mechanical hidden acceptance tests, blinded.' % (
               manifest['executor']['harness'], manifest['executor']['model'], ', '.join('`%s`' % m for m in models)),
           '- Artifacts: candidate `%s`; method (8.4.1) `%s`.' % (candidate_sha, method_841_sha),
           '', '```text', verdicts, '```', '']
    out += episode_table(rows) + [''] + arm_table(manifest, rows) + ['', 'Roles and per-episode dollar cost:', ''] \
        + role_table(rows, prices) + ['', 'Audit:', ''] + audit_lines(rows)
    outcome, models_seen = escalation_model_check(rows)
    if models_seen is not None or outcome == 'not observed':
        out += ['', 'Escalation mechanism episode, post-hoc model check: **%s** (roles\' models in order: %s).' % (
            outcome, ', '.join(models_seen) if models_seen else NA)]
    out += ['']
    return out, records


def render():
    pilot = load(HERE / 'manifest.json')
    prices = load(HERE / 'price-table.json')['prices']
    out = ['# Second candidate cohort: the 9.0.0 candidate against the 8.4.1 method', '',
          LIMIT, '',
           'Hypothesis: %s' % pilot['hypothesis'], '',
           'Arms: `method` receives the 8.4.1 install; `method:candidate` receives the 9.0.0 candidate as a '
           'fixed, single session at the cheapest tier. In the smoke only, `method:split` receives the 9.0.0 '
           'candidate as a planner session then an executor session, both pinned to the cheapest tier, to '
           'prove the multi-session mechanism; the pilot runs no split episodes, so the Decision section\'s '
           'split line has no split-arm figures; the routing default is settled by the candidate\'s own rule, '
           'not by that line.', '']
    pilot_lines, pilot_records = section('Pilot: held-out variants', HERE, prices)
    out += pilot_lines
    for smoke_dir in sorted(HERE.glob('smoke*')):
        if smoke_dir.is_dir() and (smoke_dir / 'manifest.json').is_file():
            smoke_lines, _ = section('Smoke: %s' % smoke_dir.name, smoke_dir, prices)
            out += smoke_lines
    candidate, candidate_reason = decision.candidate_verdict(pilot_records)
    split_line = decision.split_summary(pilot_records, prices)
    out += ['## Decision', '',
           '- `candidate`: **%s**%s' % (candidate, '' if candidate_reason is None else ' (%s)' % candidate_reason),
           '- `split`: %s' % split_line, '']
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
