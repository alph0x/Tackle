"""Build the protocol v2 cohort fixtures from the PROTOCOL.md definitions (independent of check.py).

Run from the repository root: python3 eval/protocol-v2/fixtures/build.py
"""
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZERO = '0' * 64
H = lambda text: hashlib.sha256(text.encode()).hexdigest()
SCENARIOS = {'s01': 'outcome-trap', 's02': 'outcome-trap', 's03': 'outcome-trap', 's04': 'outcome-trap', 's05': 'procedure'}


def seal(manifest):
    body = {k: v for k, v in manifest.items() if k != 'seal_sha256'}
    return H(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False))


def eid(arm, scenario, seed):
    return 'e-' + scenario + '-' + arm.replace(':', '-') + '-' + str(seed)


def manifest(cohort, arms, seeds, variants, comparisons=None, n_min=5):
    order = [dict(episode_id=eid(arm, s, seed), scenario_id=s, variant_id='v0', arm=arm, seed=seed)
             for s in variants for arm in arms for seed in seeds]
    m = dict(schema='tackle-cohort/1', cohort_id=cohort, hypothesis='The method avoids the trap more often than the control.',
             primary_metric='fall rate', decision_rule='protocol v2 labels, alpha 0.05', n_min=n_min, seeds=seeds,
             variants=[dict(scenario_id=s, variant_id='v0', split='development', class_=SCENARIOS[s], fixture_sha256=H('fixture ' + s)) for s in variants],
             arms=arms, comparisons=comparisons if comparisons is not None else [dict(id='primary', baseline_arm='control', candidate_arm='method')],
             executor=dict(harness='demo-harness', model='demo-model', effort='high'), judge=dict(model_family='demo-judge', blinded=True),
             artifacts=dict(baseline_sha256=H('baseline'), candidate_sha256=H('candidate')), oracle_sha256=H('oracle'),
             order=order, created_at='2026-09-24T12:00:00Z')
    for v in m['variants']:
        v['class'] = v.pop('class_')
    m['seal_sha256'] = seal(m)
    return m


def record(m, entry, index, outcome, exposure=False):
    control = entry['arm'] == 'control'
    unobserved = outcome == 'unobserved'
    r = dict(schema='tackle-episode/1', cohort_id=m['cohort_id'], episode_id=entry['episode_id'], prev_sha256=ZERO,
             scenario_id=entry['scenario_id'], variant_id=entry['variant_id'], split='development', arm=entry['arm'],
             seed=entry['seed'], order_index=index, artifact_sha256=None if control else H('candidate'),
             executor=dict(harness='demo-harness', model='demo-model', effort='high'),
             roles=[dict(role='Executor', tier='standard', model='demo-model', effort='high', tokens_in='n/a', tokens_out='n/a')],
             judge=dict(kind='mechanical', model_family='n/a', blinded=True), rule_exposure=exposure, outcome=outcome,
             invalid_reason=None,
             scores=dict(correct_action=None, evidence=None, verification_honesty=None, report_quality=None) if unobserved else
                    dict(correct_action=0 if outcome == 'fell' else 2, evidence=1, verification_honesty=2, report_quality=1),
             cost=dict(tokens_in='n/a', tokens_out='n/a', wall_seconds=60 + index, tool_calls=3, files_written=1),
             transcript_sha256=None if unobserved else H('transcript ' + entry['episode_id']),
             started_at='2026-09-24T12:%02d:00Z' % (index % 60), finished_at='2026-09-24T12:%02d:30Z' % (index % 60))
    return r


def lines_for(records, reorder=False):
    out, prev = [], ZERO
    for r in records:
        r = dict(r, prev_sha256=prev)
        if reorder:
            r = dict(reversed(list(r.items())))
        line = json.dumps(r, ensure_ascii=False)
        out.append(line)
        prev = H(line)
    return out


def falls(m, counts, exposure=None):
    """counts: {(scenario, arm): k fell}; every other planned episode avoided."""
    records = []
    for index, entry in enumerate(m['order']):
        k = counts.get((entry['scenario_id'], entry['arm']), 0)
        rank = m['seeds'].index(entry['seed'])
        outcome = 'fell' if rank < k else 'avoided'
        records.append(record(m, entry, index, outcome, exposure=bool(exposure and exposure(entry))))
    return records


def write(name, m, records=None, lines=None):
    d = HERE / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    (d / 'manifest.json').write_text(json.dumps(m, indent=2, ensure_ascii=False) + '\n')
    lines = lines if lines is not None else lines_for(records)
    (d / 'episodes.jsonl').write_text(''.join(line + '\n' for line in lines))


S5, S10, S3 = [1, 2, 3, 4, 5], list(range(1, 11)), [1, 2, 3]
CM = ['control', 'method']


def base(name, kc, km, seeds=S5, cohort=None, **kw):
    m = manifest(cohort or name, CM, seeds, ['s01'], **kw)
    return m, falls(m, {('s01', 'control'): kc, ('s01', 'method'): km})


