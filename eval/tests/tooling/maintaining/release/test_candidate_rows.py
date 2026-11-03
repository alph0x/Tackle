"""Exercise candidate workspace rows on disposable repositories."""
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / 'maintaining/release/workspace_sweep.py'


class CandidateRows(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(os.path.realpath(self.temp.name))
        self.main = self.root / 'main'
        self.candidate = self.root / 'candidate'
        self.workspace = self.main / 'docs/plans/example'
        self.workspace.mkdir(parents=True)
        self.candidate.mkdir()
        scripts = self.candidate / 'skills/tackle/scripts'
        scripts.mkdir(parents=True)
        for name in ('lint.py', 'workspace_archive.py', 'README.md'):
            shutil.copy2(ROOT / 'skills/tackle/scripts' / name, scripts / name)
        (scripts.parent / 'SKILL.md').write_text('**Tackle 2.3.4**\n')
        (self.candidate / 'citation.txt').write_text('candidate text\n')
        (self.workspace / 'reference.md').write_text('')
        (self.main / 'citation.txt').write_text('main text\n')
        (self.workspace / 'plan.md').write_text('citation.txt:1 — "main text"\n')
        (self.workspace / 'history.md').write_text('history\n')
        (self.workspace / 'resource-usage.md').write_text('usage\n')
        (self.workspace / 'link').symlink_to('history.md')
        secret = self.workspace / ('held' + 'out')
        secret.mkdir()
        (secret / 'hidden').write_text('excluded\n')
        archive = self.main / 'docs/plans/.archive'
        archive.mkdir()
        (archive / 'hidden').write_text('excluded\n')
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@invalid',
                   GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@invalid')
        self.env = env
        self.git('init', '-q')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.head = self.git('rev-parse', 'HEAD')
        config = {'schema': 'tackle-release/1', 'version': '2.3.4', 'from_version': '2.3.3',
                  'base': 'a' * 40, 'branch': 'release', 'catalog_revision': [1, 2],
                  'runtimes': {'py310': {'path': sys.executable, 'version': [3, 10, 0]},
                               'py314': {'path': sys.executable, 'version': [3, 14, 0]}},
                  'workspace': str(self.workspace), 'initiative': 'example',
                  'changelog': {'path': str(self.root / 'changes'), 'sha256': 'a' * 64},
                  'record': {'path': str(self.root / 'record'), 'sha256': 'b' * 64, 'destination': 'eval/records/example.md'},
                  'claims': [], 'parts': [], 'install_count': 1, 'expected_ledger_gate': '',
                  'expected_sweep': '', 'gating_workspaces': ['example']}
        self.config = self.root / 'config.json'
        self.config.write_text(json.dumps(config))

    def git(self, *args):
        return subprocess.check_output(['/usr/bin/git', '-C', str(self.candidate), *args], env=self.env, text=True).strip()

    def sweep(self, mode, name, bootstrap=None, env=None):
        records = self.root / name
        arguments = ['--config', str(self.config), '--repo', str(self.candidate), '--workspace', str(self.workspace),
                     '--candidate', self.head, '--records', str(records), '--version', '2.3.4', '--rows-tree', mode]
        if bootstrap is None:
            command = [sys.executable, '-I', '-B', str(SCRIPT), *arguments]
        else:
            command = [sys.executable, '-I', '-B', '-c', bootstrap, str(SCRIPT), *arguments]
        result = subprocess.run(command, cwd=self.root, env=dict(self.env, **(env or {})), capture_output=True, text=True)
        return result, records

    def test_candidate_and_main_discriminate_citation(self):
        before = self.git('status', '--porcelain', '--ignored')
        main, main_records = self.sweep('main', 'main-records')
        candidate, candidate_records = self.sweep('candidate', 'candidate-records')
        self.assertIn(main.returncode, (0, 1), main.stderr)
        self.assertIn(candidate.returncode, (0, 1), candidate.stderr)
        main_row = json.loads((main_records / 'workspace-sweep/results.json').read_text())[0]
        candidate_row = json.loads((candidate_records / 'workspace-sweep/results.json').read_text())[0]
        self.assertTrue(main_row['rows'][3]['passed'])
        self.assertFalse(candidate_row['rows'][3]['passed'])
        self.assertEqual(candidate_row['rows_tree'], 'candidate')
        self.assertEqual(candidate_row['candidate'], self.head)
        self.assertEqual(self.git('status', '--porcelain', '--ignored'), before)
        self.assertFalse(list(self.root.glob('tackle-candidate-rows-*')))

    def test_candidate_citation_passes(self):
        (self.workspace / 'plan.md').write_text('citation.txt:1 — "candidate text"\n')
        result, records = self.sweep('candidate', 'matching-records')
        self.assertIn(result.returncode, (0, 1), result.stderr)
        row = json.loads((records / 'workspace-sweep/results.json').read_text())[0]
        self.assertTrue(row['rows'][3]['passed'])

    def test_candidate_phase_records_facts_and_gating_mismatch(self):
        config = json.loads(self.config.read_text())
        config['gating_workspaces'] = ['absent']
        self.config.write_text(json.dumps(config))
        records = self.root / 'phase-records'
        (records / 'candidate').mkdir(parents=True)
        (records / 'candidate/phase.json').write_text(json.dumps({'ok': True}))
        (records / 'candidate/candidate.json').write_text(json.dumps({'candidate': self.head}))
        result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'maintaining/release/steps.py'),
                                 '--config', str(self.config), '--repo', str(self.candidate),
                                 '--records', str(records), '--phase', 'candidate-rows'],
                                cwd=self.root, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        phase = json.loads((records / 'candidate-rows/phase.json').read_text())
        facts = {item['name']: item for item in phase['results']}
        self.assertEqual(facts['rows judged on the candidate tree']['value'], ['candidate'])
        self.assertTrue(facts['rows judged on the candidate tree']['met'])
        self.assertFalse(facts['gating workspaces']['met'])
        self.assertIn('mandatory rows of gating workspaces', facts)
        child = facts['candidate-rows']['argv']
        self.assertEqual(child[child.index('--rows-tree') + 1], 'candidate')

    def test_relative_interpreter_is_bound_to_caller(self):
        real = self.root / 'runtime'
        real.write_text('#!/bin/sh\nif [ "$3" = "-c" ]; then printf "[3,10,0]\\\\n"; fi\nexit 0\n')
        real.chmod(0o755)
        decoy = self.candidate / 'runtime'
        decoy.write_text('#!/bin/sh\nprintf decoy > "$DECOY_MARKER"\nexit 0\n')
        decoy.chmod(0o755)
        self.git('add', 'runtime')
        self.git('commit', '-qm', 'add decoy')
        self.head = self.git('rev-parse', 'HEAD')
        config = json.loads(self.config.read_text())
        config['runtimes']['py310']['path'] = str(real)
        self.config.write_text(json.dumps(config))
        marker = self.root / 'decoy-marker'
        records = self.root / 'catalog-records'
        result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'maintaining/release/catalog_checks.py'),
                                 '--config', str(self.config), '--repo', str(self.candidate),
                                 '--workspace', str(self.workspace), '--candidate', self.head,
                                 '--records', str(records), '--version', '2.3.4', '--interpreter', 'runtime'],
                                cwd=self.root, env=dict(self.env, DECOY_MARKER=str(marker)), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(marker.exists())
        report = json.loads((records / 'results.json').read_text())
        self.assertEqual(report['checks'][0]['argv'][0], str(real))

    def test_link_failure_precedes_records(self):
        bootstrap = 'import os,runpy,sys; os.link=lambda *a,**k: (_ for _ in ()).throw(OSError("link failure")); sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name="__main__")'
        result, records = self.sweep('candidate', 'failure-records', bootstrap)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('candidate overlay:', result.stderr)
        self.assertFalse((records / 'workspace-sweep').exists())

    def test_interrupt_removes_overlay(self):
        bootstrap = 'import os,runpy,sys; os.link=lambda *a,**k: (_ for _ in ()).throw(KeyboardInterrupt()); sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name="__main__")'
        result, records = self.sweep('candidate', 'interrupt-records', bootstrap, {'TMPDIR': str(self.root)})
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((records / 'workspace-sweep').exists())
        self.assertFalse(list(self.root.glob('tackle-candidate-rows-*')))

    def test_overlay_inside_checkout_refused(self):
        result, records = self.sweep('candidate', 'inside-records', env={'TMPDIR': str(self.candidate)})
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('candidate overlay:', result.stderr)
        self.assertFalse((records / 'workspace-sweep').exists())

    def test_overlay_links_and_exclusions(self):
        observation = self.root / 'overlay.json'
        bootstrap = """
import json, os, pathlib, runpy, shutil, sys
old = shutil.rmtree
def inspect(path, **kw):
    root = pathlib.Path(path)
    workspace = root / 'docs/plans/example'
    original = pathlib.Path(os.environ['SOURCE_WORKSPACE'])
    data = {'linked': (workspace / 'history.md').stat().st_ino == (original / 'history.md').stat().st_ino,
            'symlink': os.readlink(workspace / 'link'),
            'excluded': not (workspace / ('held' + 'out')).exists() and not (root / 'docs/plans/.archive').exists()}
    pathlib.Path(os.environ['OBSERVATION']).write_text(json.dumps(data))
    old(path, **kw)
shutil.rmtree = inspect
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        result, _ = self.sweep('candidate', 'observed-records', bootstrap,
                               {'SOURCE_WORKSPACE': str(self.workspace), 'OBSERVATION': str(observation)})
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertEqual(json.loads(observation.read_text()), {'linked': True, 'symlink': 'history.md', 'excluded': True})

    def test_overlay_reproduces_fifo(self):
        fifo = self.workspace / 'verification-records/RUN-1/pipe'
        fifo.parent.mkdir(parents=True)
        os.mkfifo(fifo)
        os.chmod(fifo, 0o600)
        observation = self.root / 'fifo.json'
        bootstrap = """
