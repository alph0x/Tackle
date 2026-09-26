"""Build the rule-ledger fixtures: small repositories, each valid or carrying one planted defect.

The builder states the expected coverage units by hand and computes hashes and historical lists
itself, independently of inventory.py and check_ledger.py. The fixtures are not committed: the tests
build them into a temporary directory. Usage: python3 eval/rules/fixtures/build.py <output dir>
"""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = '''---
name: demo
description: Demo skill for ledger fixtures.
---

# Demo

**Demo 1.0.0** is outside every listed section.

## Public surface

One entry: `demo`. State requests in any language.

| Surface | Request | Result |
|---|---|---|
| **PLAN** | `plan` | Prepare briefs. PLAN-only stops before implementation. |

## PLAN and RUN

Resolve links from their containing file; see
[guide](references/guides/guide.md). Use the `demo` entry. `plan` prepares work.
- **First:** probe prerequisites. Wait for results.
* Star items count too.
+ Plus items count too.

<a id="state"></a>
## Compatibility and state

<!-- maintainer note, ignored -->
Version 8.x stays readable. Unknown telemetry stays `n/a`. All 16 rows pass. 16 rows exist.

## Core conventions

1. **Authority order** — user > spec. Preferences cannot override this order.
2) **Scope** — write only declared scope. **Bold** starts here.

## Output

State the result. Ask only when input changes affected work.
Is it ready? Say so! Then stop.
# Appendix

Appendix text is not covered.

## Guide map

Links only. Nothing here is covered.
'''

# The coverage units of SKILL above, in document order: (line, sentence).
UNITS = [
    (12, 'One entry: `demo`.'), (12, 'State requests in any language.'),
    (16, '**PLAN** `plan` Prepare briefs.'), (16, 'PLAN-only stops before implementation.'),
    (20, 'Resolve links from their containing file; see [guide](references/guides/guide.md).'),
    (21, 'Use the `demo` entry.'), (21, '`plan` prepares work.'),
    (22, '**First:** probe prerequisites.'), (22, 'Wait for results.'),
    (23, 'Star items count too.'), (24, 'Plus items count too.'),
    (30, 'Version 8.x stays readable.'), (30, 'Unknown telemetry stays `n/a`.'),
    (30, 'All 16 rows pass.'), (30, '16 rows exist.'),
    (34, '**Authority order** — user > spec.'), (34, 'Preferences cannot override this order.'),
    (35, '**Scope** — write only declared scope.'), (35, '**Bold** starts here.'),
    (39, 'State the result.'), (39, 'Ask only when input changes affected work.'),
    (40, 'Is it ready?'), (40, 'Say so!'), (40, 'Then stop.'),
]
LINE_21 = '[guide](references/guides/guide.md). Use the `demo` entry. `plan` prepares work.'

GUIDE = '# Guide\n\nChecks precede completion. Probe prerequisites first.\n\nReleases wait for the sweep.\n'

SUITE = ('# Suite run\n\n| Scenario | Control | Method | Read |\n|---|---|---|---|\n'
         '| s1 | 0 | 2 | discriminates |\n| s2 | 2 | 2 | null |\n| s3 | 2 | 0 | method-worse |\n')
MIXED = ('# Mixed run\n\ns1 contaminated control: verdict: null\ns2 placeholder scores: verdict: unscored\n'
         's3 partial: verdict: partial\n')
S3_ANSWER = ('# s3 answer sheet\n\n## Run records\n\n- control (clause removed) fell; method (clause present) avoided.\n'
             '- Verdict: ablation-discriminating.\n')

SUITE_PATH = 'eval/runs/2026-01-01-suite.md'
MIXED_PATH = 'eval/runs/2026-01-02-mixed.md'
ABSENT_PATH = 'eval/runs/2026-01-03-absent.md'
S3_PATH = 'eval/scenarios/s3-usage-trap/GROUND-TRUTH.md'


def key(sentence):
    return sentence[:48]


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def arm(outcome, seeds):
    return {'outcome': outcome, 'seeds': seeds}


def entry(scenario, recorded, mapped, seeds, comparison, baseline, candidate, basis, contamination=None):
    return {'scenario_id': scenario, 'recorded_label': recorded, 'mapped_label': mapped, 'seeds': seeds,
            'comparison': comparison, 'baseline': baseline, 'candidate': candidate,
            'contamination': contamination, 'basis': [{'line': n, 'quote': q} for n, q in basis]}


