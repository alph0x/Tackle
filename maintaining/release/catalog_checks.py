"""Read-only canonical release checks, bound to an explicit committed candidate."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path

import importlib.util
_support_spec=importlib.util.spec_from_file_location('release_support',Path(__file__).with_name('release_support.py'))
support=importlib.util.module_from_spec(_support_spec);_support_spec.loader.exec_module(support)
parser=argparse.ArgumentParser()
parser.add_argument('--config',required=True)
for name in ('repo','workspace','candidate','records','version','interpreter'):parser.add_argument('--'+name,required=True)
args=parser.parse_args();
_config_spec=importlib.util.spec_from_file_location('release_config',Path(__file__).with_name('config.py'));config=importlib.util.module_from_spec(_config_spec);_config_spec.loader.exec_module(config);cfg=config.load(args.config)
if args.version != cfg['version'] or Path(args.workspace).resolve() != Path(cfg['workspace']).resolve():raise SystemExit('configuration version or workspace mismatch')
if Path(args.interpreter).resolve() != Path(cfg['runtimes']['py310']['path']).resolve() or not config.runtime_ok(cfg,'py310',support.probe(args.interpreter)['version']):raise SystemExit('runtime mismatch')
root=Path(args.repo).resolve(strict=True);workspace=Path(args.workspace).resolve(strict=True);out=Path(args.records).resolve()
import re
stamp_match=re.search(r'^\*\*Tackle ([0-9]+[.][0-9]+[.][0-9]+)\*\*',(root/'skills/tackle/SKILL.md').read_text(),re.M)
if stamp_match is None or stamp_match[1]!=args.version:raise SystemExit('candidate methodology/version argument mismatch')
if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!=args.candidate:raise SystemExit('candidate HEAD mismatch')
if subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True):raise SystemExit('candidate must be clean')
out.mkdir(parents=True,exist_ok=False);binding=out/'runtime-bin';binding.mkdir();(binding/'python3').symlink_to(Path(args.interpreter).resolve(strict=True))
env=dict(os.environ);env['PATH']=str(binding)+os.pathsep+env.get('PATH','')
def run(name,argv,silent=False):
    return support.capture(name,argv,root,out,env=env,timeout=600,silent=silent)

checks=[run('scenario-index',[args.interpreter,'-I','-B','eval/scenario-index/check_index.py','--repo','.']),run('record-currency',[args.interpreter,'-I','-B','eval/records/check_currency.py','--repo','.'])]
report={'candidate':args.candidate,'checks':checks,'passed':all(check['passed'] for check in checks)}
try:support.require_candidate(root,args.candidate)
except ValueError as error:report['candidate_drift']=str(error);report['passed']=False
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
