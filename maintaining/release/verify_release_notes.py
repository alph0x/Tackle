"""Verify the exact heading-bounded changelog entry and retain publication notes."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
spec=importlib.util.spec_from_file_location('support',Path(__file__).with_name('release_support.py'));support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)
parser=argparse.ArgumentParser()
parser.add_argument('--config',required=True)
for name in ('repo','workspace','candidate','records','version'):parser.add_argument('--'+name,required=True)
args=parser.parse_args();
_config_spec=importlib.util.spec_from_file_location('release_config',Path(__file__).with_name('config.py'));config=importlib.util.module_from_spec(_config_spec);_config_spec.loader.exec_module(config);cfg=config.load(args.config)
if args.version != cfg['version'] or Path(args.workspace).resolve() != Path(cfg['workspace']).resolve():raise SystemExit('configuration version or workspace mismatch')
root=support.require_candidate(args.repo,args.candidate);workspace=Path(args.workspace).resolve(strict=True);out=Path(args.records).resolve()
if out.exists():raise SystemExit('notes destination must be fresh')
if out.is_relative_to(root):raise SystemExit('notes destination must be outside candidate checkout')
entry_path=Path(cfg['changelog']['path']);entry=entry_path.read_bytes();
if hashlib.sha256(entry).hexdigest()!=cfg['changelog']['sha256']:raise SystemExit('changelog prose drift')
changelog=(root/'CHANGELOG.md').read_bytes()
heading=('## Tackle '+args.version+'\n').encode()
if not entry.startswith(heading+b'\n') or entry.count(heading)!=1:raise SystemExit('entry heading mismatch')
if changelog.count(heading)!=1:raise SystemExit('changelog heading is not unique')
start=changelog.index(heading)
if start and changelog[start-1:start]!=b'\n':raise SystemExit('version heading must begin a line')
end=changelog.find(b'\n## ',start+len(heading))
if end<0:raise SystemExit('next release heading missing')
section=changelog[start:end+1]
if section!=entry+b'\n':raise SystemExit('heading-bounded changelog entry differs from sealed notes')
body=entry.split(b'\n\n',1)[1]
if section.split(b'\n\n',1)[1][:-1]!=body:raise SystemExit('publication body drift')
support.require_candidate(root,args.candidate)
out.mkdir(parents=True);(out/'release-notes.md').write_bytes(body);(out/'changelog-entry.md').write_bytes(entry)
support.require_candidate(root,args.candidate)
report={'candidate':args.candidate,'version':args.version,'entry_sha256':hashlib.sha256(entry).hexdigest(),'notes_sha256':hashlib.sha256(body).hexdigest(),'heading_boundary_exact':True,'passed':True,'publication':False}
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
