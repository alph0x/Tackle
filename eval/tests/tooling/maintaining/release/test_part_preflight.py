"""A release part runs the committed-text preflight after applying its edit and before staging it.

Guarantee: `steps.py --phase part` refuses to stage or commit when the committed-text preflight finds a
workspace-shaped identifier added since the previous release, leaving HEAD and the index untouched; a clean
part still commits, with the preflight recorded before the stage.
Concrete fault: a release part stages and commits first and only a later phase inspects committed text.
Consumer: the standing release procedure. Valid alternative: a clean candidate commits exactly as before.
Each case builds a disposable repository; nothing is written inside this repository.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
STEPS = ROOT / 'maintaining/release/steps.py'
README = ('**Tackle 2.3.3** · Model-agnostic\n'
          "npx skills add 'https://github.com/example-org/Tackle.git#v2.3.3' --skill tackle\n"
          'Public routes have not been probed for 2.3.3.\n'
          'The migration catalog targets Tackle 2.3.3 and older plans.\n')


class PartPreflight(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(os.path.realpath(temp.name))
        self.repo = self.root / 'candidate'
        self.workspace = self.root / 'main/docs/plans/relfixture'
        self.workspace.mkdir(parents=True)
        (self.repo / 'eval/rules').mkdir(parents=True)
        shutil.copy2(ROOT / 'eval/rules/committed_text.py', self.repo / 'eval/rules/committed_text.py')
        catalog = self.repo / 'skills/tackle/references/guides/migration-catalog.json'
        catalog.parent.mkdir(parents=True)
        catalog.write_text(json.dumps({'target_methodology': '2.3.4'}) + '\n')
        (self.repo / 'README.md').write_text(README)
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@invalid',
                        GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@invalid')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.git('tag', 'v2.3.3')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], env=self.env, text=True).strip()

    def part(self):
        base = self.git('rev-parse', 'HEAD')
        self.git('switch', '-qc', 'release-2.3.4')
        runtime = {'path': sys.executable, 'version': list(sys.version_info[:3])}
        config = {'schema': 'tackle-release/1', 'version': '2.3.4', 'from_version': '2.3.3', 'base': base,
                  'branch': 'release-2.3.4', 'catalog_revision': [1, 2],
                  'runtimes': {'py310': runtime, 'py314': runtime}, 'workspace': str(self.workspace),
                  'initiative': 'relfixture', 'changelog': {'path': str(self.root / 'entry'), 'sha256': 'a' * 64},
                  'record': {'path': str(self.root / 'record'), 'sha256': 'b' * 64,
                             'destination': 'eval/records/demo.md'},
                  'claims': [], 'parts': ['readme'], 'install_count': 1, 'expected_ledger_gate': '',
                  'expected_sweep': '', 'gating_workspaces': ['relfixture']}
        path = self.root / 'release.json'
        path.write_text(json.dumps(config))
        records = self.root / 'records'
        result = subprocess.run([sys.executable, '-I', '-B', str(STEPS), '--config', str(path), '--repo', str(self.repo),
                                 '--records', str(records), '--phase', 'part', '--part', 'readme'],
                                cwd=self.root, env=self.env, capture_output=True, text=True)
        phase = json.loads((records / 'part-readme/phase.json').read_text())
        return base, result, [item['name'] for item in phase['results']], {item['name']: item for item in phase['results']}

    def test_identifier_added_since_release_blocks_before_staging(self):
        (self.repo / 'notes.md').write_text('Carried over from ' + '-'.join(('T', str(7).zfill(2))) + '.\n')
        self.git('add', 'notes.md')
        self.git('commit', '-qm', 'notes')
        before = self.git('ls-files', '-s')
        base, result, order, facts = self.part()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse(facts['committed-preflight']['met'])
        self.assertNotIn('stage', order)
        self.assertNotIn('commit', order)
        self.assertEqual(self.git('rev-parse', 'HEAD'), base)
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertEqual(self.git('ls-files', '-s'), before)

    def test_clean_part_commits_after_the_preflight(self):
        base, result, order, facts = self.part()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(facts['committed-preflight']['met'])
        self.assertLess(order.index('second'), order.index('committed-preflight'))
        self.assertLess(order.index('committed-preflight'), order.index('stage'))
        self.assertEqual(self.git('rev-parse', 'HEAD^'), base)
        self.assertEqual(self.git('log', '-1', '--format=%s'), 'Point the README at Tackle 2.3.4')
        self.assertEqual(self.git('status', '--porcelain'), '')


if __name__ == '__main__':
    unittest.main()
