"""Install inventory: the shipped install stays thin after relocating maintainer-only content.

Permanent checks read the working tree. The shipped install (``SKILL.md`` plus ``references/``)
carries none of: the changelog, the historical migration checklists, Tackle's own release and
self-lint gates, or the unreferenced vendor collectors and validator example. Every relative link
in the listed files resolves, the five legacy templates keep their pinned hashes, and the eight
self-lint gates are silent.

Historical checks read commits only. At ``T32_REV``, the commit that made the relocation, every
relocated byte is preserved, unchanged except the enumerated substitutions, in a repository file
that does not ship. Later edits to those files cannot break these checks.

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

ROOT = Path(__file__).resolve().parents[2]
BASE_REV = '03b992e52b1b40faa5e3897a0d4729065f503c02'
# The commit that made the relocation; historical checks compare it with BASE_REV.
T32_REV = 'b2bb990962096417548f1321964dbe2f4e35e1a9'


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def git_show(rev, path, repo=ROOT):
    """Bytes of ``path`` as committed at ``rev`` in ``repo`` (a read-only export)."""
    result = subprocess.run(['git', '-C', str(repo), 'show', '%s:%s' % (rev, path)],
                            capture_output=True, check=True)
    return result.stdout


def line_range(data, start, end):
    """Bytes of the 1-indexed, inclusive lines [start, end] of ``data``, matching what
    ``sed -n 'start,endp'`` would print for an LF-terminated file."""
    parts = data.decode('utf-8').split('\n')
    selected = parts[start - 1:end]
    return ('\n'.join(selected) + '\n').encode('utf-8')


def apply_subs(data, subs):
    text = data.decode('utf-8')
    for before, after in subs:
        count = text.count(before)
        if count != 1:
            raise AssertionError('substitution site not unique (%d occurrences): %r' % (count, before))
        text = text.replace(before, after)
    return text.encode('utf-8')


def reverse_subs(data, subs, path_for_error=''):
    """Undo ``subs`` (each applied exactly once) to recover the pre-substitution bytes."""
    text = data.decode('utf-8')
    for before, after in reversed(subs):
        count = text.count(after)
        if count != 1:
            raise AssertionError('%s: reversal site not unique (%d occurrences): %r'
                                 % (path_for_error, count, after))
        text = text.replace(after, before)
    return text.encode('utf-8')


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
# What moved where, and the exact substitutions each moved block carries
# ---------------------------------------------------------------------------

MOVED_FILES = [
    ('references/CHANGELOG.md', 'CHANGELOG.md'),
    ('references/collectors/README.md', 'extras/collectors/README.md'),
    ('references/collectors/antigravity-cli.md', 'extras/collectors/antigravity-cli.md'),
    ('references/collectors/claude-code.md', 'extras/collectors/claude-code.md'),
    ('references/collectors/cursor.md', 'extras/collectors/cursor.md'),
    ('references/collectors/kimi-code.md', 'extras/collectors/kimi-code.md'),
    ('references/collectors/oh-my-pi.md', 'extras/collectors/oh-my-pi.md'),
    ('references/collectors/openai-responses.md', 'extras/collectors/openai-responses.md'),
    ('references/collectors/opencode.md', 'extras/collectors/opencode.md'),
    ('references/guides/validator-example.md', 'extras/validator-example.md'),
]

# Gate 3: the changelog path gate 3 greps. Anchored to the surrounding "exit}' ... )" rather
# than the bare path, so that a planted defect (the substitution never applied, old path left in
# place) is a *missing* anchor (count 0) rather than a same-suffix false match against
# "references/CHANGELOG.md", which also contains the literal substring "CHANGELOG.md".
SUB_GATE3 = ("exit}' references/CHANGELOG.md)", "exit}' CHANGELOG.md)")
# Gate 4: only the second grep (the fixed v7.3 -> v8.0 candidate check) moves; the first
# (the immediately-previous-version check) still reads migrate.md, since the current checklist
# (v8.3 -> v8.4) stays there.
SUB_GATE4 = ('grep -qF "## v7.3 → v8.0 checklist" references/guides/migrate.md',
            'grep -qF "## v7.3 → v8.0 checklist" maintaining/migrations.md')
# Gate 7: only the self-lint-gate counter's source file moves; the lint-row counter (16 rows)
# stays on lint-spec.md, since the row table itself never moves.
SUB_GATE7 = (
    "g=$(awk '/^### Skill self-lint gates/{f=1;next} f && /^##/{exit} f && /^[0-9]+\\. /{n++} "
    "END{print n+0}' references/guides/lint-spec.md)",
    "g=$(awk '/^### Skill self-lint gates/{f=1;next} f && /^##/{exit} f && /^[0-9]+\\. /{n++} "
    "END{print n+0}' MAINTAINING.md)",
)

# Bare, backtick-quoted mentions of a sibling references/guides/ file that resolved as a
# same-directory reference only while migrate.md itself lived in references/guides/; once it
# moves to maintaining/, each gains the references/guides/ prefix so the pointer still resolves.
# Verified: within the moved ranges, these are the only five such bare mentions (checked against
# every references/guides/*.md basename); every other bare .md mention in the moved text names a
# workspace-local artifact (log.md, board.md, decisions.md, ...) that was never a same-directory
# reference and so is left untouched.
SUB_FULL_CHECKS = ('`full-checks.md`', '`references/guides/full-checks.md`')
SUB_VERIFY = ('`verify.md` step 0 is now two-phase', '`references/guides/verify.md` step 0 is now two-phase')
SUB_INTAKE = ('Step 1 of `intake-and-gate.md`', 'Step 1 of `references/guides/intake-and-gate.md`')
SUB_DESIGN = ('Step 5.5 of `design-and-contract.md`', 'Step 5.5 of `references/guides/design-and-contract.md`')
SUB_STATUS = ('the archive protocol (`status.md` §Archive)',
             'the archive protocol (`references/guides/status.md` §Archive)')

# Each entry: source file at BASE_REV, its 1-indexed inclusive line range, the substitutions
# applied (in order) when the block lands at its new home, and that new home.
EXTRACTED_BLOCKS = [
    dict(source='references/guides/lint-spec.md', start=50, end=95,
        subs=[SUB_GATE3, SUB_GATE4, SUB_GATE7], dest='MAINTAINING.md'),
    dict(source='references/guides/lint-spec.md', start=106, end=112,
        subs=[], dest='MAINTAINING.md'),
    dict(source='references/guides/migrate.md', start=25, end=38,
        subs=[], dest='maintaining/migrations.md'),
    dict(source='references/guides/migrate.md', start=109, end=636,
        subs=[SUB_FULL_CHECKS, SUB_VERIFY, SUB_INTAKE, SUB_DESIGN, SUB_STATUS],
        dest='maintaining/migrations.md'),
]

# What stays in each edited guide, verbatim, at BASE_REV line numbers. lines 96-105 are the lint
# (not sweep) score -- heading, paragraph, the `lint: N/M` marker, and its own M/N bullets, which
# stay because ordinary PLAN Full workspaces compute this digest for every task, not only a
# release sweep. Lines 113-116 are the row-8 filter, the symbol notation, the warn-severity rule
# and the digest rule -- interpretive notes for the 16-row table, which never moves. Both ranges
# were located by matching their actual, distinctive content (the lint-digest bullets' own text,
# and each of the four listed rule descriptions) against the file at BASE_REV, not assumed from a
# line-number range alone.
LINTSPEC_STAYS = [(1, 49), (96, 105), (113, None)]
MIGRATE_STAYS = [(1, 7), (13, 24), (39, 108)]

MIGRATE_POINTER = ("Historical checklists for older workspaces are in the repository's\n"
                   "`maintaining/migrations.md`; they remain readable historical context and cannot bypass the\n"
                   "current selection, pinning, history or rollback guards.")
LINTSPEC_POINTER = ("The release sweep and the eight self-lint gates are documented in the "
                    "repository's\n`MAINTAINING.md`.")


def block_bytes(entry):
    """The expected bytes of an extracted block at its NEW home: BASE_REV content with exactly
    the listed substitutions applied."""
    source = git_show(BASE_REV, entry['source'])
    original = line_range(source, entry['start'], entry['end'])
    return apply_subs(original, entry['subs'])


def stay_bytes(path, ranges):
    parts = []
    for start, end in ranges:
        data = git_show(BASE_REV, path)
        if end is None:
            end = len(data.decode('utf-8').split('\n'))
        parts.append(line_range(data, start, end))
    return b''.join(parts)


def expected_lintspec_bytes():
    # 1-49 ends blank; a new pointer paragraph (replacing the section this file used to carry)
    # is inserted before "## Score line" resumes at 96; 96-105 ends blank; 113-end begins the
    # row-8 bullet. The 96-105/113-end join already carries exactly one blank line at that
    # boundary in the original file, so that pair concatenates directly with no inserted
    # separator.
    lines_1_49 = line_range(git_show(BASE_REV, 'references/guides/lint-spec.md'), 1, 49)
    rest = stay_bytes('references/guides/lint-spec.md', LINTSPEC_STAYS[1:])
    # The file ends with exactly one newline, as it did at BASE_REV (D-72).
    return (lines_1_49 + LINTSPEC_POINTER.encode('utf-8') + b'\n\n' + rest).rstrip(b'\n') + b'\n'


def expected_migrate_bytes():
    lines_1_7 = line_range(git_show(BASE_REV, 'references/guides/migrate.md'), 1, 7)
    lines_13_24 = line_range(git_show(BASE_REV, 'references/guides/migrate.md'), 13, 24)
    lines_39_108 = line_range(git_show(BASE_REV, 'references/guides/migrate.md'), 39, 108)
    # lines_1_7 is untouched -- line 7 keeps its own original bytes and trailing newline, so this
    # range stays byte-identical on its own. The pointer is appended as new lines continuing the
    # same paragraph (the original had no blank line between line 7 and line 8 either).
    # lines_13_24 already opens with line 13's own blank line, so no extra separator is added here.
    # lines_13_24 also *closes* with blank line 24, and lines_39_108 *opens* with blank line 39
    # (the separator on each side of the removed F-1..F-8 block); concatenating both leading and
    # trailing separators would leave two blank lines where the original had one, so the leading
    # "\n" of lines_39_108 is dropped here.
    assert lines_39_108[:1] == b'\n'
    # Line 108 is the blank separator before the moved chain; the file ends with exactly one newline (D-72).
    return (lines_1_7 + MIGRATE_POINTER.encode('utf-8') + b'\n'
           + lines_13_24 + lines_39_108[1:]).rstrip(b'\n') + b'\n'


def extract_gates(maintaining_text):
    """The eight self-lint gate commands, extracted the same way
    ``eval/validation-integrity/acceptance.py``'s ``canonical_gates`` does once it reads
    MAINTAINING.md: split after the gates heading, stop at the next heading of any level."""
    after = maintaining_text.split('### Skill self-lint gates\n', 1)[1]
    section = re.split(r'\n#{1,6} ', after, maxsplit=1)[0]
    return [command.strip() for _, command in re.findall(r'^   (`+)(.+?)\1$', section, re.M)]


def at_t32(path):
    """Text of ``path`` as committed at T32_REV."""
    return git_show(T32_REV, path).decode('utf-8')


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

    def test_gate_3_and_gate_5_pass_at_the_new_paths(self):
        maintaining = (ROOT / 'MAINTAINING.md').read_text(encoding='utf-8')
        gate3, gate5 = extract_gates(maintaining)[2], extract_gates(maintaining)[4]
        for command in (gate3, gate5):
            result = subprocess.run(['/bin/sh', '-c', command], cwd=ROOT, capture_output=True)
            self.assertEqual((result.returncode, result.stdout), (0, b''))


# ---------------------------------------------------------------------------
# Historical checks: commits only (T32_REV against BASE_REV)
# ---------------------------------------------------------------------------

class HistoricalRelocationTests(unittest.TestCase):
    """Case: byte preservation -- at T32_REV, each moved file and each extracted block equals its
    BASE_REV bytes (reversing exactly the enumerated substitutions), and the edited guides
    reconstruct exactly."""

    def test_moved_files_are_byte_identical(self):
        for old, new in MOVED_FILES:
            expected = git_show(BASE_REV, old)
            actual = git_show(T32_REV, new)
            self.assertEqual(sha256(actual), sha256(expected), '%s changed in the move' % new)

    def test_extracted_blocks_reverse_to_their_original_bytes(self):
        for entry in EXTRACTED_BLOCKS:
            expected = line_range(git_show(BASE_REV, entry['source']), entry['start'], entry['end'])
            dest = at_t32(entry['dest'])
            found = self._locate(dest, entry)
            actual = reverse_subs(found.encode('utf-8'), entry['subs'], entry['dest'])
            self.assertEqual(sha256(actual), sha256(expected),
                             '%s:%d-%d (now in %s) is not byte-identical after reversing '
                             'its substitutions' % (entry['source'], entry['start'], entry['end'], entry['dest']))

    def test_edited_guides_reconstruct_exactly_from_base_rev(self):
        self.assertEqual(git_show(T32_REV, 'references/guides/lint-spec.md'), expected_lintspec_bytes())
        self.assertEqual(git_show(T32_REV, 'references/guides/migrate.md'), expected_migrate_bytes())

    def test_stayed_ranges_are_byte_identical(self):
        current = at_t32('references/guides/lint-spec.md')
        for start, end in LINTSPEC_STAYS:
            source = git_show(BASE_REV, 'references/guides/lint-spec.md')
            if end is None:
                end = len(source.decode('utf-8').split('\n'))
            expected = line_range(source, start, end)
            self.assertIn(expected.decode('utf-8').rstrip('\n'), current,
                         'lines %d-%s of %s no longer appear verbatim' % (start, end, BASE_REV))

    @staticmethod
    def _locate(dest_text, entry):
        """Find an extracted block inside its new home by its first line, then take exactly as
        many lines as the block spans (substitutions never add or remove a line)."""
        source_bytes = git_show(BASE_REV, entry['source'])
        first_line = source_bytes.decode('utf-8').split('\n')[entry['start'] - 1]
        span = entry['end'] - entry['start'] + 1
        dest_lines = dest_text.split('\n')
        for index, line in enumerate(dest_lines):
            if line == first_line:
                return '\n'.join(dest_lines[index:index + span]) + '\n'
        raise AssertionError('%s: could not locate the block starting %r' % (entry['dest'], first_line))


class HistoricalContentTests(unittest.TestCase):
    """Case: the relocation kept the install's current content -- at T32_REV, migrate.md still
    holds the current checklists and the pointer, and lint-spec.md still holds its score line."""

    def test_current_checklists_and_pointer_stayed(self):
        text = at_t32('references/guides/migrate.md')
        self.assertIn('## v8.4.0 → v8.4.1 checklist', text)
        self.assertIn('## v8.3 → v8.4 checklist', text)
        self.assertIn('maintaining/migrations.md', text)

    def test_score_line_stayed(self):
        self.assertIn('## Score line', at_t32('references/guides/lint-spec.md'))


class HistoricalVersionTests(unittest.TestCase):
    """Case: unchanged version -- at T32_REV, the stamps and the changelog head are still 8.4.1."""

    def test_stamps_are_unchanged(self):
        self.assertIn('**Tackle 8.4.1**', at_t32('SKILL.md'))
        self.assertTrue(at_t32('CHANGELOG.md').startswith('# Tackle changelog\n\n## Tackle 8.4.1\n'))


class HistoricalRecipesAndRulesTests(unittest.TestCase):
    """Case: recipes and rules -- at T32_REV, candidate_board loads from its new home, the task
    contracts read it there, and R-MIGRATE-03 alone is retired with an updated home."""

    def test_candidate_board_recipe_moved_unchanged(self):
        expected = block_bytes(dict(source='references/guides/migrate.md', start=109, end=636,
                                    subs=EXTRACTED_BLOCKS[3]['subs']))
        self.assertIn(b"def candidate_board(text, reports):", expected)
        migrations = git_show(T32_REV, 'maintaining/migrations.md')
        self.assertIn(b"def candidate_board(text, reports):", migrations)

    def test_test_task_contracts_reads_the_new_home(self):
        text = at_t32('eval/task-contracts/test_task_contracts.py')
        self.assertNotIn("recipe('references/guides/migrate.md')", text)
        self.assertEqual(text.count("recipe('maintaining/migrations.md')['candidate_board']"), 3)

    def test_ledger_retires_r_migrate_03_only(self):
        import json
        already_retired = {rule['rule_id'] for rule in json.loads(git_show(BASE_REV, 'eval/rules/ledger.json'))['rules']
                           if isinstance(rule, dict) and 'retired_in' in rule}
        ledger = json.loads(git_show(T32_REV, 'eval/rules/ledger.json'))
        rules = {rule['rule_id']: rule for rule in ledger['rules'] if isinstance(rule, dict) and 'rule_id' in rule}
        migrate03 = rules['R-MIGRATE-03']
        self.assertEqual(migrate03.get('retired_in'), '9.0.0')
        self.assertTrue(migrate03['home'].startswith('maintaining/migrations.md:'))
        self.assertFalse(migrate03['hot_path'])
        for rule_id, rule in rules.items():
            if rule_id in already_retired | {'R-MIGRATE-03'}:
                continue
            self.assertNotIn('retired_in', rule, '%s was unexpectedly retired' % rule_id)


class HistoricalSelfCheckTests(unittest.TestCase):
    """Case: the historical checks, and the helpers they call, read commits and never the
    working tree, so a later edit cannot change their result."""

    def test_historical_checks_read_only_commits(self):
        import inspect
        readers = (HistoricalRelocationTests, HistoricalContentTests, HistoricalVersionTests,
                   HistoricalRecipesAndRulesTests, at_t32, block_bytes, stay_bytes,
                   expected_lintspec_bytes, expected_migrate_bytes)
        for reader in readers:
            source = inspect.getsource(reader)
            for pattern in ('ROOT /', 'read_bytes(', 'read_text(', 'open(', 'Path('):
                self.assertNotIn(pattern, source, '%s reads the working tree (%s)' % (reader.__name__, pattern))


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

    def test_a_gate_still_reading_the_old_changelog_path_is_caught(self):
        entry = EXTRACTED_BLOCKS[0]  # the block carrying gate 3
        correct = block_bytes(entry)
        defective = correct.replace(b'CHANGELOG.md', b'references/CHANGELOG.md', 1)
        with self.assertRaises(AssertionError) as failure:
            reverse_subs(defective, entry['subs'], entry['dest'])
        self.assertIn(entry['dest'], str(failure.exception))

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


if __name__ == '__main__':
    unittest.main()
