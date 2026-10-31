"""Existing strict committed-text consumer over a temporary index, including untracked files."""
from pathlib import Path
import argparse,dataclasses,hashlib,importlib.util,json,os,subprocess,tempfile
parser=argparse.ArgumentParser()
parser.add_argument('--config',required=True)
for name in ('repo','candidate','base','initiative','records'):parser.add_argument('--'+name,required=True)
args=parser.parse_args();
_config_spec=importlib.util.spec_from_file_location('release_config',Path(__file__).with_name('config.py'));config=importlib.util.module_from_spec(_config_spec);_config_spec.loader.exec_module(config);cfg=config.load(args.config)
if args.base != 'v'+cfg['from_version'] or args.initiative != cfg['initiative']:raise SystemExit('configuration base or initiative mismatch')
root=Path(args.repo).resolve(strict=True);out=Path(args.records).resolve();out.mkdir(parents=True,exist_ok=False)
def head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
if head()!=args.candidate:raise SystemExit('candidate drift')
spec=importlib.util.spec_from_file_location('committed_text',root/'eval/rules/committed_text.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
index_name=subprocess.check_output(['git','rev-parse','--git-path','index'],cwd=root,text=True).strip();real_index=Path(index_name)
if not real_index.is_absolute():real_index=root/real_index
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
before_sha=sha(real_index) if real_index.exists() else None
old_index=os.environ.get('GIT_INDEX_FILE');checks=[]
with tempfile.TemporaryDirectory(prefix='tackle-committed-index-',dir=out) as temporary:
    os.environ['GIT_INDEX_FILE']=str(Path(temporary)/'index')
    try:
        for number,argv in enumerate((['git','read-tree','HEAD'],['git','add','-N','--','.'])):
            result=subprocess.run(argv,cwd=root,capture_output=True)
            (out/('index-'+str(number)+'.stdout')).write_bytes(result.stdout);(out/('index-'+str(number)+'.stderr')).write_bytes(result.stderr)
            checks.append({'argv':argv,'cwd':str(root),'exit':result.returncode,'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()})
            if result.returncode:raise SystemExit('temporary index preparation failed')
        findings=module.scan_committed_text(root,args.base,args.initiative)
    finally:
        if old_index is None:os.environ.pop('GIT_INDEX_FILE',None)
        else:os.environ['GIT_INDEX_FILE']=old_index
after_sha=sha(real_index) if real_index.exists() else None
passed=not findings and before_sha==after_sha and head()==args.candidate
report={'passed':passed,'candidate':args.candidate,'base':args.base,'initiative':args.initiative,'temporary_index_includes_untracked':True,'real_index_unchanged':before_sha==after_sha,'guard_sha256':sha(root/'eval/rules/committed_text.py'),'findings':[dataclasses.asdict(item) for item in findings],'checks':checks,'exemptions':[]}
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':passed,'findings':len(findings),'real_index_unchanged':before_sha==after_sha}))
raise SystemExit(0 if passed else 1)
