"""Read-only per-row lint sweep for the 10.3.0 release, preserving native results and explicit release scope.

Discovery goes through the installed archive helper's `list_workspaces(..., state="active")` (MAINTAINING, Release
sweep: not a raw docs/plans glob, so the reserved archive store is not an active workspace and unfamiliar ordinary
directories stay visible). A slug is embedded in a shell command by the lint program, so it is checked against the
lint script's own SLUG pattern first: a directory that fails it is reported and never reaches a shell. The lint script
that runs is pinned to its digest row in scripts/README.md, so the row 2 sibling-path confinement that the 10.2.0
review found missing is the reviewed code, and every AGENTS.md sibling declaration is scanned and recorded with the
same pattern.

Arguments: --repo --workspace --candidate --records --version
  Discovery is rooted at the explicit workspace repository; no fixed slug defaults.
Writes <records dir>/workspace-sweep/<slug>/NN.stdout|NN.stderr per row, results.json per workspace and overall;
exit 1 when a gating workspace fails a mandatory row, 2 when the sweep itself cannot run.
"""
import concurrent.futures
import hashlib
import importlib.util
import json
from pathlib import Path

import importlib.util
_support_spec=importlib.util.spec_from_file_location('release_support',Path(__file__).with_name('release_support.py'))
support=importlib.util.module_from_spec(_support_spec);_support_spec.loader.exec_module(support)
import re
import runpy
import subprocess
import sys


import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--config',required=True)
for name in ('repo','workspace','candidate','records','version'):parser.add_argument('--'+name,required=True)

args=parser.parse_args()

_config_spec=importlib.util.spec_from_file_location('release_config',Path(__file__).with_name('config.py'));config=importlib.util.module_from_spec(_config_spec);_config_spec.loader.exec_module(config);cfg=config.load(args.config)
if args.version != cfg['version'] or Path(args.workspace).resolve() != Path(cfg['workspace']).resolve():raise SystemExit('configuration version or workspace mismatch')
root=Path(args.repo).resolve(strict=True);workspace=Path(args.workspace).resolve(strict=True)
import re
stamp_match=re.search(r'^\*\*Tackle ([0-9]+[.][0-9]+[.][0-9]+)\*\*',(root/'skills/tackle/SKILL.md').read_text(),re.M)
if stamp_match is None or stamp_match[1]!=args.version:raise SystemExit('candidate methodology/version argument mismatch')
if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!=args.candidate:raise SystemExit('candidate HEAD mismatch')

MAIN=workspace.parents[2];SELECTED=workspace.name;RELEASE=root;RECORDS=Path(args.records).resolve()
support.require_candidate(RELEASE,args.candidate)
SCRIPT = RELEASE / 'skills/tackle/scripts/lint.py'
HELPER = RELEASE / 'skills/tackle/scripts/workspace_archive.py'
MANIFEST = RELEASE / 'skills/tackle/scripts/README.md'
ROWS = range(1, 20)
WARN_ROWS = (8, 13, 15)
ACTIVE = ('In progress', 'Checking', 'Interrupted', '🟡')
SIBLING = re.compile(r'^[a-z0-9][a-z0-9-]*$')

digest = hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
row = [l for l in MANIFEST.read_text(encoding='utf-8').splitlines() if l.startswith('| [lint.py](lint.py) |')]
if len(row) != 1 or digest not in row[0]:
    raise SystemExit('lint.py does not match its digest row in scripts/README.md; sweep not run')
lint = runpy.run_path(str(SCRIPT))
slug_ok = re.compile(lint['SLUG'].pattern + r'\Z')
spec = importlib.util.spec_from_file_location('tackle_workspace_archive', HELPER)
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)
discovery = archive.list_workspaces(MAIN, state='active')
if discovery['pending']:
    raise SystemExit('archive discovery pending; resolve scoped recovery before the release sweep')