INDEX = {'schema': 'tackle-historical-index/1', 'records': {
    SUITE_PATH: [
        entry('s1-demo-trap', 'discriminates', 'discriminates', 1, 'no-skill', arm('fell', 1), arm('avoided', 1),
              [(5, '| s1 | 0 | 2 |')]),
        entry('s2-plan-trap', 'null', 'inert', 1, 'no-skill', arm('avoided', 1), arm('avoided', 1),
              [(6, '| s2 | 2 | 2 |')]),
        entry('s3-usage-trap', 'method-worse', 'method-worse', 1, 'no-skill', arm('avoided', 1), arm('fell', 1),
              [(7, '| s3 | 2 | 0 |')]),
    ],
    MIXED_PATH: [
        entry('s1-demo-trap', 'null', 'contaminated', 1, 'no-skill', arm('avoided', 1), arm('avoided', 1),
              [(3, 's1 contaminated control')], 'the fixture ships the rule under test'),
        entry('s2-plan-trap', 'unscored', 'unobserved', 1, 'no-skill', arm('placeholder', 1), arm('placeholder', 1),
              [(4, 's2 placeholder scores')]),
        entry('s3-usage-trap', 'partial', 'inconclusive', 'n/a', 'no-skill', arm('fell', 1), arm('partial', 2),
              [(5, 's3 partial')]),
    ],
    ABSENT_PATH: [
        entry('s2-plan-trap', 'method=pass', 'unobserved', 1, 'method-only', arm('absent', 0), arm('avoided', 1),
              [(9, 'SCENARIO s2 method=pass')]),
    ],
    S3_PATH: [
        entry('s3-usage-trap', 'ablation-discriminating', 'discriminates', 1, 'ablation', arm('fell', 1),
              arm('avoided', 1), [(5, 'control (clause removed) fell'), (6, 'ablation-discriminating')]),
    ],
}}


def rule(rid, statement, home, fragment, units, cls, scenarios=(), discovered=(), status='untested', cohort=None,
         mirrors=(), added='1.0.0'):
    return {'rule_id': rid, 'statement': statement, 'statement_sha256': sha(statement), 'home': home,
            'home_fragment': fragment, 'units': [key(u) for u in units], 'mirrors': list(mirrors), 'class': cls,
            'hot_path': home.split(':')[0] == 'SKILL.md',
            'origin': {'added_in': added, 'trigger': 'demo fixture', 'discovered_by': list(discovered)},
            'evidence': {'status': status, 'scenarios': list(scenarios), 'cohort_id': cohort, 'as_of': '2026-01-04'},
            'historical': []}


def base_ledger():
    rules = [
        rule('R-ENTRY-01', 'The skill has one entry and accepts any language.', 'SKILL.md:12', 'One entry: `demo`.',
             ['One entry: `demo`.', 'State requests in any language.'], 'behavioral', ['s1-demo-trap']),
        rule('R-PLAN-01', 'PLAN prepares briefs and stops before implementation.', 'SKILL.md:16',
             'PLAN-only stops before implementation.',
             ['**PLAN** `plan` Prepare briefs.', 'PLAN-only stops before implementation.'], 'safety-invariant',
             ['s2-plan-trap']),
        rule('R-INTAKE-01', 'Resolve links from their containing file and use the demo entry.', 'SKILL.md:20',
             'Resolve links from their containing file',
             [UNITS[4][1], 'Use the `demo` entry.', '`plan` prepares work.'], 'behavioral'),
        rule('R-INTAKE-02', 'Probe prerequisites first and wait for the results.', 'SKILL.md:22', 'probe prerequisites',
             ['**First:** probe prerequisites.', 'Wait for results.', 'Star items count too.',
              'Plus items count too.'], 'behavioral', mirrors=['references/guides/guide.md:3']),
        rule('R-EVID-01', 'Unknown telemetry stays n/a.', 'SKILL.md:30', 'Unknown telemetry stays `n/a`.',
             ['Unknown telemetry stays `n/a`.'], 'safety-invariant', ['s3-usage-trap']),
        rule('R-STATE-01', 'All sixteen rows exist and pass.', 'SKILL.md:30', 'All 16 rows pass.',
             ['All 16 rows pass.', '16 rows exist.'], 'format'),
        rule('R-COMM-01', 'The user outranks the specification, and preferences cannot change that order.',
             'SKILL.md:34', '**Authority order** — user > spec.',
             ['**Authority order** — user > spec.', 'Preferences cannot override this order.'], 'safety-invariant',
             ['s1-demo-trap', 's2-plan-trap'], ['s1-demo-trap']),
        rule('R-RUN-01', 'Write only declared scope.', 'SKILL.md:35', 'write only declared scope',
             ['**Scope** — write only declared scope.', '**Bold** starts here.'], 'safety-invariant', added='unknown'),
        rule('R-COMM-02', 'State the result.', 'SKILL.md:39', 'State the result.', ['State the result.'], 'format'),
        rule('R-COMM-03', 'Ask only when input changes affected work.', 'SKILL.md:39',
             'Ask only when input changes affected work.', ['Ask only when input changes affected work.'],
             'behavioral', ['s2-plan-trap'], status='discriminates', cohort='demo-cohort'),
        rule('R-COMM-04', 'Say whether the work is ready, then stop.', 'SKILL.md:40', 'Is it ready? Say so! Then stop.',
             ['Is it ready?', 'Say so!', 'Then stop.'], 'safety-invariant'),
        rule('R-RUN-02', 'Checks precede completion.', 'references/guides/guide.md:3', 'Checks precede completion.', [],
             'behavioral', ['s2-plan-trap']),
        rule('R-REL-01', 'Releases wait for the sweep.', 'references/guides/guide.md:5', 'Releases wait for the sweep.',
             [], 'maintainer'),
    ]
    return {'schema': 'tackle-rule-ledger/1', 'rules': rules,
            'non_normative': [{'unit': key('Version 8.x stays readable.'), 'reason': 'version note'}]}


