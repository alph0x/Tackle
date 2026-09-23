"""Packaging checks only; behavioral decisions require the fresh-agent trials."""
from pathlib import Path
import json
import re
import runpy
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HARNESS = runpy.run_path(str(Path(__file__).with_name('behavioral.py')))


class PackagingTests(unittest.TestCase):
    def test_case_ids_reject_traversal_and_duplicates(self):
        safe_ids = HARNESS['safe_ids']
        self.assertEqual(safe_ids([{'id': 'safe-1'}]), ['safe-1'])
        for value in ('../outside', 'nested/case', '.', '', 'Upper'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_ids([{'id': value}])
        with self.assertRaises(ValueError):
            safe_ids([{'id': 'same'}, {'id': 'same'}])
        with tempfile.TemporaryDirectory() as directory:
            reserved = Path(directory) / 'bad,name'
            reserved.write_text('test')
            with self.assertRaisesRegex(ValueError, 'reserved separator'):
                HARNESS['docker_mount'](reserved, '/fixture')

    def test_manifest_rejects_changed_and_redirected_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            case = source / 'safe'
            case.mkdir()
            (case / 'TASK.md').write_text('safe')
            inputs = HARNESS['hashes'](case)
            (source / 'manifest.json').write_text(json.dumps([{'id': 'safe', 'inputs': inputs}]))
            self.assertEqual(len(HARNESS['checked_manifest'](source)), 1)
            (case / 'TASK.md').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'changed'):
                HARNESS['checked_manifest'](source)
            (case / 'TASK.md').unlink()
            (case / 'TASK.md').symlink_to(source / 'manifest.json')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                HARNESS['checked_manifest'](source)

    def test_manifest_rejects_escaping_case_before_reading_it(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / 'manifest.json').write_text(json.dumps([{'id': '../outside', 'inputs': {}}]))
            with self.assertRaisesRegex(ValueError, 'safe path'):
                HARNESS['checked_manifest'](source)

    def test_requires_explicit_dedicated_credential(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            primary = home / '.codex/auth.json'
            primary.parent.mkdir()
            primary.write_text('test only')
            alternate = home / 'test-auth.json'
            alternate.write_text('test only')
            with patch.object(Path, 'home', return_value=home):
                with self.assertRaisesRegex(ValueError, 'dedicated test'):
                    HARNESS['dedicated_auth'](primary)
                self.assertEqual(HARNESS['dedicated_auth'](alternate), alternate.resolve())
            case = home / 'case'
            case.mkdir()
            (case / 'SKILL.md').write_text('test')
            (home / 'results').mkdir()
            with patch.object(subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=b'', stderr=b'')) as launched:
                HARNESS['run_case'](home, {'id': 'case'}, home / 'results', 'test-model', 'low', alternate)
            command = launched.call_args_list[1].args[0]
            self.assertEqual(command[command.index('--sandbox') + 1], 'workspace-write')
            self.assertNotIn('danger-full-access', command)
            self.assertIn(f'type=bind,src={alternate.resolve()},dst=/root/.codex/auth.json,readonly', command)

    def test_one_installed_entry(self):
        skill = (ROOT / 'SKILL.md').read_text()
        self.assertRegex(skill, r'(?m)^name: tackle$')
        self.assertLessEqual(len(skill.split()), 1100)
        self.assertFalse(list((ROOT / 'references').rglob('SKILL.md')))

    def test_invocation_links_resolve(self):
        path = ROOT / 'references/guides/invocation.md'
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            self.assertTrue((path.parent / target).is_file(), target)

    def test_active_request_tables_do_not_advertise_legacy_commands(self):
        for name in ('SKILL.md', 'README.md', 'references/guides/invocation.md'):
            rows = [line for line in (ROOT / name).read_text().splitlines() if line.startswith('|')]
            self.assertFalse(any('/tackle-' in line for line in rows), name)

    def test_trial_ids_are_unique(self):
        cases = json.loads(Path(__file__).with_name('cases.json').read_text())
        self.assertEqual(len(cases), len({case['id'] for case in cases}))
        self.assertTrue(all(set(case) == {'id', 'request', 'expected'} for case in cases))


if __name__ == '__main__':
    unittest.main()
