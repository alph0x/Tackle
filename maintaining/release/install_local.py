"""Verify local install channels and retain an inventory of installed files."""
import atexit
import datetime
import json
import os
from pathlib import Path

import importlib.util
_support_spec=importlib.util.spec_from_file_location('release_support',Path(__file__).with_name('release_support.py'))
support=importlib.util.module_from_spec(_support_spec);_support_spec.loader.exec_module(support)
import shutil
import subprocess
import sys
import tempfile


def inventory(root, expected_count):
    """Describe every file under the installed skill root and enforce its count."""
    files = sorted(p for p in root.rglob('*') if p.is_file())
    if len(files) != expected_count:
        raise ValueError('installed artifact has %d files, expected %d' % (len(files), expected_count))
    return {'files': [{'path': p.relative_to(root).as_posix(), 'size': p.stat().st_size,
                       'sha256': support.sha(p)} for p in files]}


def cleanup_sandbox(sandbox):
    """Remove the complete sandbox owned by this install check."""
    shutil.rmtree(sandbox)


def main():
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

    support.require_candidate(root,args.candidate)
    EXPECTED=cfg['install_count']
    out=Path(args.records).resolve()
    if out.exists():raise SystemExit('record destination must be new')
    out.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix='release-install-', dir=out))   # owned sandbox beside the records, not in the system temp dir
    atexit.register(shutil.rmtree, scratch, ignore_errors=True)
    clone = scratch / 'clone'
    subprocess.run(['git', 'clone', '-q', '--no-hardlinks', str(root), str(clone)], check=True)
    want = sorted(p[len('skills/tackle/'):] for p in subprocess.check_output(['git', '-C', str(root), 'ls-tree', '-r', '--name-only', 'HEAD', 'skills/tackle'], text=True).splitlines())
    assert len(want) == EXPECTED, 'the install artifact has %d files, expected %d' % (len(want), EXPECTED)
    manual = scratch / 'manual'
    manual.mkdir()
    for name in ('SKILL.md', 'references', 'scripts'):
        src = clone / 'skills/tackle' / name
        if src.is_dir():
            shutil.copytree(src, manual / name)
        else:
            shutil.copyfile(src, manual / name)


    def listing(path):
        return sorted(str(p.relative_to(path)) for p in path.rglob('*') if p.is_file())


    assert listing(manual) == want
    readme = (root / 'README.md').read_text()
    for sentence in ('with %d installation-relative files' % len(want), 'against the %d expected files' % len(want)):
        assert sentence in readme, 'README does not say %r' % sentence
    for rel in want:
        assert (manual / rel).read_bytes() == (root / 'skills/tackle' / rel).read_bytes(), rel
    agent_config=scratch/'claude-config';agent_config.mkdir();state=scratch/'state';state.mkdir()
    (scratch / 'npm-logs').mkdir()
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(agent_config), XDG_STATE_HOME=str(state), npm_config_cache=str(Path.home() / '.npm'), npm_config_logs_dir=str(scratch / 'npm-logs'),
               DO_NOT_TRACK='1', DISABLE_TELEMETRY='1')
    command = ['npx', '--offline', '--yes', 'skills@1.7.0', 'add', str(clone), '--skill', 'tackle', '-a', 'claude-code', '-y', '-g','--copy']
    observation=support.capture('install-npx',command,scratch,out,env=env,timeout=180)
    from types import SimpleNamespace
    result=SimpleNamespace(returncode=observation['exit'],stdout=(out/'install-npx.stdout').read_bytes(),stderr=(out/'install-npx.stderr').read_bytes())
    data = dict(sandbox=str(scratch), revision=subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
                argv=command, cwd=str(scratch), environment={'CLAUDE_CONFIG_DIR':str(agent_config),'XDG_STATE_HOME':str(state), 'npm_config_cache': str(Path.home() / '.npm'), 'npm_config_logs_dir': str(scratch / 'npm-logs'), 'DO_NOT_TRACK': '1', 'DISABLE_TELEMETRY': '1'},
                expected=want, count=len(want), manual_pass=True, npx_exit=observation["native_exit"],npx_capture=observation)
    if result.returncode == 0:
        installed = agent_config/'skills/tackle'
        data['npx_files'] = listing(installed)
        data['npx_list_pass'] = data['npx_files'] == want
        data['npx_bytes_pass'] = all((installed / rel).read_bytes() == (root / 'skills/tackle' / rel).read_bytes() for rel in want) if data['npx_list_pass'] else False
    support.require_candidate(root,args.candidate)
    (out / 'inventory.json').write_text(json.dumps(inventory(manual, EXPECTED), indent=2) + '\n')
    (out / 'install-results.json').write_text(json.dumps(data, indent=2) + '\n')
    cleanup_sandbox(scratch)
    print('manual: %d files, same list and bytes' % len(want))
    print('README count %d (both sentences)' % len(want))
    print('npx:', result.returncode, data.get('npx_list_pass'), data.get('npx_bytes_pass'))
    print('owned sandbox removed:', scratch)
    raise SystemExit(int(not (result.returncode == 0 and data.get('npx_list_pass') and data.get('npx_bytes_pass'))))


if __name__ == '__main__':
    main()
