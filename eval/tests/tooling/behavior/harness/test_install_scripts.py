"""The method arm's install tree: SKILL.md, references/ and, when present, scripts/.

Guarantee: an install that ships scripts/ is read, digested and staged with them, so a method arm holds every
program the skill ships; an install without scripts/ keeps the digest the earlier function produced, so sealed
cohorts of earlier releases stay checkable; a symlinked scripts/ refuses. No model, network or host is involved.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'eval/behavior/harness'))
import harness  # noqa: E402
import subscription_route  # noqa: E402

# Digests of the earlier release trees under the function as it stood before scripts/ was read.
V93_DIGEST = 'ce853d6a65c151191b9e7907a8a00cd590a80922b1dc2c9eb46fdae96778bd69'
V91_DIGEST = 'f971da09b66f4675387c208132ca9d7596d9cc774bfc4b72b245bac0e4b7aa9a'


def earlier_digest(root):
    """The install digest as the function computed it before scripts/ was read, rebuilt independently."""
    root = Path(root)
    files = {'SKILL.md': (root / 'SKILL.md').read_bytes()}
    refs = root / 'references'
    if refs.is_dir():
        for path in sorted(refs.rglob('*')):
            if path.is_file():
                files['references/' + path.relative_to(refs).as_posix()] = path.read_bytes()
    entries = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    return harness.mapping_digest(entries)


def archive(tag, into):
    subprocess.run('git -C %s archive %s skills/tackle | tar -x -C %s' % (ROOT, tag, into), shell=True, check=True)
    return Path(into) / 'skills' / 'tackle'


def shaped(root, with_scripts):
    root = Path(root)
    (root / 'references').mkdir(parents=True)
    (root / 'SKILL.md').write_bytes(b'# skill\n')
    (root / 'references' / 'a.md').write_bytes(b'ref\n')
    if with_scripts:
        (root / 'scripts').mkdir()
        (root / 'scripts' / 'tool.py').write_bytes(b'print(1)\n')
    return root


class InstallScripts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_scripts_are_read_and_digested(self):
        root = shaped(self.dir / 'i', True)
        files = harness.read_install(root)
        self.assertEqual(sorted(files), ['SKILL.md', 'references/a.md', 'scripts/tool.py'])
        before = harness.files_digest(files)
        (root / 'scripts' / 'tool.py').write_bytes(b'print(2)\n')
        self.assertNotEqual(before, harness.files_digest(harness.read_install(root)))

    def test_nested_scripts_are_read(self):
        root = shaped(self.dir / 'i', True)
        (root / 'scripts' / 'lib').mkdir()
        (root / 'scripts' / 'lib' / 'x.py').write_bytes(b'x\n')
        self.assertIn('scripts/lib/x.py', harness.read_install(root))

    def test_method_arm_stages_every_returned_file(self):
        root = shaped(self.dir / 'i', True)
        files = harness.read_install(root)
        digest = harness.files_digest(files)
        home = self.dir / 'home'
        subscription_route.stage_skill(home, files, digest)
        skill = home / '.claude' / 'skills' / 'tackle'
        self.assertEqual(sorted(p.relative_to(skill).as_posix() for p in skill.rglob('*') if p.is_file()),
                         sorted(files))
        self.assertEqual((skill / 'scripts' / 'tool.py').read_bytes(), b'print(1)\n')

    def test_staging_refuses_when_a_script_is_missing_from_the_copy(self):
        root = shaped(self.dir / 'i', True)
        files = harness.read_install(root)
        digest = harness.files_digest(files)
        partial = {k: v for k, v in files.items() if not k.startswith('scripts/')}
        with self.assertRaises(harness.Refusal):
            subscription_route.stage_skill(self.dir / 'home', partial, digest)

    def test_install_without_scripts_keeps_the_earlier_digest(self):
        root = shaped(self.dir / 'i', False)
        self.assertEqual(harness.files_digest(harness.read_install(root)), earlier_digest(root))

    def test_release_trees_keep_their_digests(self):
        for tag, pinned in (('v9.3.0', V93_DIGEST), ('v9.1.0', V91_DIGEST)):
            with self.subTest(tag=tag):
                root = archive(tag, tempfile.mkdtemp(dir=self.dir))
                self.assertFalse((root / 'scripts').exists())
                digest = harness.files_digest(harness.read_install(root))
                self.assertEqual(digest, earlier_digest(root))
                self.assertEqual(digest, pinned)

    def test_candidate_tree_stages_its_scripts(self):
        root = archive('a5f4341', tempfile.mkdtemp(dir=self.dir))
        files = harness.read_install(root)
        shipped = sorted(p.relative_to(root).as_posix() for p in (root / 'scripts').rglob('*') if p.is_file())
        self.assertTrue(shipped)
        self.assertEqual(sorted(k for k in files if k.startswith('scripts/')), shipped)
        self.assertNotEqual(harness.files_digest(files), earlier_digest(root))

    def test_symlinked_scripts_directory_refuses(self):
        root = shaped(self.dir / 'i', False)
        target = self.dir / 'elsewhere'
        target.mkdir()
        (target / 'tool.py').write_bytes(b'x\n')
        (root / 'scripts').symlink_to(target)
        with self.assertRaises(harness.Refusal):
            harness.read_install(root)

    def test_symlinked_file_inside_scripts_refuses(self):
        root = shaped(self.dir / 'i', True)
        (root / 'scripts' / 'link.py').symlink_to(root / 'SKILL.md')
        with self.assertRaises(harness.Refusal):
            harness.read_install(root)


if __name__ == '__main__':
    unittest.main()
