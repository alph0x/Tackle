"""Render this cohort's report from its records.

    python3 eval/cohorts/2026-09-third-candidate/report.py           # writes report.md beside this file
    python3 eval/cohorts/2026-09-third-candidate/report.py --check   # exit 0 only if report.md matches

It reads manifest.json, episodes.jsonl, judgments/ and audits/ of this cohort and of its sealed smoke
cohort (any sibling directory named smoke*), and prints ids, labels, counts and costs only: never a
prompt, a fixture or a test (word for word the restriction the earlier cohorts' own report.py states for
itself). decision.py's own two lines (`candidate`, `no-regression`) are reproduced here from the same
tracked records, never recomputed differently; the `no-regression` line is printed verbatim from
decision.py's own formatter, so the two can never drift from each other.
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

LIMIT = ('Development-grade evidence. Each episode ran as a Claude Code subagent of the coordinating '
        'session, on the operator\'s machine and login, not in an isolated install: it started in the host '
        'repository, and every arm could reach the installed skill and that repository. The contamination '
        'audit sees only what the transcript\'s tool calls name; an episode it flags is invalid and leaves '
        'the counts. The method and method:candidate arms are asked to read and follow their staged skill, '
        'as a user who invokes it would; triggering is not measured. Every episode, smoke and pilot, is '
        'one session at the cheapest tier. At three seeds per arm per variant, protocol v2\'s own native '
        'per-variant labels (`discriminates`, `method-worse`) are mathematically unreachable: the single '
        'most extreme 3-vs-3 split lands exactly at the significance threshold, not below it, so those '
        'lines below can only ever read `unobserved`, `inert`, `inconclusive` or `contaminated` here. The '
        '`pooled[candidate]` line pools the outcome-trap variants that are neither contaminated nor '
        'unobserved. It bootstraps variant-level differences, so with three variants its interval runs '
        'from the smallest to the largest difference, and all-zero differences print [0.0000,0.0000], a '
        'degenerate interval, not a tight estimate. The Decision section pools only the two primary '
        'variants; with two, its lower bound is the smaller difference, a screen for an observed '
        'regression, not a significance test. The held-out third variant is a binary tripwire on both '
        'decision lines, never pooled into either arm\'s own primary figure. The smoke\'s two episodes run '
        'on a development variant to check staging and the close chain; they are pooled into nothing and '
        'read as no measurement. The fresh-input column prices every input token at the fresh rate, '
        'though most input is cache reads, and overstates spend; it is disclosure only. The cache-aware '
        'column prices each episode\'s own transcript usage, cache writes and reads included, at '
        'published rates, and is the spend. These traps start in a fresh fixture repository with no '
        'workspace, so neither line measures how the candidate treats an older workspace.')

# The same sentence LIMIT states once, up top; section() repeats it immediately after any verdict block
# whose rendered text holds a native `pooled[...]` line, so the caveat sits beside the actual figure
# wherever that line prints, not only once in the document's own preamble.
POOLED_SENTENCE = ('The `pooled[candidate]` line pools the outcome-trap variants that are neither '
                  'contaminated nor unobserved. It bootstraps variant-level differences, so with three '
                  'variants its interval runs from the smallest to the largest difference, and all-zero '
                  'differences print [0.0000,0.0000], a degenerate interval, not a tight estimate. The '
                  'Decision section pools only the two primary variants; with two, its lower bound is the '
                  'smaller difference, a screen for an observed regression, not a significance test.')
assert POOLED_SENTENCE in LIMIT, 'POOLED_SENTENCE must stay word for word what LIMIT already states'


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


def dollars_table(rows, prices):
    """One line per episode (every arm here is single-session, so there is no roles table): the executor's
    own model and token counts, the disclosure-only fresh-input price (decision.episode_dollars, the same
    price table and arithmetic every earlier cohort's report used) and the real cache-aware spend from the
    episode's own judgment (`spend`, from the copied cost_usd.py), plus a total line for each column."""
    out = ['| Episode | Arm | Model | Tokens in | Tokens out | Fresh-input $ | Cache-aware $ |',
           '|---|---|---|---|---|---|---|']
    fresh_values, cache_values = [], []
    for record, judgment, _ in rows:
        fresh = decision.episode_dollars(record, prices)
        spend = judgment.get('spend') or {}
        cache = spend.get('usd')
        fresh_values.append(NA if fresh is None else fresh)
        cache_values.append(NA if cache is None else cache)
        out.append('| %s | %s | %s | %s | %s | %s | %s |' % (
            record['episode_id'], record['arm'], record['executor']['model'], cell(record['cost']['tokens_in']),
            cell(record['cost']['tokens_out']), NA if fresh is None else '%.4f' % fresh,
            NA if cache is None else '%.4f' % cache))
    fresh_total, cache_total = total(fresh_values), total(cache_values)
    out.append('| Total | | | | | %s | %s |' % (
        NA if fresh_total == NA else '%.4f' % fresh_total, NA if cache_total == NA else '%.4f' % cache_total))
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


def not_counted_line(rows):
    """A data-driven replacement for cohort 2's fixed one-episode-error sentence: every record whose
    outcome does not count toward a verdict (only `fell`/`avoided` do), named with its outcome and reason
    (n/a when the outcome carries none, as for `error` or `timeout`)."""
    excluded = [(r['episode_id'], r['outcome'], r.get('invalid_reason') or NA)
               for r, _, _ in rows if r['outcome'] not in ('fell', 'avoided')]
    if not excluded:
        return 'Not counted: none.'
    return 'Not counted: ' + ', '.join('%s (%s: %s)' % item for item in excluded) + '.'


def artifact_check(manifest, rows):
    """Both tested trees' hashes, named, now both from the manifest's own two-slot artifacts object (no
    longer read from an episode's own artifact_sha256, since the manifest carries both here), plus the
    close chain's own tie: every record's artifact_sha256 must equal its arm's expected hash. Returns the
    two hashes and the (possibly empty) list of episode ids where the tie does not hold."""
    baseline_sha = manifest['artifacts']['baseline_sha256']
    candidate_sha = manifest['artifacts']['candidate_sha256']
    expected = {'method': baseline_sha, 'method:candidate': candidate_sha}
    mismatches = [r['episode_id'] for r, _, _ in rows
                 if r['arm'] in expected and r['artifact_sha256'] != expected[r['arm']]]
    return baseline_sha, candidate_sha, mismatches


def section(title, directory, prices, level='##'):
    manifest, context, records, rows = cohort(directory)
    verdicts = check.render(context, records, False)
    verdicts_block = ['(no comparison: development-grade smoke)'] if not manifest.get('comparisons') else \
        ['```text', verdicts, '```'] + (['', POOLED_SENTENCE] if 'pooled[' in verdicts else [])
    models = sorted({r['executor']['model'] for r, _, _ in rows})
    baseline_sha, candidate_sha, mismatches = artifact_check(manifest, rows)
    tie_text = 'yes' if not mismatches else 'no with %s' % ', '.join(mismatches)
    out = ['%s %s' % (level, title), '',
           '- Cohort `%s`, seal `%s`, created %s.' % (manifest['cohort_id'], manifest['seal_sha256'], manifest['created_at']),
           '- Variants: %s.' % ', '.join('`%s/%s` (%s)' % (v['scenario_id'], v['variant_id'], v['split'])
                                         for v in manifest['variants']),
           '- Executor: %s, `%s`; as served: %s. Judge: mechanical hidden acceptance tests, blinded.' % (
               manifest['executor']['harness'], manifest['executor']['model'], ', '.join('`%s`' % m for m in models)),
           '- Artifacts: baseline (method, 8.4.1) `%s` and candidate `%s`, from the manifest; every '
           'record\'s artifact_sha256 matches its arm\'s: %s.' % (baseline_sha, candidate_sha, tie_text),
           ''] + verdicts_block + ['']
    out += episode_table(rows) + ['', not_counted_line(rows), ''] + arm_table(manifest, rows) \
        + ['', 'Per-episode dollars:', ''] + dollars_table(rows, prices) + ['', 'Audit:', ''] + audit_lines(rows) + ['']
    return out, records


def render():
    pilot = load(HERE / 'manifest.json')
    prices = load(HERE / 'price-table.json')['prices']
    out = ['# Third candidate cohort: the 9.0.0 candidate that runs only current workspaces, against the '
          '8.4.1 method', '',
          LIMIT, '',
           'Hypothesis: %s' % pilot['hypothesis'], '',
           'Arms: `method` receives the 8.4.1 install; `method:candidate` receives the 9.0.0 candidate as '
           'a fixed, single session at the cheapest tier. The smoke runs one episode of each arm on a '
           'development variant, to check that both installs stage and that the close chain records '
           'them; it gates nothing.', '']
    pilot_lines, pilot_records = section('Pilot: held-out variants', HERE, prices)
    out += pilot_lines
    for smoke_dir in sorted(HERE.glob('smoke*')):
        if smoke_dir.is_dir() and (smoke_dir / 'manifest.json').is_file():
            smoke_lines, _ = section('Smoke: %s' % smoke_dir.name, smoke_dir, prices)
            out += smoke_lines
    candidate, candidate_reason = decision.candidate_verdict(pilot_records)
    nr_verdict, nr_reason, nr_lower, nr_tripped = decision.no_regression_verdict(pilot_records)
    out += ['## Decision', '',
           '- `candidate`: **%s**%s' % (candidate, '' if candidate_reason is None else ' (%s)' % candidate_reason),
           '- ' + decision.format_no_regression(nr_verdict, nr_reason, nr_lower, nr_tripped), '']
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