def project(index, scenarios):
    rows = [{'record': record, 'label': e['recorded_label'], 'seeds': e['seeds']}
            for record, entries in index['records'].items() for e in entries if e['scenario_id'] in scenarios]
    return sorted(rows, key=lambda r: (r['record'], r['label'], str(r['seeds'])))


def refresh(ledger, index):
    for r in ledger['rules']:
        r['historical'] = project(index, set(r['evidence']['scenarios']))
    return ledger


def dump(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def base():
    return {'SKILL.md': SKILL, 'references/guides/guide.md': GUIDE, SUITE_PATH: SUITE, MIXED_PATH: MIXED,
            S3_PATH: S3_ANSWER, 'eval/scenarios/s1-demo-trap/GROUND-TRUTH.md': '# s1 answer sheet\n',
            'eval/scenarios/s2-plan-trap/GROUND-TRUTH.md': '# s2 answer sheet\n',
            'eval/cohorts/demo-cohort/manifest.json': '{"cohort_id": "demo-cohort"}\n',
            'ledger': refresh(base_ledger(), INDEX), 'index': copy.deepcopy(INDEX)}


def find(ledger, rid):
    return next(r for r in ledger['rules'] if r['rule_id'] == rid)


def reordered(t):
    t['ledger']['rules'].reverse()
    t['ledger']['rules'] = [dict(reversed(list(r.items()))) for r in t['ledger']['rules']]
    t['ledger'] = dict(reversed(list(t['ledger'].items())))
    t['index']['records'] = dict(reversed(list(t['index']['records'].items())))
    for entries in t['index']['records'].values():
        entries.reverse()


def set_rule(rid, **fields):
    def mutate(t):
        find(t['ledger'], rid).update(fields)
    return mutate


def set_evidence(rid, **fields):
    def mutate(t):
        find(t['ledger'], rid)['evidence'].update(fields)
        refresh(t['ledger'], t['index'])
    return mutate


def set_entry(record, scenario, **fields):
    def mutate(t):
        next(e for e in t['index']['records'][record] if e['scenario_id'] == scenario).update(fields)
        refresh(t['ledger'], t['index'])
    return mutate


def edit_skill(old, new):
    def mutate(t):
        assert t['SKILL.md'].count(old) == 1, old
        t['SKILL.md'] = t['SKILL.md'].replace(old, new)
    return mutate


def append_unit(rid, sentence):
    def mutate(t):
        find(t['ledger'], rid)['units'].append(key(sentence))
    return mutate


def add_retired(t, retired_in='1.1.0', hot_path=False):
    retired = rule('R-STATUS-01', 'Status once wrote a digest.', 'SKILL.md@v1.0.0:99', 'wrote a digest', [],
                   'behavioral')
    retired['retired_in'] = retired_in
    retired['hot_path'] = hot_path
    t['ledger']['rules'].append(retired)


def set_origin(rid, **fields):
    def mutate(t):
        find(t['ledger'], rid)['origin'].update(fields)
    return mutate


def restate(rid, statement):
    return set_rule(rid, statement=statement, statement_sha256=sha(statement))


def set_arm(record, scenario, side, **fields):
    def mutate(t):
        next(e for e in t['index']['records'][record] if e['scenario_id'] == scenario)[side].update(fields)
    return mutate


def move_record(old, new):
    def mutate(t):
        records = t['index']['records']
        records[new] = records.pop(old)
        refresh(t['ledger'], t['index'])
    return mutate


def duplicate_entry(t):
    records = t['index']['records'][SUITE_PATH]
    records.append(copy.deepcopy(records[0]))
    refresh(t['ledger'], t['index'])


def set_top(part, **fields):
    def mutate(t):
        t[part].update(fields)
    return mutate


def set_note(**fields):
    def mutate(t):
        t['ledger']['non_normative'][0].update(fields)
    return mutate


def drop_history(t):
    find(t['ledger'], 'R-ENTRY-01')['historical'].pop()


def truncate(t):
    t['ledger_text'] = dump(t['ledger'])[:200]


def remove_ledger(t):
    t['ledger'] = None


VARIANTS = {
    'valid-base': [],
    'valid-reordered': [reordered],
    'valid-retired': [add_retired],
    'added-sentence': [edit_skill('Ask only when input changes affected work.\n',
                                  'Ask only when input changes affected work. Never skip the checks.\n')],
    'wrong-home': [set_rule('R-COMM-02', home_fragment='State the outcome.')],
    'duplicate-id': [set_rule('R-COMM-03', rule_id='R-COMM-02')],
    'hash-drift': [set_rule('R-EVID-01', statement='Unknown telemetry stays n/a, always.')],
    'double-coverage': [append_unit('R-COMM-03', 'State the result.')],
    'discovery-only': [set_evidence('R-COMM-01', status='discriminates', cohort_id='demo-cohort',
                                    scenarios=['s1-demo-trap'])],
    'stale-unit': [append_unit('R-COMM-02', 'Removed sentence.')],
    'missing-section': [edit_skill('## Output\n', '## Results\n')],
    'key-collision': [edit_skill('State the result. Ask only', 'State the result. State the result. Ask only')],
    'table-row-uncovered': [edit_skill('PLAN-only stops before implementation. |',
                                       'PLAN-only stops before implementation. Handoff writes only its projection. |')],
    'bad-index-label': [set_entry(SUITE_PATH, 's2-plan-trap', mapped_label='discriminates')],
    'historical-mismatch': [drop_history],
    'bad-class': [set_rule('R-STATE-01', **{'class': 'style'})],
    'bad-rule-id': [set_rule('R-STATE-01', rule_id='R-FOO-01')],
    'hot-path-mismatch': [set_rule('R-RUN-02', hot_path=True)],
    'unknown-scenario': [set_evidence('R-EVID-01', scenarios=['s9-missing-trap'])],
    'cohort-mismatch': [set_evidence('R-EVID-01', cohort_id='c2')],
    'bad-record-label': [set_entry(SUITE_PATH, 's2-plan-trap', recorded_label='nullish')],
    'bad-basis-line': [set_entry(MIXED_PATH, 's1-demo-trap', basis=[{'line': 6, 'quote': 's1'}])],
    'basis-quote-mismatch': [set_entry(MIXED_PATH, 's1-demo-trap', basis=[{'line': 4, 'quote': 's1 contaminated'}])],
    'bad-rule-id-type': [set_rule('R-REL-01', rule_id=['R-REL-01'])],
    'bad-scenario-type': [lambda t: t['index']['records'][ABSENT_PATH][0].update(scenario_id=['s2-plan-trap'])],
    'missing-cohort': [set_evidence('R-COMM-03', cohort_id='ghost-cohort')],
    'wrong-cohort-manifest': [lambda t: t.update({'eval/cohorts/demo-cohort/manifest.json': '{"cohort_id": "other"}\n'})],
    'duplicate-section': [edit_skill('## Guide map\n', '## Output\n')],
    'unnormalized-statement': [restate('R-STATE-01', 'All sixteen  rows exist and pass.')],
    'long-fragment': [set_rule('R-INTAKE-01', home='SKILL.md:21', home_fragment=LINE_21[:61])],
    'retired-hot-path': [lambda t: add_retired(t, hot_path=True)],
    'bad-retired-in': [lambda t: add_retired(t, retired_in='soon')],
    'tested-without-cohort': [set_evidence('R-COMM-03', cohort_id=None)],
    'bad-status': [set_evidence('R-COMM-03', status='passed')],
    'bad-added-in': [set_origin('R-STATE-01', added_in='v1')],
    'bad-as-of': [set_evidence('R-STATE-01', as_of='24/09/2026')],
    'escaping-home': [set_rule('R-REL-01', home='../outside.md:1')],
    'bad-ledger-schema': [set_top('ledger', schema='tackle-rule-ledger/2')],
    'bad-index-schema': [set_top('index', schema='tackle-historical-index/2')],
    'bad-non-normative': [set_note(reason='')],
    'absent-with-seeds': [set_arm(ABSENT_PATH, 's2-plan-trap', 'baseline', seeds=1)],
    'method-only-with-baseline': [set_entry(SUITE_PATH, 's1-demo-trap', comparison='method-only')],
    'bad-comparison': [set_entry(SUITE_PATH, 's2-plan-trap', comparison='versus')],
    'bad-record-path': [move_record(ABSENT_PATH, 'eval/other/2026-01-03-absent.md')],
    'duplicate-entry': [duplicate_entry],
    'contamination-without-control': [set_entry(MIXED_PATH, 's2-plan-trap', contamination='x',
                                                mapped_label='contaminated')],
    'seeds-mismatch': [set_entry(SUITE_PATH, 's1-demo-trap', seeds='n/a')],
    'units-off-skill': [set_rule('R-COMM-02', home='references/guides/guide.md:3',
                                 home_fragment='Checks precede completion.', hot_path=False)],
    'bad-mirror': [set_rule('R-INTAKE-02', mirrors=['references/guides/guide.md:40'])],
    'unknown-field': [set_rule('R-STATE-01', notes='free text')],
    'invalid-json': [truncate],
    'missing-ledger': [remove_ledger],
}


def write(out, name, tree):
    root = out / name
    if root.exists():
        shutil.rmtree(root)
    for path, text in tree.items():
        if path in ('ledger', 'index', 'ledger_text'):
            continue
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    rules_dir = root / 'eval/rules'
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / 'historical-index.json').write_text(dump(tree['index']), encoding='utf-8')
    if 'ledger_text' in tree:
        (rules_dir / 'ledger.json').write_text(tree['ledger_text'], encoding='utf-8')
    elif tree['ledger'] is not None:
        (rules_dir / 'ledger.json').write_text(dump(tree['ledger']), encoding='utf-8')


