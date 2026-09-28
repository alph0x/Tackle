"""Install inventory: the shipped install stays thin after relocating maintainer-only content.

Permanent checks read the working tree. The shipped install (``SKILL.md`` plus ``references/``)
carries none of: the changelog, the historical migration checklists, Tackle's own release and
self-lint gates, or the unreferenced vendor collectors and validator example. Every relative link
in the listed files resolves, the five legacy templates keep their pinned hashes, and the eight
self-lint gates are silent.

Standard library only; no network, container or model call. Every "against a temporary copy"
case below builds its own disposable directory and never touches this repository.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def sha256(data):
    return hashlib.sha256(data).hexdigest()


def strip_fences(text):
    """Blank out fenced code blocks, keeping line numbers stable, so link-scanning never
    matches a markdown-link-shaped string inside an example (e.g. a generated report's own
    ``[stdout](stdout.bin)`` line)."""
    out, fence = [], None
    for line in text.split('\n'):
        stripped = line.strip()
        marker = re.match(r'^(`{3,}|~{3,})', stripped)
        if fence:
            if marker and stripped[0] == fence[0] and len(marker.group(1)) >= fence[1]:
                fence = None
            out.append('')
            continue
        if marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
            out.append('')
            continue
        out.append(line)
    return '\n'.join(out)


LINK = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
HEADING = re.compile(r'^(#{1,6})\s+(.*)$')
EXPLICIT_ANCHOR = re.compile(r'<a\s+id="([^"]+)"')


def slugify(heading):
    """Reproduce GitHub's heading slug: lowercase, drop everything but word/space/hyphen
    characters, then turn every remaining space into its own hyphen (runs of spaces are not
    collapsed) -- verified against this repo's own anchors, e.g. "v8.3 -> v8.4 checklist"
    slugifies to "v83--v84-checklist" because the arrow's two flanking spaces both survive."""
    text = re.sub(r'[^\w\s-]', '', heading.strip().lower())
    return ''.join('-' if character.isspace() else character for character in text)


def anchors_of(path):
    text = path.read_text(encoding='utf-8', errors='replace')
    ids = set(EXPLICIT_ANCHOR.findall(text))
    for line in text.split('\n'):
        match = HEADING.match(line)
        if match:
            ids.add(slugify(match.group(2)))
    return ids


def in_scope_files(root):
    """The published Markdown surface: the installed skill, top-level project docs, and the
    repository files a relocation can move content into or out of."""
    out = []
    for name in ('SKILL.md', 'README.md', 'AGENTS.md', 'MAINTAINING.md', 'CHANGELOG.md'):
        candidate = root / name
        if candidate.is_file():
            out.append(candidate)
    for directory in ('references', 'maintaining', 'extras'):
        base = root / directory
        if base.is_dir():
            out.extend(sorted(p for p in base.rglob('*.md') if p.is_file()))
    return out


def check_links(root):
    """Every relative markdown link in the in-scope files resolves to a file, and to an
    anchor where one is given. Returns a list of problem strings, naming the file."""
    problems = []
    for source in in_scope_files(root):
        text = strip_fences(source.read_text(encoding='utf-8', errors='replace'))
        for match in LINK.finditer(text):
            target = match.group(1).strip()
            if not target or target.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            path_part, _, fragment = target.partition('#')
            resolved = (source.parent / path_part).resolve() if path_part else source
            if not resolved.exists():
                problems.append('%s: target missing: %s' % (source.relative_to(root), target))
                continue
            if fragment and fragment not in anchors_of(resolved):
                problems.append('%s: anchor missing: %s' % (source.relative_to(root), target))
    return problems


