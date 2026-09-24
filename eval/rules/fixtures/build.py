"""Build the rule-ledger fixtures: small repositories, each valid or carrying one planted defect.

The builder states the expected coverage units by hand and computes hashes and historical lists
itself, independently of inventory.py and check_ledger.py. The fixtures are not committed: the tests
build them into a temporary directory. Usage: python3 eval/rules/fixtures/build.py <output dir>
"""
import copy
import hashlib
import json
import shutil
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


def main():
    if len(sys.argv) != 2:
        print('usage: build.py <output dir>', file=sys.stderr)
        return 2
    print('built %d fixtures in %s' % (build(sys.argv[1]), sys.argv[1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