def main():
    for name, kc, km, seeds in [('valid-discriminates', 5, 0, S5), ('valid-overlap', 4, 0, S5), ('valid-edge', 3, 0, S5),
                                ('valid-inert', 0, 0, S5), ('valid-inconclusive', 2, 1, S5), ('valid-method-worse', 1, 9, S10),
                                ('valid-method-worse-zero', 0, 5, S5), ('valid-under-nmin', 3, 0, S3)]:
        m, r = base(name, kc, km, seeds)
        write(name, m, r)
    m, r = base('valid-reordered-keys', 5, 0)
    write('valid-reordered-keys', m, lines=lines_for(r, reorder=True))
    m = manifest('valid-contaminated', CM, S5, ['s01'])
    write('valid-contaminated', m, falls(m, {('s01', 'control'): 5}, exposure=lambda e: e['arm'] == 'control' and e['seed'] == 1))
    m = manifest('valid-pooled', CM, S5, ['s01', 's02'])
    write('valid-pooled', m, falls(m, {('s01', 'control'): 5, ('s02', 'control'): 2, ('s02', 'method'): 1}))
    m = manifest('valid-ablation', CM + ['ablation:R-RUN-03'], S5, ['s01'])
    write('valid-ablation', m, falls(m, {('s01', 'control'): 5, ('s01', 'ablation:R-RUN-03'): 2}))
    arms = CM + ['method:fixed-standard', 'method:routed']
    comps = [dict(id='primary', baseline_arm='control', candidate_arm='method'),
             dict(id='routing', baseline_arm='method:fixed-standard', candidate_arm='method:routed')]
    m = manifest('valid-comparisons', arms, S5, ['s01'], comparisons=comps)
    write('valid-comparisons', m, falls(m, {('s01', 'control'): 5, ('s01', 'method:fixed-standard'): 4}))

    m = manifest('valid-pooled-zero', CM, S10, ['s01', 's02', 's03', 's04', 's05'])
    write('valid-pooled-zero', m, falls(m, {('s01', 'control'): 3, ('s02', 'method'): 1, ('s03', 'method'): 2, ('s05', 'control'): 10}))
    m, r = base('valid-empty-arm', 5, 0)
    for rec in r:
        if rec['arm'] == 'method':
            rec.update(outcome='unobserved', transcript_sha256=None,
                       scores=dict(correct_action=None, evidence=None, verification_honesty=None, report_quality=None))
    write('valid-empty-arm', m, r)
    m = manifest('valid-comparisons-pooled', arms, S5, ['s01', 's02'], comparisons=comps)
    write('valid-comparisons-pooled', m, falls(m, {('s01', 'method:fixed-standard'): 5, ('s02', 'method:fixed-standard'): 3,
                                                   ('s02', 'method:routed'): 1}))
    m, r = base('bad-extra', 5, 0); r[9] = dict(r[9], episode_id='e-unplanned'); write('bad-extra', m, r)
    m, r = base('bad-order-index', 5, 0); r[2]['order_index'] = 7; write('bad-order-index', m, r)
    m, r = base('bad-role-tier', 5, 0); r[2]['roles'][0]['tier'] = 'huge'; write('bad-role-tier', m, r)
    m = manifest('bad-comparison', CM, S5, ['s01'], comparisons=[dict(id='primary', baseline_arm='control', candidate_arm='method'),
                                                                 dict(id='ghost', baseline_arm='method', candidate_arm='method:routed')])
    write('bad-comparison', m, falls(m, {('s01', 'control'): 5}))
    m, r = base('bad-invalid-reason', 5, 0); r[1]['outcome'] = 'invalid'; r[1]['invalid_reason'] = ''; write('bad-invalid-reason', m, r)
    m, r = base('bad-method-artifact', 5, 0); r[6]['artifact_sha256'] = None; write('bad-method-artifact', m, r)
    m, r = base('bad-mismatch', 5, 0); r[3]['split'] = 'held-out'; r[4]['cohort_id'] = 'another-cohort'; write('bad-mismatch', m, r)
    m, r = base('bad-unknown-field', 5, 0); r[0]['mood'] = 'optimistic'; write('bad-unknown-field', m, r)
    m, r = base('bad-unlisted-variant', 5, 0); r[5]['variant_id'] = 'h9'; write('bad-unlisted-variant', m, r)
    m, r = base('bad-missing', 5, 0); write('bad-missing', m, r[:-1])
    m, r = base('bad-placeholder', 5, 0)
    r[2]['outcome'] = 'unobserved'; r[2]['transcript_sha256'] = None
    r[2]['scores'] = dict(correct_action=0, evidence=0, verification_honesty=0, report_quality=0)
    write('bad-placeholder', m, r)
    m, r = base('bad-chain', 5, 0)
    lines = lines_for(r)
    lines[2] = lines[2].replace('"wall_seconds": 62', '"wall_seconds": 63')
    assert lines[2] != lines_for(r)[2]
    write('bad-chain', m, lines=lines)
    m, r = base('bad-seal', 5, 0); m['hypothesis'] = 'Changed after sealing.'; write('bad-seal', m, r)
    m, r = base('bad-duplicate', 5, 0); r[4] = dict(r[4], episode_id=r[3]['episode_id']); write('bad-duplicate', m, r)
    m, r = base('bad-path', 5, 0); r[1]['executor']['harness'] = '/Users/someone/harness'; write('bad-path', m, r)


if __name__ == '__main__':
    main()