LEGACY_TEMPLATE_HASHES = {
    'references/point.tmpl.md': 'a6b787c810fa6184af995c2d55eb3a6a9024ac22b9f1f8eee6c4eab8abd2852c',
    'references/log.tmpl.md': 'def3ee4ed6228ebab8e137c57d446a63e9b5eea7d34d4fd01daa96de1d1baca1',
    'references/usage.tmpl.md': 'f48bca9f80d51043642ea8ec4e58ba09eee6f2e924158494cec29c6000736860',
    'references/board.tmpl.md': '2b46170bef238aa537fd71605d3e20c04c88c5744d0947228a6fc41fd72cb00b',
    'references/coordinator.tmpl.md': '2840778e58f8a169a7a02e284b723a302240ea7cd01fd13e7a8fd83c9200ade6',
}


def check_legacy_hashes(root):
    problems = []
    for path, expected in LEGACY_TEMPLATE_HASHES.items():
        target = root / path
        if not target.is_file():
            problems.append('%s: missing' % path)
            continue
        actual = sha256(target.read_bytes())
        if actual != expected:
            problems.append('%s: hash changed (expected %s, got %s)' % (path, expected, actual))
    return problems


# ---------------------------------------------------------------------------
# Gate extraction
# ---------------------------------------------------------------------------

def extract_gates(maintaining_text):
    """The eight self-lint gate commands, extracted the same way
    ``eval/validation-integrity/acceptance.py``'s ``canonical_gates`` does once it reads
    MAINTAINING.md: split after the gates heading, stop at the next heading of any level."""
    after = maintaining_text.split('### Skill self-lint gates\n', 1)[1]
    section = re.split(r'\n#{1,6} ', after, maxsplit=1)[0]
    return [command.strip() for _, command in re.findall(r'^   (`+)(.+?)\1$', section, re.M)]


# ---------------------------------------------------------------------------
# The self-development archetype examples leave the install
# ---------------------------------------------------------------------------

MOVED_ARCHETYPES = ('eval-driven-method-fix.md', 'retro-improvements-batch.md', 'skill-feature-with-eval.md')


def archetype_leaks(root, moved_names=MOVED_ARCHETYPES, moved_hashes=None):
    """Problem strings for any basename- or content-identical copy of a moved archetype file found
    under ``root``'s shipped surface (``SKILL.md`` + ``references/**``), checked by a sha256 sweep
    -- not only the specific old/new path pair. ``moved_hashes`` defaults to hashing each moved
    file at its own new home (``maintaining/archetypes/``) under ``root``."""
    if moved_hashes is None:
        moved_hashes = {}
        for name in moved_names:
            target = root / 'maintaining/archetypes' / name
            if target.is_file():
                moved_hashes[sha256(target.read_bytes())] = name
    problems = []
    shipped = [root / 'SKILL.md'] + (sorted((root / 'references').rglob('*')) if (root / 'references').is_dir() else [])
    for path in shipped:
        if not path.is_file():
            continue
        if path.name in moved_names:
            problems.append('%s: a moved archetype basename is still present under the shipped surface' % path)
            continue
        digest = sha256(path.read_bytes())
        if digest in moved_hashes:
            problems.append('%s: byte-identical to moved archetype %s, still under the shipped surface'
                            % (path, moved_hashes[digest]))
    return problems


# ---------------------------------------------------------------------------
# Permanent checks: the working tree
# ---------------------------------------------------------------------------

