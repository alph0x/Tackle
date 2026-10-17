"""Script manifest and install shape: the shipped install is ``SKILL.md``, ``references/`` and
``scripts/``; gate 9 keeps ``scripts/README.md`` current with every ``*.py`` under ``scripts/``, and
gate 6 holds the update guide's copy path to all three.

Every planted defect lives in a disposable temporary copy, never in this repository. Standard
library only; no network, container or model call.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)
SCRIPTS = 'skills/tackle/scripts'
UPDATE = 'skills/tackle/references/guides/update.md'


def gates():
    """The self-lint gate commands, extracted as ``canonical_gates`` extracts them."""
    text = (ROOT / 'MAINTAINING.md').read_text(encoding='utf-8')
    section = re.split(r'\n#{1,6} ', text.split('### Skill self-lint gates\n', 1)[1], maxsplit=1)[0]
    return [command.strip() for _, command in re.findall(r'^   (`+)(.+?)\1$', section, re.M)]


def run_gate(command, root):
    result = subprocess.run(['/bin/sh', '-c', command], cwd=root, capture_output=True, text=True)
    return result.returncode, [line for line in result.stdout.splitlines() if line.strip()], result.stderr


class InstallShapeTests(unittest.TestCase):
    """Case: install shape -- the install folder, the update guide's copy path and gate 6 agree."""

    def test_the_install_holds_exactly_skill_references_and_scripts(self):
        names = sorted(path.name for path in INSTALL.iterdir() if path.name != '__pycache__')
        self.assertEqual(names, ['SKILL.md', 'references', 'scripts'])

    def test_the_copy_path_names_all_three(self):
        lines = [line for line in (ROOT / UPDATE).read_text(encoding='utf-8').split('\n')
                 if line.startswith('3. The owner-controlled installer')]
        self.assertEqual(len(lines), 1)
        for name in ('`SKILL.md`', '`references/`', '`scripts/`'):
            self.assertIn(name, lines[0])

    def test_gate_6_reports_a_copy_path_without_scripts(self):
        command = gates()[5]
        with tempfile.TemporaryDirectory(prefix='tackle-install-shape-') as scratch:
            target = Path(scratch) / UPDATE
            target.parent.mkdir(parents=True)
            text = (ROOT / UPDATE).read_text(encoding='utf-8')
            target.write_text(text, encoding='utf-8')
            self.assertEqual(run_gate(command, scratch)[:2], (0, []))
            narrowed = text.replace('copy only `SKILL.md`, `references/` and `scripts/`',
                                    'copy only `SKILL.md` and `references/`')
            self.assertNotEqual(narrowed, text)
            target.write_text(narrowed, encoding='utf-8')
            code, lines, _ = run_gate(command, scratch)
            self.assertEqual(code, 0)
            self.assertEqual(lines, ['update.md install copy path missing install artifact'])


class ScriptManifestTests(unittest.TestCase):
    """Case: script manifest -- gate 9 is silent on this repository and, on a temporary copy, echoes
    exactly one line naming the script for each drifted, missing, stale or duplicated row."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='tackle-script-manifest-')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        shutil.copytree(ROOT / SCRIPTS, self.root / SCRIPTS, ignore=shutil.ignore_patterns('__pycache__'))
        self.command = [command for command in gates() if SCRIPTS in command]
        self.assertEqual(len(self.command), 1, 'no single gate checks the script manifest')

    def findings(self, root=None):
        code, lines, stderr = run_gate(self.command[0], root or self.root)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(stderr, '')
        return lines

    def script(self, rel):
        return self.root / SCRIPTS / rel

    def manifest(self):
        return (self.root / SCRIPTS / 'README.md').read_text(encoding='utf-8').split('\n')

    def write_manifest(self, lines):
        (self.root / SCRIPTS / 'README.md').write_text('\n'.join(lines), encoding='utf-8')

    def listed(self):
        return [match.group(1) for line in self.manifest()
                for match in [re.match(r'^\| \[([^]]+)\]\(\1\) \|', line)] if match]

    def assert_one_finding(self, kind, name):
        lines = self.findings()
        self.assertEqual(len(lines), 1, lines)
        self.assertEqual(lines[0], 'script manifest: %s %s' % (kind, name))

    def test_the_repository_and_its_copy_are_silent(self):
        self.assertEqual(self.findings(root=ROOT), [])
        self.assertEqual(self.findings(), [])

    def test_every_script_is_listed_with_its_sha256(self):
        rows = self.manifest()
        for path in sorted((ROOT / SCRIPTS).rglob('*.py')):
            rel = path.relative_to(ROOT / SCRIPTS).as_posix()
            matching = [line for line in rows if line.startswith('| [%s](%s) |' % (rel, rel))]
            self.assertEqual(len(matching), 1, rel)
            self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(), matching[0])
        self.assertIn('\n## Consent\n', '\n'.join(rows))

    def test_a_drifted_script_is_named(self):
        name = self.listed()[0]
        path = self.script(name)
        path.write_bytes(path.read_bytes() + b'\n')
        self.assert_one_finding('hash mismatch', name)

    def test_a_missing_row_is_named(self):
        name = self.listed()[-1]
        self.write_manifest([line for line in self.manifest() if not line.startswith('| [%s](' % name)])
        self.assert_one_finding('missing row', name)

    def test_an_unlisted_nested_script_is_named(self):
        self.script('nested').mkdir()
        self.script('nested/extra.py').write_text('VALUE = 1\n', encoding='utf-8')
        self.assert_one_finding('missing row', 'nested/extra.py')

    def test_a_stale_row_is_named(self):
        name = self.listed()[0]
        self.script(name).unlink()
        self.assert_one_finding('stale row', name)

    def test_a_duplicate_row_is_named(self):
        name = self.listed()[0]
        lines = self.manifest()
        row = [line for line in lines if line.startswith('| [%s](' % name)][0]
        self.write_manifest(lines + [row])
        self.assert_one_finding('duplicate row', name)

    def test_one_line_per_problem(self):
        first, last = self.listed()[0], self.listed()[-1]
        path = self.script(first)
        path.write_bytes(path.read_bytes() + b'\n')
        self.write_manifest([line for line in self.manifest() if not line.startswith('| [%s](' % last)])
        self.assertEqual(sorted(self.findings()), sorted(['script manifest: hash mismatch %s' % first,
                                                          'script manifest: missing row %s' % last]))


if __name__ == '__main__':
    unittest.main()
