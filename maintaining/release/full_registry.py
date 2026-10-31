"""One complete release registry with candidate, interpreter and child evidence."""
import argparse,datetime,json,os,re,subprocess,sys
from pathlib import Path

import importlib.util
_support_spec=importlib.util.spec_from_file_location('release_support',Path(__file__).with_name('release_support.py'))
support=importlib.util.module_from_spec(_support_spec);_support_spec.loader.exec_module(support)

parser=argparse.ArgumentParser()
parser.add_argument('--config',required=True)
for name in ('repo','workspace','candidate','records','version','interpreter','label'):parser.add_argument('--'+name,required=True)
parser.add_argument('--changed',action='append',default=[])
args=parser.parse_args();
_config_spec=importlib.util.spec_from_file_location('release_config',Path(__file__).with_name('config.py'));config=importlib.util.module_from_spec(_config_spec);_config_spec.loader.exec_module(config);cfg=config.load(args.config)
if args.version != cfg['version'] or Path(args.workspace).resolve() != Path(cfg['workspace']).resolve():raise SystemExit('configuration version or workspace mismatch')
root=support.require_candidate(args.repo,args.candidate);workspace=Path(args.workspace).resolve(strict=True)
match=re.search(r'^\*\*Tackle ([0-9]+[.][0-9]+[.][0-9]+)\*\*',(root/'skills/tackle/SKILL.md').read_text(),re.M)
if match is None or match[1]!=args.version:raise SystemExit('candidate methodology/version mismatch')
if not re.fullmatch('[A-Za-z0-9_-]+',args.label):raise SystemExit('invalid registry label')
records=Path(args.records).resolve();records.mkdir(parents=True,exist_ok=False)
identity=support.probe(args.interpreter);interpreter=identity['resolved']
if args.label not in cfg['runtimes'] or Path(args.interpreter).resolve()!=Path(cfg['runtimes'][args.label]['path']).resolve() or not config.runtime_ok(cfg,args.label,identity['version']):raise SystemExit('selected interpreter version or path mismatch')
binding=records/'runtime-bin';binding.mkdir();(binding/'python3').symlink_to(interpreter)
environment=dict(os.environ);environment['PATH']=str(binding)+os.pathsep+environment.get('PATH','')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');name='registry-'+args.label+'-'+stamp;out=records/name
argv=[interpreter,'-I','-B','eval/run_suites.py','--phase','release','--output',str(out)]
for relative in args.changed:argv.extend(['--changed',relative])
observed=support.capture(name,argv,root,records,env=environment,timeout=1800)
data=dict(observed,revision=args.candidate,interpreter=json.dumps(identity['version']),interpreter_identity=identity,changed_paths=args.changed,results=str(out/'results.json'))
data['revision_after']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
try:support.require_candidate(root,args.candidate)
except ValueError as error:data['candidate_drift']=str(error);data['passed']=False;data['complete']=False
result=None
if (out/'results.json').is_file():
    result=json.loads((out/'results.json').read_text());data['results_sha256']=support.sha(out/'results.json')
data['passed']=observed['passed'] and data.get('candidate_drift') is None and result is not None and result.get('passed') is True and result.get('complete') is True
data['complete']=observed['complete'] and data.get('candidate_drift') is None and result is not None and result.get('complete') is True
data['tests']=result.get('tests') if result is not None else None
meta=records/(name+'.metadata.json');meta.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2),flush=True)
raise SystemExit(0 if data['passed'] and data['complete'] else 1)
