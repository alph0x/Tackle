"""Replay every step of .github/workflows/ci.yml locally on a release candidate (MAINTAINING before-tagging step 2).

Each step of both jobs gets one record: replayed with its exit, covered by a named record, or not replayed with the
reason. The mechanical block runs exactly as extracted from ci.yml, under bash with `set -eu`, in the candidate tree.
The step list below is checked against the workflow's own step names, in order, so a workflow that gained, lost or
renamed a step stops this tool instead of being replayed from a stale list (the 10.2.0 tool hardcoded names and never
compared them). Nothing is installed and nothing is uploaded.

Arguments: --repo --workspace --candidate --records --version --registry310 --registry314 --interpreter310 --interpreter314
A registry record must be the bound full_registry.py metadata for the exact candidate and interpreter.
Writes <records dir>/ci-replay.json and one stdout/stderr pair per replayed step; exit 1 when a replayed step fails,
2 when the workflow's steps differ from the list below.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import importlib.util
_support_spec=importlib.util.spec_from_file_location('release_support',Path(__file__).with_name('release_support.py'))
support=importlib.util.module_from_spec(_support_spec);_support_spec.loader.exec_module(support)

import argparse,os,hashlib
parser=argparse.ArgumentParser()
parser.add_argument('--config',required=True)
for name in ('repo','workspace','candidate','records','version','registry310','registry314','interpreter310','interpreter314'):parser.add_argument('--'+name,required=True)
args=parser.parse_args();
_config_spec=importlib.util.spec_from_file_location('release_config',Path(__file__).with_name('config.py'));config=importlib.util.module_from_spec(_config_spec);_config_spec.loader.exec_module(config);cfg=config.load(args.config)
if args.version != cfg['version'] or Path(args.workspace).resolve() != Path(cfg['workspace']).resolve():raise SystemExit('configuration version or workspace mismatch')
tree=Path(args.repo).resolve(strict=True);workspace=Path(args.workspace).resolve(strict=True)
import re
stamp_match=re.search(r'^\*\*Tackle ([0-9]+[.][0-9]+[.][0-9]+)\*\*',(tree/'skills/tackle/SKILL.md').read_text(),re.M)
if stamp_match is None or stamp_match[1]!=args.version:raise SystemExit('candidate methodology/version argument mismatch')
if subprocess.check_output(['git','rev-parse','HEAD'],cwd=tree,text=True).strip()!=args.candidate:raise SystemExit('candidate HEAD mismatch')
out,reg310,reg314=(Path(x).resolve() for x in (args.records,args.registry310,args.registry314))
env=dict(os.environ);runtime_bin=out/'runtime-bin'
support.require_candidate(tree,args.candidate)
if reg310==reg314:raise SystemExit('registry records must be distinct')
expected_records={reg310:(cfg['runtimes']['py310']['version'],args.interpreter310),reg314:(cfg['runtimes']['py314']['version'],args.interpreter314)}
for label, interpreter in (('py310', args.interpreter310), ('py314', args.interpreter314)):
    if Path(interpreter).resolve() != Path(cfg['runtimes'][label]['path']).resolve():raise SystemExit('runtime path mismatch')
for record,(version,interpreter) in expected_records.items():support.registry(record,version,interpreter,args.candidate)
out.mkdir(parents=True, exist_ok=False)
runtime_bin.mkdir();(runtime_bin/'python3').symlink_to(Path(args.interpreter314).resolve());(runtime_bin/'python3.10').symlink_to(Path(args.interpreter310).resolve())
env['PATH']=str(runtime_bin)+os.pathsep+env.get('PATH','')
workflow = (tree / '.github/workflows/ci.yml').read_text()
marker = '      - name: Run the documented mechanical release checks\n        run: |\n'
if workflow.count(marker) != 1:
    raise SystemExit('ci.yml: the mechanical block was not found exactly once')
block = []
for line in workflow.split(marker, 1)[1].splitlines():
    if not line.startswith('          '):
        break
    block.append(line[10:])
mechanical = '\n'.join(block) + '\n'
(out / 'mechanical.sh').write_text(mechanical)


def workflow_steps(text):
    jobs, job = {}, None
    in_jobs = False
    for line in text.splitlines():
        if line == 'jobs:':
            in_jobs = True
        elif in_jobs and re.match(r'^  [A-Za-z][\w-]*:$', line):
            job = line.strip()[:-1]
            jobs[job] = []
        elif job and re.match(r'^      - (name|uses): ', line):
            key, value = re.match(r'^      - (name|uses): (.*)$', line).groups()
            jobs[job].append(value if key == 'name' else 'uses ' + value)
    return jobs


def run(name,argv):
    return support.capture(name,argv,tree,out,env=env,timeout=900)['exit']


def registry(record):
    version,interpreter=expected_records[record]
    return support.registry(record,version,interpreter,args.candidate)


NO_SUDO = 'needs sudo and package installs, forbidden before publication; observed only in CI'
CHECKOUT = {'status': 'not replayed', 'reason': 'the candidate tree is the local checkout'}
UPLOAD = {'status': 'not replayed', 'reason': 'upload is hosted only'}
steps = [
    ('sweep', 'uses actions/checkout@v7', CHECKOUT),
    ('sweep', 'Run the documented mechanical release checks',
     {'command': 'bash mechanical.sh', 'status': 'replayed', 'exit': lambda: run('mechanical', ['bash', str(out / 'mechanical.sh')])}),
    ('sweep', 'Install every awk the lint-row suite exercises', {'status': 'not replayed', 'reason': NO_SUDO}),
    ('sweep', 'Run every registered deterministic suite with strict discovery (verifies fixtures and harnesses, not agent behavior)',
     {'status': 'covered', 'reason': 'the full registry under the local candidate for the runner python3 (3.14)',
      'covered_by': lambda: registry(reg314)}),
    ('sweep', 'Check evidence-record currency (verifies records and claims, not agent behavior)',
     {'command': 'python3 eval/records/check_currency.py --repo .', 'status': 'replayed',
      'exit': lambda: run('currency', ['python3', 'eval/records/check_currency.py', '--repo', '.'])}),
    ('sweep', 'Run the change gate, structural-only (no release cohort to cite from CI)',
     {'command': 'python3 eval/rules/check_ledger.py --repo . --gate auto', 'status': 'replayed',
      'exit': lambda: run('ledger', ['python3', 'eval/rules/check_ledger.py', '--repo', '.', '--gate', 'auto'])}),
    ('sweep', 'Account for every removed rule-home sentence unit, structural-only',
     {'command': 'python3 eval/rules/check_unit_diff.py --repo . --base auto', 'status': 'replayed',
      'exit': lambda: run('unitdiff', ['python3', 'eval/rules/check_unit_diff.py', '--repo', '.', '--base', 'auto'])}),
    ('sweep', 'Preserve deterministic outcomes and raw command streams', UPLOAD),
    ('registry-floor', 'uses actions/checkout@v7', CHECKOUT),
    ('registry-floor', 'Use the minimum Python that scripts/README.md declares',
     {'status': 'not replayed', 'reason': 'setup-python is hosted only; local python3.10 is used instead'}),
    ('registry-floor', 'Install every awk the lint-row suite exercises', {'status': 'not replayed', 'reason': NO_SUDO}),
    ('registry-floor', 'Run every registered deterministic suite on the minimum Python (verifies fixtures and harnesses, not agent behavior)',
     {'status': 'covered', 'reason': 'the full registry under python3.10 (the python3 assertion of this step runs below)',
      'covered_by': lambda: registry(reg310)}),
    ('registry-floor', 'Preserve deterministic outcomes and raw command streams', UPLOAD),
]
actual = workflow_steps(workflow)
expected = {}
for job, name, _ in steps:
    expected.setdefault(job, []).append(name)
if actual != expected:
    print('ci.yml steps differ from the replay list; nothing replayed', file=sys.stderr)
    for job in sorted(set(actual) | set(expected)):
        for a, b in zip(actual.get(job, []) + [None] * 20, expected.get(job, []) + [None] * 20):
            if a != b:
                print('  %s: workflow %r, replay %r' % (job, a, b), file=sys.stderr)
                break
    raise SystemExit(2)
records = []
for job, name, spec in steps:
    rec = {'job': job, 'step': name}
    for key, value in spec.items():
        rec[key] = value() if callable(value) else value
    records.append(rec)
    if name.startswith('Run every registered') and job == 'registry-floor':
        # the step's own first command, replayed under the local minimum interpreter
        records.append({'job': job, 'step': 'python3 version assertion (first command of the step above)',
                        'command': "python3.10 -c 'import sys; assert sys.version_info[:2] == (3, 10), sys.version'",
                        'status': 'replayed',
                        'exit': run('floor-version', ['python3.10', '-c', 'import sys; assert sys.version_info[:2] == (3, 10), sys.version'])})
failed = [s for s in records if s['status'] == 'replayed' and s['exit'] != 0]
failed += [s for s in records if s['status'] == 'covered' and not (s['covered_by']['passed'] and s['covered_by']['complete'])]
head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=tree, capture_output=True, text=True).stdout.strip()
try:support.require_candidate(tree,args.candidate)
except ValueError as error:failed.append({'candidate_drift':str(error)})
(out / 'ci-replay.json').write_text(json.dumps({'candidate': head, 'steps': records, 'passed': not failed}, indent=2) + '\n')
for s in records:
    print('%-15s %-60s %s %s' % (s['job'], s['step'][:60], s['status'], s.get('exit', '')))
print('ci replay:', 'PASS' if not failed else 'FAIL (%d)' % len(failed))
raise SystemExit(1 if failed else 0)
