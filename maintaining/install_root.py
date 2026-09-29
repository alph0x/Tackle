"""Resolve repository installation roots without changing logical ledger paths."""
from pathlib import Path, PurePosixPath
import subprocess


class InstallRootError(OSError):
    """The repository has no single complete Tackle installation root."""


_LAYOUTS = (('', 'historical repository root'), ('skills/tackle/', 'nested installation'))


def _install_path(path):
    text = str(path).replace('\\', '/')
    if text != 'SKILL.md' and text != 'references' and not text.startswith('references/'):
        return None
    logical = PurePosixPath(text)
    if logical.is_absolute() or '..' in logical.parts or text != logical.as_posix():
        raise InstallRootError('invalid installation-relative path: %s' % path)
    return logical


def _candidate_state(root, prefix):
    skill = root / (prefix + 'SKILL.md')
    references = root / (prefix + 'references')
    skill_present = skill.exists() or skill.is_symlink()
    references_present = references.exists() or references.is_symlink()
    if not skill_present and not references_present:
        return False, False
    complete = (skill.is_file() and not skill.is_symlink()
                and references.is_dir() and not references.is_symlink())
    return True, complete


def current_root(repo):
    """Return the sole complete installation root in the current working tree."""
    root = Path(repo).resolve()
    if not root.is_dir():
        raise InstallRootError('repository root is not a directory: %s' % root)
    candidates, incomplete = [], []
    for prefix, label in _LAYOUTS:
        present, complete = _candidate_state(root, prefix)
        if complete:
            candidates.append((root / prefix, label))
        elif present:
            incomplete.append(label)
    if incomplete:
        raise InstallRootError('incomplete installation candidate: %s' % ', '.join(incomplete))
    if len(candidates) > 1:
        raise InstallRootError('ambiguous installation roots: %s' % ', '.join(label for _, label in candidates))
    if not candidates:
        raise InstallRootError('no complete SKILL.md and references/ installation root')
    return candidates[0][0]


def _git(repo, *args):
    try:
        return subprocess.run(['git', '-C', str(Path(repo).resolve()), *args],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as error:
        raise InstallRootError('Git could not inspect installation revision') from error


def _tree_entry(repo, revision, path):
    result = _git(repo, 'ls-tree', '-z', '--full-tree', revision, '--', path)
    if result.returncode != 0:
        raise InstallRootError('Git could not inspect installation path at revision %s' % revision)
    rows = [row for row in result.stdout.split(b'\0') if row]
    if len(rows) > 1:
        raise InstallRootError('Git returned ambiguous tree entries for %s' % path)
    if not rows:
        return None
    try:
        mode, kind, object_id, name = rows[0].decode('utf-8').split(None, 3)
    except (UnicodeDecodeError, ValueError) as error:
        raise InstallRootError('Git returned an invalid tree entry for %s' % path) from error
    return mode, kind, object_id, name


def _revision_candidate(repo, revision, prefix):
    skill = _tree_entry(repo, revision, prefix + 'SKILL.md')
    references = _tree_entry(repo, revision, prefix + 'references')
    present = skill is not None or references is not None
    complete = (skill is not None and skill[0] in ('100644', '100755') and skill[1] == 'blob'
                and references is not None and references[0] == '040000' and references[1] == 'tree')
    return present, complete


def revision_prefix(repo, revision):
    """Return the install prefix in a real Git revision, never using working-tree paths."""
    resolved = _git(repo, 'rev-parse', '--verify', '--quiet', '--end-of-options', '%s^{commit}' % revision)
    if resolved.returncode != 0:
        raise InstallRootError('revision does not resolve to a Git commit: %s' % revision)
    try:
        commit = resolved.stdout.decode('ascii', 'strict').strip()
    except UnicodeDecodeError as error:
        raise InstallRootError('Git returned an invalid commit id for revision %s' % revision) from error
    candidates, incomplete = [], []
    for prefix, label in _LAYOUTS:
        present, complete = _revision_candidate(repo, commit, prefix)
        if complete:
            candidates.append((prefix, label))
        elif present:
            incomplete.append(label)
    if incomplete:
        raise InstallRootError('incomplete installation candidate at revision %s: %s' %
                               (revision, ', '.join(incomplete)))
    if len(candidates) > 1:
        raise InstallRootError('ambiguous installation roots at revision %s: %s' %
                               (revision, ', '.join(label for _, label in candidates)))
    if not candidates:
        raise InstallRootError('no complete SKILL.md and references/ installation at revision %s' % revision)
    return candidates[0][0]


def current_path(repo, path):
    """Resolve an installation-relative logical path or leave a repository path at repo root."""
    root = Path(repo).resolve()
    logical = _install_path(path)
    return current_root(root) / Path(*logical.parts) if logical is not None else root / path


def revision_path(repo, revision, path):
    """Map an installation-relative logical path into a revision's physical tree path."""
    logical = _install_path(path)
    if logical is not None:
        return revision_prefix(repo, revision) + logical.as_posix()
    return str(path)
