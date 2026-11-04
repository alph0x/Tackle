"""Glued release prose detection and notes-phase refusal."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_release_config import sample

ROOT = Path(__file__).resolve().parents[5]
TOOL = ROOT / 'maintaining/release/verify_release_notes.py'


class ProseTokensTest(unittest.TestCase):
    def test_pairs_and_technical_prose(self):
        spec = importlib.util.spec_from_file_location('prose_tokens', ROOT / 'maintaining/release/prose_tokens.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pairs = [('revision5', 'revision 5', 'letters-digits'),
                 ('card1045', 'card 1045', 'letters-digits'),
                 ('is86', 'is 86', 'letters-digits'),
                 ('abc123', 'abc1234', 'letters-digits'),
                 ('Abc123', 'Abc1234', 'letters-digits'),
                 ('105files', '105 files', 'digits-letters'),
                 ('alternatives,105', 'alternatives, 105', 'punctuation'),
                 ('files;then', 'files; then', 'punctuation')]
        for invalid, valid, rule in pairs:
            with self.subTest(token=invalid):
                self.assertEqual(module.glued_tokens(invalid), [(1, invalid, rule)])
                self.assertEqual(module.glued_tokens(valid), [])
        self.assertEqual(module.glued_tokens('2nd c1e3cb78 1234abc s93 SHA256 sha256 ' + 'T' + '-' + '08' + ' R-REL-29 10.5.1 v10.5.1 3.10.22 py310 sha1 sha512 md5 utf8 base64 python3 py314 arm64 amd64 ipv4 ipv6'), [])
        self.assertEqual(module.glued_tokens('1,000'), [])
        self.assertEqual(module.glued_tokens('`card1045` [notes](https://x.y/a1b) https://github.com/alph0x/Tackle/releases/tag/v10.5.1 <https://x.y/a1b>\n```\nrevision5\n```'), [])
        self.assertEqual(module.glued_tokens('first5\n\nfiles;then 105files'), [(1, 'first5', 'letters-digits'), (3, 'files;then', 'punctuation'), (3, '105files', 'digits-letters')])
        with tempfile.TemporaryDirectory() as tmp:
            loop = Path(tmp) / 'loop'
            loop.symlink_to('loop')
            result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'maintaining/release/prose_tokens.py'), str(loop)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)

    def run_notes(self, notes, report):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / 'candidate'
            repo.mkdir()
            workspace = root / 'workspace'
            workspace.mkdir()
            entry = b'## Tackle 2.3.4\n\n' + notes.encode()
            changelog = root / 'entry.md'
            changelog.write_bytes(entry)
            (repo / 'CHANGELOG.md').write_bytes(b'# Changelog\n\n' + entry + b'\n## Tackle 2.3.3\n\nPrevious.\n')
            report_path = root / 'report.md'
            report_path.write_text(report)
            cfg = sample()
            cfg['workspace'] = str(workspace)
            cfg['changelog'] = {'path': str(changelog), 'sha256': hashlib.sha256(entry).hexdigest()}
            cfg['record']['path'] = str(report_path)
            cfg['record']['sha256'] = hashlib.sha256(report.encode()).hexdigest()
            config_path = root / 'config.json'
            config_path.write_text(json.dumps(cfg))
            fake_bin = root / 'bin'
            fake_bin.mkdir()
            git = fake_bin / 'git'
            git.write_text('#!/bin/sh\ncase "$*" in\n  "rev-parse HEAD") printf "%s\\n" ' + 'a' * 40 + ';;\n  "status --porcelain") exit 0;;\n  *) exit 98;;\nesac\n')
            git.chmod(0o755)
            env = dict(os.environ, PATH=str(fake_bin) + os.pathsep + os.environ.get('PATH', ''))
            out = root / 'records'
            result = subprocess.run([sys.executable, '-I', '-B', str(TOOL), '--config', str(config_path), '--repo', str(repo), '--workspace', str(workspace), '--candidate', 'a' * 40, '--records', str(out), '--version', '2.3.4'], capture_output=True, text=True, env=env)
            return result, out.exists(), (out / 'release-notes.md').read_bytes() if out.exists() else None, json.loads((out / 'results.json').read_text()) if out.exists() else None

    def test_refusal_before_writes(self):
        for notes, report, expected in [('revision5\n', 'Clean report.\n', 'notes:1 revision5'), ('Clean notes.\n', 'alternatives,105\n', 'report:1 alternatives,105')]:
            with self.subTest(expected=expected):
                result, exists, _, _ = self.run_notes(notes, report)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('glued tokens in release prose: ', result.stderr)
                self.assertIn(expected, result.stderr)
                self.assertFalse(exists)

    def test_clean_prose_preserves_body(self):
        body = 'revision 5\n'
        result, exists, written, data = self.run_notes(body, 'alternatives, 105\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(exists)
        self.assertEqual(written, body.encode())
        self.assertEqual(data['glued_tokens'], 0)


if __name__ == '__main__':
    unittest.main()
