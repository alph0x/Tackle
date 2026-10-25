"""Reserved workspace storage stays outside active reports and release discovery."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid

from test_field_report import FIXTURES, RealRepoFixture, hash_tree

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / 'maintaining/field_report.py'
MODULE = ROOT / 'skills/tackle/scripts/workspace_archive.py'


class ArchiveDiscoveryTests(unittest.TestCase):
    def test_archive_storage_is_not_a_workspace(self):
        # Actual CLI/discovery exclusion, with ordinary hidden and option-shaped controls.
        with tempfile.TemporaryDirectory(prefix='archive-discovery-public-') as temporary:
            lab = Path(temporary)
            try:
                repo = lab / 'repo'
                plans = repo / 'docs/plans'
                plans.mkdir(parents=True)
                for name in ('active', '.ordinary', '--help', '.archive/closed'):
                    shutil.copytree(FIXTURES / 'ws-five', plans / name)
                (plans / 'archive-index.md').write_bytes(b'# Retained archive cards\n')
                (plans / 'archive-alias').symlink_to('.archive', target_is_directory=True)
                (plans / 'closed-alias').symlink_to('.archive/closed', target_is_directory=True)

                def digest(data):
                    return hashlib.sha256(data).hexdigest()

                def inventory(root):
                    result = {}
                    def visit(path, relative):
                        info = path.lstat()
                        mode = stat.S_IMODE(info.st_mode)
                        if stat.S_ISLNK(info.st_mode):
                            result[relative] = ['symlink', mode, os.readlink(path)]
                        elif stat.S_ISDIR(info.st_mode):
                            result[relative] = ['directory', mode, None]
                            for child in sorted(path.iterdir(), key=lambda p: p.name):
                                visit(child, child.name if relative == '.' else relative + '/' + child.name)
                        elif stat.S_ISREG(info.st_mode):
                            result[relative] = ['file', mode, digest(path.read_bytes())]
                        else:
                            raise AssertionError('unexpected fixture object')
                    visit(root, '.')
                    return result

                def run_bytes(label, argv, cwd):
                    capture = lab / 'captures' / (label + '-' + uuid.uuid4().hex)
                    capture.mkdir(parents=True)
                    started = datetime.now(timezone.utc).isoformat()
                    child = None
                    timed_out = False
                    try:
                        with (capture / 'stdout.bin').open('wb') as stdout, (capture / 'stderr.bin').open('wb') as stderr:
                            child = subprocess.Popen(list(map(str, argv)), cwd=cwd, stdout=stdout, stderr=stderr,
                                                     start_new_session=True)
                            try:
                                child.wait(timeout=30)
                            except subprocess.TimeoutExpired:
                                timed_out = True
                                try:
                                    os.killpg(child.pid, signal.SIGTERM)
                                except ProcessLookupError:
                                    pass
                                try:
                                    child.wait(timeout=0.5)
                                except subprocess.TimeoutExpired:
                                    try:
                                        os.killpg(child.pid, signal.SIGKILL)
                                    except ProcessLookupError:
                                        pass
                                    child.wait(timeout=0.5)
                    finally:
                        metadata = {'argv': list(map(str, argv)), 'cwd': str(cwd), 'started': started,
                                    'finished': datetime.now(timezone.utc).isoformat(), 'timeout_seconds': 30,
                                    'python': sys.version, 'executable': sys.executable,
                                    'timed_out': timed_out, 'exit': child.returncode if child else None,
                                    'signal': -child.returncode if child and child.returncode is not None and child.returncode < 0 else None}
                        for stream in ('stdout', 'stderr'):
                            path = capture / (stream + '.bin')
                            metadata[stream + '_sha256'] = digest(path.read_bytes()) if path.exists() else None
                        (capture / 'result.json').write_text(json.dumps(metadata, sort_keys=True) + '\n', encoding='utf-8')
                    self.assertFalse(timed_out, metadata)
                    return metadata, (capture / 'stdout.bin').read_bytes(), (capture / 'stderr.bin').read_bytes()

                before = inventory(plans)
                old_file_hashes = hash_tree(plans)
                expected_active = {'active', '.ordinary', '--help'}
                for plans_arg in (str(plans), str(plans.relative_to(repo))):
                    for selection in (None, '.archive', '.archive/closed', './.archive', 'archive-alias', 'closed-alias', '--help'):
                        with self.subTest(selection=selection, plans_arg=plans_arg):
                            output = lab / ('output-' + uuid.uuid4().hex)
                            json_path, markdown_path = output / 'report.json', output / 'report.md'
                            argv = [sys.executable, '-I', '-B', str(SCRIPT), '--plans', plans_arg,
                                    '--repo', str(RealRepoFixture.path), '--since', RealRepoFixture.since,
                                    '--until', RealRepoFixture.until, '--json', str(json_path), '--markdown', str(markdown_path)]
                            if selection is not None:
                                argv.append('--workspace=' + selection)
                            result, stdout, stderr = run_bytes('field-report', argv, repo)
                            if selection in (None, '--help'):
                                self.assertEqual(result['exit'], 0, (stdout, stderr))
                                report = json.loads(json_path.read_bytes())
                                self.assertEqual(set(report['workspaces']), expected_active if selection is None else {'--help'})
                                self.assertTrue(markdown_path.is_file())
                            else:
                                self.assertNotEqual(result['exit'], 0, (stdout, stderr))
                                self.assertTrue(stdout or stderr, (stdout, stderr))
                                self.assertFalse(json_path.exists())
                                self.assertFalse(markdown_path.exists())
                            self.assertEqual(inventory(plans), before)
                            self.assertEqual(hash_tree(plans), old_file_hashes)

                # Both absent metadata files mean an empty catalog; avoid a fake projection
                # becoming an unrelated metadata-conflict oracle for the actual helper.
                (plans / 'archive-index.md').unlink()
                before = inventory(plans)
                old_file_hashes = hash_tree(plans)
                source = (ROOT / 'MAINTAINING.md').read_text(encoding='utf-8')
                blocks = re.findall(r'^```python workspace-discovery\n(.*?)\n```[ \t]*$', source, re.M | re.S)
                self.assertEqual(len(blocks), 1, 'one actual named workspace-discovery source block is required')
                exact = (blocks[0] + '\n').encode()
                script = lab / 'workspace-discovery.py'
                script.write_bytes(exact)
                # The source block accepts the fixture repo and explicit installed helper path.
                bootstrap = r'''
import os, sys
from pathlib import Path
script = Path(sys.argv[1])
forbidden = os.path.abspath(sys.argv[2])
def guard(event, args):
    if event in ('open', 'os.scandir', 'os.listdir') and args:
        try:
            path = os.path.abspath(os.fsdecode(os.fspath(args[0])))
        except TypeError:
            return
        if path == forbidden or path.startswith(forbidden + os.sep):
            raise AssertionError('real workspace access is outside this fixture')
sys.addaudithook(guard)
sys.argv = [str(script), *sys.argv[3:]]
exec(compile(script.read_bytes(), str(script), 'exec'), {'__name__': '__main__', '__file__': str(script)})
'''
                argv = [sys.executable, '-I', '-B', '-c', bootstrap, str(script), str(ROOT / 'docs/plans'),
                        str(repo), str(MODULE)]
                result, stdout, stderr = run_bytes('release-discovery', argv, repo)
                self.assertEqual(result['exit'], 0, (stdout, stderr))
                observed = stdout.decode('utf-8').splitlines()
                self.assertTrue(all(Path(value).is_absolute() for value in observed))
                self.assertEqual({str(Path(value).resolve(strict=True)) for value in observed},
                                 {str((plans / name).resolve(strict=True)) for name in expected_active})
                self.assertEqual(len(observed), len(expected_active))
                self.assertEqual(inventory(plans), before)
                self.assertEqual(hash_tree(plans), old_file_hashes)
                self.assertEqual(script.read_bytes(), exact)
            finally:
                selected = os.environ.get('TACKLE_ARCHIVE_RECORD_DIR')
                if selected:
                    controller = Path(selected)
                    if controller.is_symlink() or not controller.is_dir():
                        raise ValueError('record controller root must be an existing real directory')
                    controller = controller.resolve(strict=True)
                    if controller == lab or lab in controller.parents:
                        raise ValueError('record controller root overlaps temporary fixture')
                    shutil.copytree(lab, controller / (self._testMethodName + '-' + uuid.uuid4().hex), symlinks=True)


if __name__ == '__main__':
    unittest.main()