def build(out):
    out = Path(out)
    for name, mutations in VARIANTS.items():
        tree = base()
        for mutate in mutations:
            mutate(tree)
        write(out, name, tree)
    return len(VARIANTS)


# --- gate fixtures: small two-revision git repos for the change gate, entirely separate from VARIANTS
# above (a structural-fixture concern) so neither `test_every_fixture_is_exercised`'s exact VARIANTS-vs-directory
# equality nor `test_fixture_build_is_deterministic`'s whole-tree byte digest ever sees a `.git/` directory.
# `--gate <base-rev>` diffs a committed BASE revision against whatever is on disk in --repo, so each fixture
# needs exactly one commit (the base); the "candidate" side is simply the mutated, uncommitted working tree.

GATE_SKILL = '''---
name: demo
description: Demo skill for gate fixtures.
---

# Demo

## Public surface

One entry: `demo`. State requests in any language.

## PLAN and RUN

**PLAN** `plan` Prepare briefs. PLAN-only stops before implementation.

## Compatibility and state

Version 8.x stays readable. Unknown telemetry stays `n/a`.

## Core conventions

1. **Authority order** — user > spec. Preferences cannot override this order.

## Output

State the result. Ask only when input changes affected work.
'''
GATE_GUIDE = 'Line one of the guide.\nLine two of the guide.\n'
GATE_MAINTAINING = 'Line one of maintaining.\nLine two of maintaining.\n'
GATE_INDEX = {'schema': 'tackle-historical-index/1', 'records': {}}
GIT_IDENTITY = ['-c', 'user.name=tackle-fixtures', '-c', 'user.email=fixtures@example.invalid']


