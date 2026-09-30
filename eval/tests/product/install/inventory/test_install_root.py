"""Root selection and real-consumer coverage for the repository's packaged skill."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from maintaining.install_root import (InstallRootError, current_root, revision_path,
                                      revision_prefix)


SKILL_TEXT = "# Tackle\n\nThe unchanged logical installation sentence survives its move across root layouts.\n"
REFERENCE_TEXT = "# Retained reference\n\nA retained reference remains part of the shipped logical tree.\n"
DECOY_TEXT = "# Wrong-depth decoy\n\nThis decoy is outside either supported installation root.\n"
LEDGER = {"schema": "tackle-unit-dispositions-fixture/1", "rules": [{"home": "SKILL.md:3", "mirrors": []}], "non_normative": []}
DISPOSITIONS = {"schema": "tackle-unit-dispositions/1", "records": []}
GIT_ENV = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="Install root fixture", GIT_AUTHOR_EMAIL="install-root-fixture@example.invalid",
               GIT_COMMITTER_NAME="Install root fixture", GIT_COMMITTER_EMAIL="install-root-fixture@example.invalid",
               PYTHONDONTWRITEBYTECODE="1")


def _write(root, relative, content):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], cwd=repo, env=GIT_ENV,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError("fixture Git operation failed: %s exit=%d" % (args[0], result.returncode))
    return result.stdout.decode("utf-8").strip()


def build_crossing_repo(parent):
    """Create real old-root and new-root commits plus a decoy outside both candidate roots."""
    repo = Path(parent) / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _write(repo, "SKILL.md", SKILL_TEXT)
    _write(repo, "references/guides/retained.md", REFERENCE_TEXT)
    _write(repo, "wrong-depth/SKILL.md", DECOY_TEXT)
    _write(repo, "eval/rules/ledger.json", json.dumps(LEDGER, sort_keys=True) + "\n")
    _write(repo, "eval/rules/unit-dispositions.json", json.dumps(DISPOSITIONS, sort_keys=True) + "\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "historical root layout")
    base = _git(repo, "rev-parse", "HEAD")
    package = repo / "skills/tackle"
    package.mkdir(parents=True)
    (repo / "SKILL.md").replace(package / "SKILL.md")
    (repo / "references").replace(package / "references")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "nested installation layout")
    current = _git(repo, "rev-parse", "HEAD")
    return repo, base, current


class InstallRootTests(unittest.TestCase):
    def test_current_root_historical_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write(root, "SKILL.md", SKILL_TEXT)
            _write(root, "references/guide.md", REFERENCE_TEXT)
            self.assertEqual(current_root(root), root.resolve())

    def test_current_root_nested_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / "skills/tackle"
            _write(package, "SKILL.md", SKILL_TEXT)
            _write(package, "references/guide.md", REFERENCE_TEXT)
            self.assertEqual(current_root(root), package.resolve())

    def test_revision_prefix_crosses_real_git_relocation(self):
        with tempfile.TemporaryDirectory() as temp:
            repo, base, current = build_crossing_repo(temp)
            self.assertEqual(revision_prefix(repo, base), "")
            self.assertEqual(revision_prefix(repo, current), "skills/tackle/")
            tool = REPO / "eval/rules/check_unit_diff.py"
            result = subprocess.run([sys.executable, "-B", str(tool), "--repo", str(repo), "--base", base],
                                    cwd=repo, env=GIT_ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    timeout=30, check=False)
            error_count = sum(line.startswith(b"error:") for line in result.stdout.splitlines())
            self.assertEqual(result.returncode, 0,
                             "unit-diff child exit=%d error_count=%d" % (result.returncode, error_count))
            self.assertEqual(error_count, 0)

    def test_current_root_rejects_ambiguous_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write(root, "SKILL.md", SKILL_TEXT)
            _write(root, "references/guide.md", REFERENCE_TEXT)
            _write(root, "skills/tackle/SKILL.md", SKILL_TEXT)
            _write(root, "skills/tackle/references/guide.md", REFERENCE_TEXT)
            with self.assertRaises(InstallRootError):
                current_root(root)

    def test_current_root_rejects_incomplete_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write(root, "SKILL.md", SKILL_TEXT)
            with self.assertRaises(InstallRootError):
                current_root(root)

    def test_current_root_ignores_existing_wrong_depth_decoy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / "skills/tackle"
            _write(package, "SKILL.md", SKILL_TEXT)
            _write(package, "references/guide.md", REFERENCE_TEXT)
            _write(root, "wrong-depth/SKILL.md", DECOY_TEXT)
            self.assertEqual(current_root(root), package.resolve())

    def test_revision_prefix_rejects_invalid_revision_and_git_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            repo, base, _ = build_crossing_repo(temp)
            with self.assertRaises(InstallRootError):
                revision_prefix(repo, "no-such-t01-revision")
            with self.assertRaises(InstallRootError):
                revision_prefix(Path(temp) / "not-a-repository", base)

    def test_historical_logical_paths_preserve_revision_meaning(self):
        with tempfile.TemporaryDirectory() as temp:
            repo, base, current = build_crossing_repo(temp)
            self.assertEqual(revision_path(repo, base, "SKILL.md"), "SKILL.md")
            self.assertEqual(revision_path(repo, current, "SKILL.md"), "skills/tackle/SKILL.md")
            self.assertEqual(revision_path(repo, current, "eval/rules/ledger.json"),
                             "eval/rules/ledger.json")
            for revision, path in ((base, "SKILL.md"), (current, "skills/tackle/SKILL.md")):
                result = subprocess.run(["git", "-C", str(repo), "show", "%s:%s" % (revision, path)],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                self.assertEqual(result.returncode, 0, "git show exit=%d" % result.returncode)

    def test_read_install_requires_explicit_artifact_root(self):
        from eval.behavior.harness.harness import Refusal, read_install

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / "skills/tackle"
            _write(package, "SKILL.md", SKILL_TEXT)
            _write(package, "references/guide.md", REFERENCE_TEXT)
            with self.assertRaises(Refusal):
                read_install(root)
            self.assertEqual(set(read_install(package)), {"SKILL.md", "references/guide.md"})


if __name__ == "__main__":
    unittest.main()
