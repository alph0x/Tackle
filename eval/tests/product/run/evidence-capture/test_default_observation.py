import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest


RECIPE = (Path(__file__).resolve().parents[5] / 'skills/tackle/scripts/evidence_capture.py').read_text()
DEFAULT = ['python3', '-m', 'unittest', 'discover', '-v']
PASS = "import unittest\nclass Sample(unittest.TestCase):\n def test_pass(self): pass\n"


class DefaultObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'wrapper.json'
        executable = shlex.quote(sys.executable)
        log = shlex.quote(str(self.log))
        wrapper = self.bin / 'python3'
        wrapper.write_text('#!/bin/sh\n' + executable + ' -I -c '
                           + shlex.quote('import json,sys; open(sys.argv[1], "w").write(json.dumps({"args": sys.argv[2:], "version": sys.version}))')
                           + ' ' + log + ' "$@"\nexec ' + executable + ' "$@"\n')
        wrapper.chmod(0o755)
        for name in ('module.py', 'test_module.py', 'SPEC.md'):
            (self.root / name).write_text('')

    def observe(self, *, recipe=RECIPE, env=None):
        script = self.root / 'recipe.py'
        script.write_text(recipe)
        child_env = os.environ.copy()
        child_env['PATH'] = str(self.bin) + os.pathsep + child_env.get('PATH', '')
        child_env.update(env or {})
        result = subprocess.run([sys.executable, '-I', str(script), str(self.workspace)],
                                cwd=self.root, env=child_env, capture_output=True, timeout=20)
        out = next((self.workspace / 'evidence').glob('validation-*'))
        record = json.loads((out / 'result.json').read_text())
        receipt = (out / 'receipt.md').read_text()
        payload = receipt.split('```json\n', 1)[1].split('\n```', 1)[0]
        self.assertEqual(json.loads(payload), record)
        return result, record

    def passing(self):
        (self.root / 'test_pass.py').write_text(PASS)

    def test_empty_suite(self):
        result, record = self.observe()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])

    def test_passing_suite(self):
        self.passing()
        result, record = self.observe()
        self.assertEqual(result.returncode, 0)
        self.assertTrue(record['accepted'])

    def test_mixed_suite(self):
        for name in ('a', 'z'):
            (self.root / ('test_' + name + '.py')).write_text(
                'import unittest\nfrom pathlib import Path\nclass Sample(unittest.TestCase):\n'
                + ' def test_pass(self): Path(' + repr(name) + ').write_text("seen")\n')
        (self.root / 'test_fail.py').write_text(
            'import unittest\nclass Sample(unittest.TestCase):\n def test_fail(self): self.fail()\n')
        result, record = self.observe()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])
        self.assertTrue((self.root / 'a').is_file())
        self.assertTrue((self.root / 'z').is_file())

    def test_printed_summary_spoofing(self):
        (self.root / 'test_module.py').write_text('print("Ran 3 tests\\nOK")\n')
        result, record = self.observe()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])

    def test_input_changed(self):
        (self.root / 'test_change.py').write_text(
            'import unittest\nfrom pathlib import Path\nclass Sample(unittest.TestCase):\n'
            ' def test_change(self): Path("module.py").write_text("changed")\n')
        result, record = self.observe()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])
        self.assertFalse(record['inputs_stable'])

    def test_artifact_missing(self):
        self.passing()
        result, record = self.observe(recipe=RECIPE.replace('artifacts = []', 'artifacts = ["missing"]'))
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])
        self.assertFalse(record['artifacts_present'])

    def test_timeout(self):
        (self.root / 'test_sleep.py').write_text(
            'import unittest, time\nclass Sample(unittest.TestCase):\n def test_sleep(self): time.sleep(10)\n')
        result, record = self.observe(recipe=RECIPE.replace('timeout_seconds = 30', 'timeout_seconds = 2'))
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])
        self.assertTrue(record['timeout'])

    def test_hostile_startup(self):
        self.passing()
        hostile = self.root / 'hostile'
        hostile.mkdir()
        marker = self.root / 'marker'
        (hostile / 'sitecustomize.py').write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("seen")\n')
        result, record = self.observe(env={'PYTHONPATH': str(hostile)})
        self.assertEqual(result.returncode, 0)
        self.assertTrue(record['accepted'])
        self.assertFalse(marker.exists())

    def test_honest_receipt(self):
        self.passing()
        result, record = self.observe()
        log = json.loads(self.log.read_text())
        self.assertEqual(result.returncode, 0)
        self.assertTrue(record['accepted'])
        self.assertEqual(record['argv'][0], 'python3')
        self.assertEqual(record['argv'][1:], log['args'])
        self.assertIn('-I', record['argv'])
        self.assertEqual(record['configured_argv'], DEFAULT)

    def test_child_runtime(self):
        self.passing()
        result, record = self.observe()
        self.assertEqual(result.returncode, 0)
        self.assertTrue(record['accepted'])
        self.assertEqual(json.loads(self.log.read_text())['version'], sys.version)

    def test_custom_command_unchanged(self):
        (self.root / 'child.py').write_text('pass\n')
        configured = [sys.executable, 'child.py']
        recipe = RECIPE.replace('argv = ["python3", "-m", "unittest", "discover", "-v"]', 'argv = ' + repr(configured))
        result, record = self.observe(recipe=recipe)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(record['accepted'])
        self.assertEqual(record['argv'], configured)
        self.assertNotIn('configured_argv', record)

    def test_configuration_lines(self):
        for line in ('argv = ["python3", "-m", "unittest", "discover", "-v"]',
                     'inputs = ["module.py", "test_module.py", "SPEC.md"]',
                     'artifacts = []', 'timeout_seconds = 30'):
            self.assertEqual(RECIPE.count(line), 1)

    def snapshot_tree(self):
        snapshot = {}
        for path in [self.root, *sorted(self.root.rglob('*'))]:
            stat = path.lstat()
            snapshot[str(path.relative_to(self.root))] = (
                stat.st_mode, stat.st_size, stat.st_mtime_ns,
                path.read_bytes() if path.is_file() else None,
            )
        return snapshot

    def test_external_workspace_refuses_before_effects(self):
        cwd = self.root / 'cwd'
        cwd.mkdir()
        external = self.root / 'external'
        external.mkdir()
        (external / 'sentinel').write_text('keep')
        for name in ('module.py', 'test_module.py', 'SPEC.md'):
            (cwd / name).write_text('')
        auditor = r'''
import json, os, runpy, sys
script, workspace = sys.argv[1:]
sys.argv = [script, workspace]
events = []
mutations = {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.replace',
             'os.link', 'os.symlink', 'os.chmod', 'os.chown', 'os.truncate'}
def audit(event, args):
    if event == 'open':
        mode, flags = args[1:3]
        if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            events.append([event, str(args[0]), str(mode), flags])
    elif event in mutations or event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.spawn'):
        events.append([event, *[str(a) for a in args]])
sys.addaudithook(audit)
try:
    runpy.run_path(script, run_name='__main__')
finally:
    print('BOUNDARY_EVENTS=' + json.dumps(events), file=sys.stderr)
'''
        script = Path(__file__).resolve().parents[5] / 'skills/tackle/scripts/evidence_capture.py'
        env = os.environ.copy()
        env['PATH'] = str(self.bin) + os.pathsep + env.get('PATH', '')
        before = self.snapshot_tree()
        refused = subprocess.run(
            [sys.executable, '-I', '-B', '-c', auditor, str(script), str(external)],
            cwd=cwd, env=env, capture_output=True, timeout=20,
        )
        self.assertEqual(refused.returncode, 1, refused.stderr)
        self.assertNotIn(b'Traceback', refused.stderr)
        self.assertIn(b'workspace', refused.stderr.lower())
        marker = b'BOUNDARY_EVENTS='
        lines = [line for line in refused.stderr.splitlines() if line.startswith(marker)]
        self.assertEqual(len(lines), 1, refused.stderr)
        self.assertEqual(json.loads(lines[0][len(marker):]), [])
        self.assertEqual(self.snapshot_tree(), before)
        self.assertFalse(self.log.exists())

        self.passing()
        accepted, record = self.observe()
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertTrue(record['accepted'])
        self.assertEqual(record['child_exit'], 0)

    def test_usage_import_is_inert_and_cli_records_usage(self):
        scripts = Path(__file__).resolve().parents[5] / 'skills/tackle/scripts'
        ledger = self.workspace / 'resource-usage.md'
        ledger.write_text('Schema: tackle-observability/2\n')
        trace = self.root / 'events.jsonl'
        trace.write_text('\n'.join(json.dumps(event) for event in [
            {'type': 'thread.started', 'thread_id': 'cli-thread'},
            {'type': 'turn.completed', 'usage': {'input_tokens': 12, 'output_tokens': 3}},
        ]) + '\n')
        env = os.environ.copy()
        env.pop('CODEX_THREAD_ID', None)
        code = r'''
import importlib.util, os, sys
p, w, t = sys.argv[1:]
sys.argv = [p, w, t]
mutations = {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.replace',
             'os.link', 'os.symlink', 'os.chmod', 'os.chown', 'os.truncate'}
def audit(event, args):
    if event == 'open':
        path, mode, flags = args[:3]
        if isinstance(path, (str, bytes, os.PathLike)):
            path = os.path.abspath(os.fsdecode(path))
            if path == t or path == w or path.startswith(w + os.sep):
                raise PermissionError('import touched fixture')
        if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            raise PermissionError('import wrote a file')
    elif event in mutations or event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.spawn'):
        raise PermissionError('import caused an effect')
sys.addaudithook(audit)
spec = importlib.util.spec_from_file_location('subject', p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
'''
        before = self.snapshot_tree()
        imported = subprocess.run(
            [sys.executable, '-I', '-B', '-c', code, str(scripts / 'codex_usage.py'),
             str(self.workspace), str(trace)],
            cwd=self.root, env=env, capture_output=True, timeout=20,
        )
        self.assertEqual((imported.returncode, imported.stdout, imported.stderr), (0, b'', b''))
        self.assertEqual(self.snapshot_tree(), before)
        cli = subprocess.run(
            [sys.executable, '-I', '-B', str(scripts / 'codex_usage.py'),
             str(self.workspace), str(trace)],
            cwd=self.root, env=env, capture_output=True, timeout=20,
        )
        self.assertEqual(cli.returncode, 0, cli.stderr)
        records = [json.loads(line) for line in
                   (self.workspace / 'resource-usage.telemetry.jsonl').read_text().splitlines()]
        self.assertEqual(records[0]['metrics']['input_tokens'], 12)

    def test_retro_help_does_not_read_named_file_and_valid_profile_works(self):
        script = Path(__file__).resolve().parents[5] / 'skills/tackle/scripts/retro_confidence.py'
        sentinel = self.root / '--help'
        sentinel.write_text('sentinel\n')
        before = sentinel.stat()
        args = [sys.executable, '-I', '-B', str(script)]
        help_result = subprocess.run(args + ['--help'], cwd=self.root,
                                     capture_output=True, timeout=20)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn(b'usage', help_result.stdout.lower())
        audit = r'''
import os, runpy, sys
p = sys.argv[1]
sys.argv = [p, '--help']
sentinel = os.path.abspath('--help')
def check(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        if os.path.abspath(os.fsdecode(args[0])) == sentinel:
            raise PermissionError('help sentinel read')
sys.addaudithook(check)
runpy.run_path(p, run_name='__main__')
'''
        audited = subprocess.run([sys.executable, '-I', '-B', '-c', audit, str(script)],
                                 cwd=self.root, capture_output=True, timeout=20)
        self.assertEqual(audited.returncode, 0, audited.stderr)
        self.assertIn(b'usage', audited.stdout.lower())
        after = sentinel.stat()
        self.assertEqual((after.st_mode, after.st_size, after.st_mtime_ns),
                         (before.st_mode, before.st_size, before.st_mtime_ns))
        self.assertEqual(sentinel.read_bytes(), b'sentinel\n')
        profile = self.root / 'profile.md'
        profile.write_text('## Hypotheses\n\n- id: HX · fixture · confidence: x · '
                           'observations: a:✓@2026-01-01 · status: active\n')
        valid = subprocess.run(args + [str(profile)], cwd=self.root,
                               capture_output=True, timeout=20)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertIn(b'HX 1 0 1', valid.stdout)


if __name__ == '__main__':
    unittest.main()