def gate_background():
    """Five stable, unchanged-by-default rules covering GATE_SKILL's ten units exactly once each."""
    return [
        rule('R-ENTRY-01', 'Entry background rule one.', 'SKILL.md:10', 'One entry',
             ['One entry: `demo`.', 'State requests in any language.'], 'behavioral'),
        rule('R-PLAN-01', 'Plan background rule one.', 'SKILL.md:14', '**PLAN**',
             ['**PLAN** `plan` Prepare briefs.', 'PLAN-only stops before implementation.'], 'safety-invariant'),
        rule('R-STATE-01', 'State background rule one.', 'SKILL.md:18', 'Version 8.x',
             ['Version 8.x stays readable.', 'Unknown telemetry stays `n/a`.'], 'behavioral'),
        rule('R-COMM-01', 'Comm background rule one.', 'SKILL.md:22', '**Authority order**',
             ['**Authority order** — user > spec.', 'Preferences cannot override this order.'], 'safety-invariant'),
        rule('R-RUN-01', 'Run background rule one.', 'SKILL.md:26', 'State the result',
             ['State the result.', 'Ask only when input changes affected work.'], 'behavioral'),
    ]


def gate_rule(rid, statement, hot_path=True, cls='behavioral', status='untested', cohort=None, scenarios=(),
              discovered=(), mirrors=(), retired_in=None, home=None, fragment=None):
    """A rule not tied to any GATE_SKILL unit: hot-path rules reuse R-ENTRY-01's home line (a rule's `home`
    need not be unique; only `units` coverage keys are), so every gate fixture needs no SKILL.md edits."""
    if home is None:
        home, fragment = ('SKILL.md:10', 'One entry') if hot_path else ('references/guide.md:1', 'Line one')
    made = rule(rid, statement, home, fragment, [], cls, scenarios, discovered, status, cohort, mirrors)
    made['hot_path'] = hot_path
    if retired_in:
        made['retired_in'] = retired_in
    return made


def gate_tree(rules, cohort_id='demo-cohort'):
    return {
        'SKILL.md': GATE_SKILL, 'references/guide.md': GATE_GUIDE, 'MAINTAINING.md': GATE_MAINTAINING,
        'eval/scenarios/s1-demo-trap/GROUND-TRUTH.md': '# s1 answer sheet\n',
        'eval/cohorts/demo-cohort/manifest.json': '{"cohort_id": "demo-cohort"}\n',
        'eval/cohorts/2026-09-candidate/manifest.json': '{"cohort_id": "2026-09-candidate"}\n',
        'eval/rules/historical-index.json': dump(GATE_INDEX),
        'eval/rules/ledger.json': dump({'schema': 'tackle-rule-ledger/1', 'rules': rules, 'non_normative': []}),
    }