import json, os, pathlib, runpy, shutil, stat, sys
old = shutil.rmtree
def inspect(path, **kw):
    copy = pathlib.Path(path) / 'docs/plans/example/verification-records/RUN-1/pipe'
    mode = os.lstat(copy).st_mode
    pathlib.Path(os.environ['OBSERVATION']).write_text(json.dumps({'fifo': stat.S_ISFIFO(mode), 'mode': stat.S_IMODE(mode)}))
    old(path, **kw)
shutil.rmtree = inspect
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        result, records = self.sweep('candidate', 'fifo-records', bootstrap, {'OBSERVATION': str(observation)})
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertEqual(json.loads(observation.read_text()), {'fifo': True, 'mode': 0o600})
        row = json.loads((records / 'workspace-sweep/results.json').read_text())[0]
        self.assertEqual(row['rows_tree'], 'candidate')
        self.assertEqual(len(row['rows']), 19)
        self.assertTrue(stat.S_ISFIFO(os.lstat(fifo).st_mode))

    def test_overlay_refuses_other_special_entries(self):
        here = os.getcwd()
        os.chdir(self.workspace)
        try:
            server = socket.socket(socket.AF_UNIX)
            server.bind('sock')
        finally:
            os.chdir(here)
        self.addCleanup(server.close)
        result, records = self.sweep('candidate', 'socket-records')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('unsupported workspace entry', result.stderr)
        self.assertFalse((records / 'workspace-sweep').exists())