class InstallInventoryTests(unittest.TestCase):
    """Case: install inventory -- references/** carries none of the moved categories, and the
    maintaining files exist outside the install."""

    def test_changelog_is_not_in_the_install(self):
        self.assertFalse((ROOT / 'references/CHANGELOG.md').exists())
        self.assertTrue((ROOT / 'CHANGELOG.md').is_file())

    def test_collectors_are_not_in_the_install(self):
        self.assertFalse((ROOT / 'references/collectors').exists())
        self.assertTrue((ROOT / 'extras/collectors').is_dir())

    def test_validator_example_is_not_in_the_install(self):
        self.assertFalse((ROOT / 'references/guides/validator-example.md').exists())
        self.assertTrue((ROOT / 'extras/validator-example.md').is_file())

    def test_historical_checklists_are_not_in_the_install(self):
        text = (ROOT / 'references/guides/migrate.md').read_text(encoding='utf-8')
        for stale in ('## v8.2 → v8.3 checklist', '## v7.3 → v8.0 checklist',
                     '## v2.0 → v2.1.0 checklist', 'F-1 · Agent contract'):
            self.assertNotIn(stale, text, 'historical content still in the install: %r' % stale)

    def test_release_and_self_lint_gate_sections_are_not_in_the_install(self):
        text = (ROOT / 'references/guides/lint-spec.md').read_text(encoding='utf-8')
        for stale in ('## Release sweep', '### Skill self-lint gates'):
            self.assertNotIn(stale, text, 'maintainer content still in the install: %r' % stale)

    def test_maintaining_files_exist_and_do_not_ship(self):
        self.assertTrue((ROOT / 'MAINTAINING.md').is_file())
        self.assertTrue((ROOT / 'maintaining/migrations.md').is_file())
        # Confirms the install artifact boundary is unaffected: update.md's own gate 6 scope is
        # exactly SKILL.md + references/, never repo-root MAINTAINING.md or maintaining/.
        manifest = (ROOT / 'references/guides/update.md').read_text(encoding='utf-8')
        self.assertNotIn('MAINTAINING.md', manifest)
        self.assertNotIn('maintaining/', manifest)

    def test_archetypes_directory_holds_only_the_format_readme(self):
        """The three self-development example files leave the install; only the format/mechanism
        doc (README.md) stays in the shipped `references/archetypes/`."""
        archetypes = ROOT / 'references/archetypes'
        self.assertTrue(archetypes.is_dir())
        self.assertEqual(sorted(p.name for p in archetypes.iterdir()), ['README.md'])

    def test_moved_archetype_files_exist_byte_identical_under_maintaining(self):
        for name in MOVED_ARCHETYPES:
            self.assertTrue((ROOT / 'maintaining/archetypes' / name).is_file(), name)

    def test_no_archetype_content_or_basename_leaks_into_the_shipped_surface(self):
        """A sha256 sweep of `SKILL.md` + `references/**` for the three moved files' content and
        basenames -- broader than the specific old/new path pair alone (disclosed addition)."""
        self.assertEqual(archetype_leaks(ROOT), [])


class LegacyTemplateTests(unittest.TestCase):
    """Case: legacy templates -- the five frozen templates keep the audit's pinned hashes."""

    def test_legacy_template_hashes_are_unchanged(self):
        self.assertEqual(check_legacy_hashes(ROOT), [])


class LinksTests(unittest.TestCase):
    """Case: links -- every relative link in the listed files resolves to a file, and to an
    anchor where one is given."""

    def test_no_broken_links_in_the_named_files(self):
        self.assertEqual(check_links(ROOT), [])


class GatesTests(unittest.TestCase):
    """Case: gates -- the self-lint gates run from MAINTAINING.md, each silent and exit 0."""

    def test_eight_gates_extracted_from_maintaining_are_silent(self):
        maintaining = (ROOT / 'MAINTAINING.md').read_text(encoding='utf-8')
        gates = extract_gates(maintaining)
        self.assertEqual(len(gates), 8)
        for index, command in enumerate(gates, 1):
            result = subprocess.run(['/bin/sh', '-c', command], cwd=ROOT, capture_output=True)
            self.assertEqual(result.returncode, 0, 'gate %d exited %d: %s' % (index, result.returncode, result.stderr))
            self.assertEqual(result.stdout, b'', 'gate %d printed a finding: %s' % (index, result.stdout))