def git_run(root, *args, date=None):
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')
    if date:
        env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = date
    result = subprocess.run(['git', '-C', str(root)] + GIT_IDENTITY + list(args), capture_output=True, text=True,
                            env=env)
    if result.returncode != 0:
        raise RuntimeError('git %s failed: %s' % (' '.join(args), result.stderr))
    return result.stdout.strip()


def write_tree(root, tree):
    for path, text in tree.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')


def gate_repo(out, name, base_rules, candidate_rules=None, exceptions=None, date='2026-01-01T00:00:00'):
    """Commit `base_rules` as the sole (base) revision, then optionally mutate the working tree to
    `candidate_rules` (uncommitted: the "candidate" ledger --gate reads is just what is on disk) and/or
    write a fixture-local eval/rules/gate-exceptions.json. Returns the base commit's sha256."""
    root = out / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    git_run(root, 'init', '-q', '-b', 'main')
    write_tree(root, gate_tree(base_rules))
    base_sha = commit_gate(root, 'base', date)
    if candidate_rules is not None:
        write_tree(root, gate_tree(candidate_rules))
    if exceptions is not None:
        (root / 'eval/rules/gate-exceptions.json').write_text(dump(exceptions), encoding='utf-8')
    return base_sha


def commit_gate(root, message, date):
    git_run(root, 'add', '-A')
    git_run(root, 'commit', '-q', '-m', message, date=date)
    return git_run(root, 'rev-parse', 'HEAD')


def exception(rule_id, statement_sha256, reason='a recorded exception for a gate fixture', accepted='2026-01-01'):
    return {'rule_id': rule_id, 'statement_sha256': statement_sha256, 'reason': reason, 'accepted': accepted}