unknown = [d for d in discovery['diagnostics'] if d['code'] != 'unqualified-active-name']
if unknown:
    raise SystemExit('archive discovery is incomplete: %s' % unknown)
paths = sorted(Path(e['path']) for e in discovery['entries'])
if SELECTED not in [p.name for p in paths]:
    raise SystemExit('the selected workspace %s is not an active workspace of this repository' % SELECTED)
for p in paths:
    if p.resolve(strict=True).parent != (MAIN / 'docs/plans').resolve():
        raise SystemExit('discovered path outside docs/plans: %s' % p)
OUT = RECORDS / 'workspace-sweep'
OUT.mkdir(parents=True, exist_ok=False)


def board_active(workspace):
    board = workspace / 'task-board.md'
    if not board.exists():
        board = workspace / 'board.md'
    text = board.read_text() if board.exists() else ''
    column, active = None, False
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if 'Status' in cells:
            column = cells.index('Status')
        elif column is not None and len(cells) > column and cells[column] in ACTIVE:
            active = True
    return active


def siblings(workspace):
    """Every AGENTS.md table row that names a sibling workspace path, with the confinement verdict of row 2's pattern."""
    found = []
    agents = workspace / 'AGENTS.md'
    if not agents.is_file():
        return found
    for line in agents.read_text(errors='replace').splitlines():
        cells = [c.strip().replace('`', '') for c in line.strip().strip('|').split('|')] if line.startswith('|') else []
        if len(cells) >= 2 and cells[1].startswith('docs/plans/'):
            found.append(dict(key=cells[0], path=cells[1],
                              confined=bool(SIBLING.match(cells[0]) and SIBLING.match(cells[1][len('docs/plans/'):]))))
    return found


def run(workspace):
    slug = workspace.name
    record = OUT / slug
    record.mkdir()
    active = board_active(workspace)
    selected = slug == SELECTED
    base = dict(workspace=slug, active=active, selected=selected, gating=active or selected,
                script_sha256=digest, siblings=siblings(workspace))
    if not slug_ok.match(slug):
        data = dict(base, rows=[], skipped='slug fails the lint script SLUG pattern; no command was built',
                    mandatory_pass=not base['gating'])
        (record / 'results.json').write_text(json.dumps(data, indent=2) + '\n')
        print(slug, 'gating' if data['gating'] else 'historical', 'SKIPPED (invalid slug)', flush=True)
        return data
    rows = []
    for number in ROWS:
        command = lint['program'](number, slug)
        observation=support.capture('%02d'%number,[b'/bin/sh',b'-c',command],MAIN,record,timeout=300)
        from types import SimpleNamespace
        result=SimpleNamespace(returncode=observation['exit'],stdout=(record/('%02d.stdout'%number)).read_bytes(),stderr=(record/('%02d.stderr'%number)).read_bytes())
        rows.append(dict(row=number, exit=result.returncode,
                         passed=observation['complete'] and lint['passes'](number, result.returncode, result.stdout, result.stderr),
                         warning=number in WARN_ROWS, command_sha256=hashlib.sha256(command).hexdigest()))
    data = dict(base, rows=rows, mandatory_pass=all(r['passed'] for r in rows if not r['warning']))
    (record / 'results.json').write_text(json.dumps(data, indent=2) + '\n')
    print(slug, 'gating' if data['gating'] else 'historical', 'PASS' if data['mandatory_pass'] else 'FAIL', flush=True)
    return data


results=[run(path) for path in paths]
support.require_candidate(RELEASE,args.candidate)
(OUT / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
gating = [r for r in results if r['gating']]
print('workspaces: %d discovered, %d gating (%s), %d failing mandatory rows among gating'
      % (len(results), len(gating), ', '.join(r['workspace'] for r in gating),
         sum(not r['mandatory_pass'] for r in gating)))
raise SystemExit(int(any(r['gating'] and not r['mandatory_pass'] for r in results)))