class ShippedEntryPointTests(unittest.TestCase):
    """Case: shipped entry point -- SKILL.md's frontmatter and command tables."""

    def test_one_installed_entry(self):
        skill = (ROOT / 'SKILL.md').read_text()
        self.assertRegex(skill, r'(?m)^name: tackle$')
        self.assertFalse(list((ROOT / 'references').rglob('SKILL.md')))

    def test_active_request_tables_do_not_advertise_legacy_commands(self):
        for name in ('SKILL.md', 'README.md', 'references/guides/invocation.md'):
            rows = [line for line in (ROOT / name).read_text().splitlines() if line.startswith('|')]
            self.assertFalse(any('/tackle-' in line for line in rows), name)


class PlantedDefectTests(unittest.TestCase):
    """Case: planted defect -- a link to a removed path, a gate reading
    references/CHANGELOG.md, or a changed legacy template must each make the relevant check
    fail, naming the file. Every defect is planted in a disposable temporary copy, never in the
    repository."""

    def test_a_dangling_link_is_caught(self):
        with tempfile.TemporaryDirectory(prefix='tackle-t32-defect-') as scratch:
            root = Path(scratch)
            (root / 'references/guides').mkdir(parents=True)
            (root / 'references/guides/lint-spec.md').write_text('# Lint spec\n')
            (root / 'README.md').write_text(
                '[Changelog](references/CHANGELOG.md)\n')  # the pre-move path, now removed
            problems = check_links(root)
            self.assertEqual(len(problems), 1)
            self.assertIn('README.md', problems[0])
            self.assertIn('references/CHANGELOG.md', problems[0])

    def test_a_changed_legacy_template_is_caught(self):
        with tempfile.TemporaryDirectory(prefix='tackle-t32-defect-') as scratch:
            root = Path(scratch)
            (root / 'references').mkdir()
            for path in LEGACY_TEMPLATE_HASHES:
                (root / path).write_bytes((ROOT / path).read_bytes())
            tampered = root / 'references/point.tmpl.md'
            tampered.write_bytes(tampered.read_bytes() + b'\n')
            problems = check_legacy_hashes(root)
            self.assertEqual(len(problems), 1)
            self.assertIn('references/point.tmpl.md', problems[0])

    def test_a_leaked_archetype_copy_under_the_shipped_surface_is_caught_by_content(self):
        """C6's negative fixture: byte-identical content under `references/**`, at a different
        basename, is still a leak (a content-only sweep, distinct from the old/new-path pair)."""
        with tempfile.TemporaryDirectory(prefix='tackle-t11-defect-content-') as scratch:
            root = Path(scratch)
            (root / 'references/guides').mkdir(parents=True)
            (root / 'references/guides/reintroduced-copy.md').write_text('moved content\n')
            problems = archetype_leaks(root, moved_hashes={sha256(b'moved content\n'): 'eval-driven-method-fix.md'})
            self.assertEqual(len(problems), 1)
            self.assertIn('reintroduced-copy.md', problems[0])

    def test_a_leaked_archetype_basename_under_the_shipped_surface_is_caught_by_name(self):
        """Same basename as a moved file reappearing under `references/**`, even with unrelated
        content, is still flagged (a basename-only sweep)."""
        with tempfile.TemporaryDirectory(prefix='tackle-t11-defect-name-') as scratch:
            root = Path(scratch)
            (root / 'references/guides').mkdir(parents=True)
            (root / 'references/guides/eval-driven-method-fix.md').write_text('a different file, same name\n')
            problems = archetype_leaks(root, moved_hashes={})
            self.assertEqual(len(problems), 1)
            self.assertIn('eval-driven-method-fix.md', problems[0])

    def test_a_clean_tree_with_no_leak_passes(self):
        with tempfile.TemporaryDirectory(prefix='tackle-t11-clean-') as scratch:
            root = Path(scratch)
            (root / 'references/guides').mkdir(parents=True)
            (root / 'references/guides/unrelated.md').write_text('nothing to see here\n')
            self.assertEqual(archetype_leaks(root, moved_hashes={sha256(b'moved content\n'): 'eval-driven-method-fix.md'}), [])


if __name__ == '__main__':
    unittest.main()