def build_gate(out):
    """Every gate fixture except the auto-resolution ones (those need several commits and tags:
    build_gate_auto does those). Returns {case_name: base_rev_sha}; case_name also names the scenario, so
    it is the only label a caller needs. Every one of these is a single-commit repo: the "candidate" side
    is just the mutated, uncommitted working tree gate_repo leaves behind."""
    out = Path(out)
    background = gate_background()
    bases = {}

    # add without evidence.
    added = background + [gate_rule('R-INTAKE-90', 'A brand new hot-path rule statement.')]
    bases['c1-add-untested'] = gate_repo(out, 'c1-add-untested', background, added)

    # delete (retire) without inventory: base evidence untested, empty mirrors.
    base_del = background + [gate_rule('R-INTAKE-91', 'A rule that will be deleted without inventory.')]
    cand_del = background + [dict(base_del[-1], retired_in='1.1.0', hot_path=False)]
    bases['c2-delete-no-inventory'] = gate_repo(out, 'c2-delete-no-inventory', base_del, cand_del)

    # add validated only by its discovering scenario.
    added = background + [gate_rule('R-INTAKE-92', 'A rule whose only scenario discovered it.',
                                    status='discriminates', cohort='2026-09-candidate', scenarios=['s1-demo-trap'],
                                    discovered=['s1-demo-trap'])]
    bases['c3-add-discovery-only'] = gate_repo(out, 'c3-add-discovery-only', background, added)

    # add with held-out evidence (a non-discovery scenario, this release's own cohort).
    added = background + [gate_rule('R-INTAKE-93', 'A rule added with real held-out evidence.',
                                    status='inconclusive', cohort='2026-09-candidate', scenarios=['s1-demo-trap'])]
    bases['c4-add-held-out-evidence'] = gate_repo(out, 'c4-add-held-out-evidence', background, added)

    # reword, no semantic change (the same words, reordered and repunctuated).
    base_reword = [dict(r) for r in background]
    base_reword[4] = dict(base_reword[4], statement='Always state the outcome; never skip a required step.')
    cand_reword = [dict(r) for r in base_reword]
    cand_reword[4] = dict(cand_reword[4], statement='Never skip a required step; always state the outcome.',
                          statement_sha256=sha('Never skip a required step; always state the outcome.'))
    bases['c5-reword-no-semantic-change'] = gate_repo(out, 'c5-reword-no-semantic-change', base_reword, cand_reword)

    # add citing a real but different cohort.
    added = background + [gate_rule('R-INTAKE-94', 'A rule citing the wrong cohort.', status='inert',
                                    cohort='demo-cohort')]
    bases['c21-add-unrelated-cohort'] = gate_repo(out, 'c21-add-unrelated-cohort', background, added)

    # delete (retire), prior evidence: base status was already non-untested.
    base_prior = background + [gate_rule('R-INTAKE-95', 'A rule already evidenced before this diff.',
                                         status='inert', cohort='demo-cohort')]
    cand_prior = background + [dict(base_prior[-1], retired_in='1.1.0', hot_path=False)]
    bases['c22-delete-prior-evidence'] = gate_repo(out, 'c22-delete-prior-evidence', base_prior, cand_prior)

    # delete (retire), restated elsewhere: not a safety invariant, any resolving mirror suffices.
    base_moved = background + [gate_rule('R-INTAKE-96', 'A rule whose content moved to the guide.', cls='behavioral')]
    cand_moved = background + [dict(base_moved[-1], retired_in='1.1.0', hot_path=False,
                                    mirrors=['references/guide.md:1'])]
    bases['c23-delete-restated-elsewhere'] = gate_repo(out, 'c23-delete-restated-elsewhere', base_moved, cand_moved)

    # retire in place, no prior evidence, no superseding rule: still counted as deleted.
    base_inplace = background + [gate_rule('R-INTAKE-97', 'A rule retired in place with no evidence.')]
    cand_inplace = background + [dict(base_inplace[-1], retired_in='1.1.0', hot_path=False)]
    bases['c29-retire-in-place'] = gate_repo(out, 'c29-retire-in-place', base_inplace, cand_inplace)

    # scope boundary (a): a non-hot-path rule added untested is out of scope.
    added = background + [gate_rule('R-INTAKE-98', 'A non-hot-path rule added untested.', hot_path=False,
                                    cls='behavioral')]
    bases['c30a-out-of-scope-add'] = gate_repo(out, 'c30a-out-of-scope-add', background, added)

    # scope boundary (b): a hot-path rule demoted to hot_path=false while its statement changes stays in scope.
    base_demote = background + [gate_rule('R-INTAKE-99', 'Original demoted rule statement text.')]
    cand_demote = background + [gate_rule('R-INTAKE-99', 'Original demoted rule statement text changed indeed.',
                                          hot_path=False, home='references/guide.md:2', fragment='Line two')]
    bases['c30b-scope-survives-demotion'] = gate_repo(out, 'c30b-scope-survives-demotion', base_demote, cand_demote)

    # change with evidence: the positive path for a changed (non-reworded) rule.
    base_change = background + [gate_rule('R-EVID-90', 'Alpha states one thing plainly indeed.')]
    cand_change = background + [gate_rule(
        'R-EVID-90', 'Alpha states one wholly different thing plainly indeed and completely.',
        status='inert', cohort='2026-09-candidate')]
    bases['c31-change-with-evidence'] = gate_repo(out, 'c31-change-with-evidence', base_change, cand_change)

    # exception applies to an in-scope changed rule left untested.
    base_exc = background + [gate_rule('R-EVID-91', 'Beta requires one careful step precisely.')]
    new_statement = 'Beta requires one very careful additional step precisely now.'
    cand_exc = background + [gate_rule('R-EVID-91', new_statement)]
    bases['c32-exception-applies'] = gate_repo(out, 'c32-exception-applies', base_exc, cand_exc,
                                               exceptions=[exception('R-EVID-91', sha(new_statement))])

    # exception void: the statement changes again after the entry was recorded.
    cand_exc_void = background + [gate_rule('R-EVID-91', new_statement + ' Once more, changed.')]
    bases['c33-exception-void'] = gate_repo(out, 'c33-exception-void', base_exc, cand_exc_void,
                                            exceptions=[exception('R-EVID-91', sha(new_statement))])

    # safety-invariant retirement (a): mirrors only outside the installed skill.
    base_si = background + [gate_rule('R-EVID-92', 'A safety invariant retired from the ledger.',
                                      cls='safety-invariant')]
    cand_si_a = background + [dict(base_si[-1], retired_in='1.1.0', hot_path=False,
                                   mirrors=['MAINTAINING.md:1'])]
    bases['c34a-safety-invariant-outside-only'] = gate_repo(out, 'c34a-safety-invariant-outside-only',
                                                            base_si, cand_si_a)

    # safety-invariant retirement (b): the same, with one mirror inside the installed skill too.
    cand_si_b = background + [dict(base_si[-1], retired_in='1.1.0', hot_path=False,
                                   mirrors=['MAINTAINING.md:1', 'SKILL.md:10'])]
    bases['c34b-safety-invariant-one-inside'] = gate_repo(out, 'c34b-safety-invariant-one-inside',
                                                          base_si, cand_si_b)

    # safety-invariant retirement (c): reclassified to behavioral in the candidate, but it was a safety
    # invariant at base. An outside-only mirror (as in the (a) variant above) so this exercises the
    # safety-invariant-specific check, not just the generic empty-mirrors one: the base class must still
    # count even though the candidate reclassifies.
    cand_si_c = background + [dict(base_si[-1], retired_in='1.1.0', hot_path=False, mirrors=['MAINTAINING.md:1'],
                                   **{'class': 'behavioral'})]
    bases['c34c-safety-invariant-reclassified'] = gate_repo(out, 'c34c-safety-invariant-reclassified',
                                                            base_si, cand_si_c)

    # exceptions never apply to a deletion.
    base_noexc = background + [gate_rule('R-EVID-93', 'A rule retired with an exception that cannot help.')]
    cand_noexc = background + [dict(base_noexc[-1], retired_in='1.1.0', hot_path=False)]
    bases['c35-no-exception-for-deletion'] = gate_repo(
        out, 'c35-no-exception-for-deletion', base_noexc, cand_noexc,
        exceptions=[exception('R-EVID-93', base_noexc[-1]['statement_sha256'])])

    # exception-file state (a): an entry names a rule_id absent from the candidate ledger; otherwise a
    # clean diff.
    bases['c36a-exception-ghost-rule'] = gate_repo(out, 'c36a-exception-ghost-rule', background, background,
                                                   exceptions=[exception('R-EVID-94', sha('anything'))])

    # exception-file state (b): a valid entry whose rule this diff does not touch; otherwise a clean diff
    # (printed dormant).
    bases['c36b-exception-dormant'] = gate_repo(out, 'c36b-exception-dormant', background, background,
                                                exceptions=[exception('R-ENTRY-01', background[0]['statement_sha256'])])

    # exception-file state (c): no gate-exceptions.json at all, on a clean diff.
    bases['c36c-no-exceptions-file'] = gate_repo(out, 'c36c-no-exceptions-file', background, background)

    return bases


def build_gate_auto(out):
    """The three `--gate auto` resolution fixtures: (a) only tags predate the ledger; (b) a ledger-bearing
    tag behind HEAD; (c) a tag on HEAD itself, with an older ledger-bearing tag behind it. Each needs several
    commits and tags, so it is built independently of gate_repo's single-base-commit shape. Returns
    {case_name: root_path}; the tests run --gate auto against each root directly (no base-rev argument)."""
    out = Path(out)
    background = gate_background()
    cases = {}

    def repo_root(name):
        root = out / name
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True)
        git_run(root, 'init', '-q', '-b', 'main')
        return root

    # (a) only tags predate the ledger: c0 (tag v1, no ledger) -> c1 (adds the ledger) = HEAD.
    root = repo_root('c28a-only-tags-predate-ledger')
    write_tree(root, {'README.md': 'no ledger yet\n'})
    commit_gate(root, 'no ledger', '2026-01-01T00:00:00')
    git_run(root, 'tag', 'v1')
    write_tree(root, gate_tree(background))
    commit_gate(root, 'adds the ledger', '2026-01-02T00:00:00')
    cases['c28a-only-tags-predate-ledger'] = root

    # (b) a ledger-bearing tag behind HEAD: c0 (no ledger) -> c1 (adds ledger, tag v1) -> c2 (tag v2) ->
    # c3 = HEAD (untagged).
    root = repo_root('c28b-ledger-tag-behind-head')
    write_tree(root, {'README.md': 'no ledger yet\n'})
    commit_gate(root, 'no ledger', '2026-01-01T00:00:00')
    write_tree(root, gate_tree(background))
    commit_gate(root, 'adds the ledger', '2026-01-02T00:00:00')
    git_run(root, 'tag', 'v1')
    write_tree(root, gate_tree(background + [gate_rule('R-EVID-95', 'An extra rule at v2.')]))
    commit_gate(root, 'v2 change', '2026-01-03T00:00:00')
    git_run(root, 'tag', 'v2')
    write_tree(root, gate_tree(background + [gate_rule('R-EVID-95', 'An extra rule at v2.'),
                                              gate_rule('R-EVID-96', 'An extra rule after v2, untagged.')]))
    commit_gate(root, 'untagged change', '2026-01-04T00:00:00')
    cases['c28b-ledger-tag-behind-head'] = root

    # (c) a tag on HEAD itself, with an older ledger-bearing tag behind it: c0 (no ledger) -> c1 (adds
    # ledger, tag v1) -> c2 = HEAD (tag v2, on HEAD itself, never the resolved base).
    root = repo_root('c28c-tag-on-head-itself')
    write_tree(root, {'README.md': 'no ledger yet\n'})
    commit_gate(root, 'no ledger', '2026-01-01T00:00:00')
    write_tree(root, gate_tree(background))
    commit_gate(root, 'adds the ledger', '2026-01-02T00:00:00')
    git_run(root, 'tag', 'v1')
    write_tree(root, gate_tree(background + [gate_rule('R-EVID-95', 'An extra rule at head.')]))
    commit_gate(root, 'head change', '2026-01-03T00:00:00')
    git_run(root, 'tag', 'v2')
    cases['c28c-tag-on-head-itself'] = root

    return cases


def main():
    if len(sys.argv) != 2:
        print('usage: build.py <output dir>', file=sys.stderr)
        return 2
    print('built %d fixtures in %s' % (build(sys.argv[1]), sys.argv[1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
