"""Every removed sentence unit of a ledger home/mirrors file is accounted for, mechanically.

Every case runs a small, disposable two-revision git repository built at test time (never
committed, matching this repository's own established convention for rule-ledger fixtures): a base
commit holding the "before" files and ledger, then an
uncommitted working-tree edit holding the "candidate" state -- the same shape check_unit_diff.py
reads in real use (a base revision, plus whatever is currently on disk in --repo). One case reads
two fixed, immutable historical revisions of this repository's own real file instead of a synthetic
repo, since that content can never move again.
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = (Path(__file__).resolve().parents[4] / 'eval/rules')
REPO = HERE.parent.parent
TOOL = HERE / 'check_unit_diff.py'
sys.path.insert(0, str(REPO))
from maintaining.install_root import revision_path  # noqa: E402

GIT_ENV = {'GIT_AUTHOR_NAME': 'fixture', 'GIT_AUTHOR_EMAIL': 'fixture@invalid', 'GIT_COMMITTER_NAME': 'fixture',
           'GIT_COMMITTER_EMAIL': 'fixture@invalid', 'GIT_CONFIG_NOSYSTEM': '1', 'HOME': '/nonexistent'}

spec = importlib.util.spec_from_file_location('check_unit_diff', TOOL)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def ledger(rules):
    return {'schema': 'tackle-unit-dispositions-fixture/1', 'rules': rules, 'non_normative': []}


def rule(home, mirrors=None):
    return {'home': home, 'mirrors': mirrors or []}


def dispositions(records):
    return {'schema': 'tackle-unit-dispositions/1', 'records': records}


def record(path, line, text, disposition, destination=None, note=None, destination_unit_sha256=None, dropped=None):
    out = {'path': path, 'line': line, 'unit_sha256': sha(text), 'disposition': disposition,
           'destination': destination, 'note': note, 'destination_unit_sha256': destination_unit_sha256}
    if dropped is not None:
        out['dropped'] = dropped
    return out


class GitRepoTestCase(unittest.TestCase):
    """A fresh, disposable `git init` in a temporary directory (never the real working tree),
    isolated from the operator's own git config."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        self.git('init', '-q', '-b', 'main')
        # Inert installation shape; no sentence units or changed case semantics.
        self.write('SKILL.md', '')
        self.write('references/.keep', '')

    def git(self, *args):
        env = dict(os.environ, **GIT_ENV)
        result = subprocess.run(['git', '-C', str(self.repo)] + list(args), capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def write(self, relative, text):
        target = self.repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def remove(self, relative):
        (self.repo / relative).unlink()

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', message)

    def base(self, files, ledger_rules):
        """Write every (path, text) plus the fixture ledger, commit, and return the base sha."""
        for path, text in files.items():
            self.write(path, text)
        self.write('eval/rules/ledger.json', json.dumps(ledger(ledger_rules), indent=2) + '\n')
        self.commit('base')
        return self.git('rev-parse', 'HEAD').stdout.strip()

    def candidate(self, files, ledger_rules=None):
        """Overwrite the working tree to the candidate state, uncommitted."""
        for path, text in files.items():
            self.write(path, text)
        if ledger_rules is not None:
            self.write('eval/rules/ledger.json', json.dumps(ledger(ledger_rules), indent=2) + '\n')

    def write_dispositions(self, records):
        self.write('eval/rules/unit-dispositions.json', json.dumps(dispositions(records), indent=2) + '\n')

    def run_tool(self, base, timeout=30):
        result = subprocess.run([sys.executable, str(TOOL), '--repo', str(self.repo), '--base', base],
                                capture_output=True, text=True, timeout=timeout)
        return result


# A sentence needs 8+ words to ever risk shipped auto-match; fixture "home" files below live
# outside SKILL.md/references/ specifically so ordinary cases are never accidentally auto-closed by
# the shipped-tree branch under test elsewhere (see the dedicated shipped-floor cases).
HOME_X, HOME_Y, HOME_Z = 'docs/fixtures/x.md', 'docs/fixtures/y.md', 'docs/fixtures/z.md'
FILLER = 'A filler sentence that never changes across any revision of this fixture file.\n'


class SameFileDuplicateCollapsesToHome(GitRepoTestCase):
    def test_a_sentence_kept_once_is_home_not_a_loss(self):
        kept = 'Alpha sentence appears in this fixture file for testing purposes today.'
        base_sha = self.base({HOME_X: '%s\n\n%s\n' % (kept, kept)}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: '%s\n' % kept})
        self.write_dispositions([record(HOME_X, 1, kept, 'home')])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('applied', result.stdout)


class RewordedToADifferentPlace(GitRepoTestCase):
    def test_a_removed_sentence_reworded_elsewhere_passes(self):
        removed = 'Original phrasing of an obligation stays fully out of this file after the edit.'
        new_text = 'This obligation now lives here in completely different words for the reader.\n'
        base_sha = self.base({HOME_X: removed + '\n', HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER + new_text})
        self.write_dispositions([record(HOME_X, 1, removed, 'reworded', destination=HOME_Y, note=new_text.strip())])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class MergedIntoADifferentFile(GitRepoTestCase):
    def test_a_removed_sentence_found_verbatim_in_another_file_passes(self):
        moved = 'A sentence moves whole from one file to a different one during this edit.'
        base_sha = self.base({HOME_X: moved + '\n' + FILLER, HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER + moved + '\n'})
        self.write_dispositions([record(HOME_X, 1, moved, 'merged', destination=HOME_Y, destination_unit_sha256=sha(moved))])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class RuledNonNormative(GitRepoTestCase):
    def test_a_removed_sentence_ruled_non_normative_passes(self):
        cut = 'A purely descriptive aside gets trimmed away during this edit for length only.'
        base_sha = self.base({HOME_X: cut + '\n' + FILLER}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: FILLER})
        self.write_dispositions([record(HOME_X, 1, cut, 'ruled', note='a purely descriptive aside, no obligation of its own')])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class NegativeNoDisposition(GitRepoTestCase):
    def test_a_removed_sentence_with_no_record_fails(self):
        cut = 'A sentence disappears from this file with nobody ever accounting for it.'
        base_sha = self.base({HOME_X: cut + '\n' + FILLER}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: FILLER})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn('removed unit with no disposition', result.stdout + result.stderr)


class NegativeDestinationDoesNotHoldIt(GitRepoTestCase):
    def test_a_reworded_record_whose_destination_lacks_the_note_is_void(self):
        removed = 'A sentence claims to move somewhere it never actually landed at all.'
        base_sha = self.base({HOME_X: removed + '\n', HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER})
        self.write_dispositions([record(HOME_X, 1, removed, 'reworded', destination=HOME_Y,
                                         note='this exact sentence is nowhere in the destination file')])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn('void', result.stdout + result.stderr)

    def test_a_merged_record_whose_destination_hash_is_absent_is_void(self):
        removed = 'A second sentence claims a merge destination that never holds its own hash.'
        base_sha = self.base({HOME_X: removed + '\n', HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER})
        self.write_dispositions([record(HOME_X, 1, removed, 'merged', destination=HOME_Y,
                                         destination_unit_sha256=sha('text that does not exist anywhere'))])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn('void', result.stdout + result.stderr)


class TokenPreservation(GitRepoTestCase):
    def test_a_dropped_normative_token_without_a_reason_fails(self):
        removed = 'Every session must record the outcome before the reviewer closes it.'
        new_text = 'Every session must record the outcome before closing it.\n'  # drops "reviewer"
        base_sha = self.base({HOME_X: removed + '\n', HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER + new_text})
        self.write_dispositions([record(HOME_X, 1, removed, 'reworded', destination=HOME_Y, note=new_text.strip())])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn('drops normative token', result.stdout + result.stderr)

    def test_the_same_dropped_token_declared_with_a_reason_passes(self):
        removed = 'Every session must record the outcome before the reviewer closes it.'
        new_text = 'Every session must record the outcome before closing it.\n'  # drops "reviewer"
        base_sha = self.base({HOME_X: removed + '\n', HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER + new_text})
        self.write_dispositions([record(HOME_X, 1, removed, 'reworded', destination=HOME_Y, note=new_text.strip(),
                                         dropped=[{'token': 'reviewer', 'reason': 'the step is anonymous now'}])])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class FencedBlockRemoved(GitRepoTestCase):
    def test_a_removed_fenced_block_with_no_record_fails(self):
        fenced = '```text\nan illustrative fence with plenty of separate words inside it today\n```\n'
        base_sha = self.base({HOME_X: fenced + FILLER}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: FILLER})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn('removed unit with no disposition', result.stdout + result.stderr)

    def test_the_same_removed_fenced_block_with_a_record_passes(self):
        fenced_text = '```text\nan illustrative fence with plenty of separate words inside it today\n```'
        base_sha = self.base({HOME_X: fenced_text + '\n' + FILLER}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: FILLER})
        self.write_dispositions([record(HOME_X, 1, tool.collapse(fenced_text), 'ruled',
                                         note='an illustrative fence, no obligation of its own')])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class FencedBlockShippedAutoMatch(GitRepoTestCase):
    def test_a_fenced_block_found_verbatim_in_the_shipped_tree_auto_closes(self):
        fenced = '```text\nthis fenced example has quite a few separate words inside it\n```\n'
        base_sha = self.base({'SKILL.md': fenced + FILLER, 'references/guides/other.md': FILLER},
                              [rule('SKILL.md:1')])
        self.candidate({'SKILL.md': FILLER, 'references/guides/other.md': FILLER + fenced})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('auto-matched (shipped)', result.stdout)


class FencedBlockIntoMaintainerMaterialNeverAutoCloses(GitRepoTestCase):
    def test_a_fenced_block_moved_only_into_maintainer_material_still_needs_a_record(self):
        # Shaped like the real migrate.md -> maintaining/migrations.md move: a fenced block relocated
        # verbatim into maintainer-only material never auto-closes, however long or exact the match.
        fenced = '```python\ndef relocated_helper():\n    return "moved verbatim into maintainer-only material during the edit"\n```\n'
        base_sha = self.base({HOME_X: fenced + FILLER}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: FILLER, 'MAINTAINING.md': FILLER + fenced})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('auto-matched', result.stdout)
        self.assertIn('removed unit with no disposition', result.stdout + result.stderr)


class FenceCommentParity(GitRepoTestCase):
    """Mirrors duplicates.blocks()'s own per-line precedence (fence-state, then HTML-comment state,
    then a fresh boundary): a fence-shaped line inside an HTML comment is never a fence boundary, and
    an opening fence never closed before EOF contributes no unit. Neither property has a
    pre-extension analogue to fail -- the unextended tool already contributes no fenced units at all
    -- so both stay green before and after; their value is guarding the new code's own edge behavior.
    Each fixture *removes* the shielded/unterminated span entirely between revisions (rather than
    leaving base and candidate identical), so a buggy scanner that mistakenly treats the shielded or
    unterminated span as a real unit would show it as removed and fail; only correct exclusion stays
    silent both before and after."""

    def test_a_fence_shaped_line_inside_an_html_comment_contributes_no_unit(self):
        text = '<!--\n```\ninside\n```\n-->\n' + FILLER
        base_sha = self.base({HOME_X: text}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: FILLER})  # the whole comment-shielded block is removed
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_an_unclosed_fence_at_eof_contributes_no_unit(self):
        text = FILLER + '```text\nan opening fence that is never closed before end of file\n'
        base_sha = self.base({HOME_X: text}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: FILLER})  # the whole unterminated span is removed
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class TokenPreservationOnAFencedBlock(GitRepoTestCase):
    def test_a_reworded_fenced_block_that_drops_a_normative_token_without_a_reason_fails(self):
        removed_inner = 'Every session must record the outcome before the reviewer closes it.'
        new_inner = 'Every session must record the outcome before closing it.'  # drops "reviewer"
        removed_fence = '```text\n%s\n```' % removed_inner
        new_fence = '```text\n%s\n```\n' % new_inner
        base_sha = self.base({HOME_X: removed_fence + '\n', HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER + new_fence})
        self.write_dispositions([record(HOME_X, 1, tool.collapse(removed_fence), 'reworded', destination=HOME_Y,
                                         note=new_inner)])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn('drops normative token', result.stdout + result.stderr)

    def test_the_same_dropped_token_declared_with_a_reason_passes(self):
        removed_inner = 'Every session must record the outcome before the reviewer closes it.'
        new_inner = 'Every session must record the outcome before closing it.'
        removed_fence = '```text\n%s\n```' % removed_inner
        new_fence = '```text\n%s\n```\n' % new_inner
        base_sha = self.base({HOME_X: removed_fence + '\n', HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER + new_fence})
        self.write_dispositions([record(HOME_X, 1, tool.collapse(removed_fence), 'reworded', destination=HOME_Y,
                                         note=new_inner,
                                         dropped=[{'token': 'reviewer', 'reason': 'the step is anonymous now'}])])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class FileSetUnionAcrossLedgers(GitRepoTestCase):
    def test_a_mirror_only_at_base_still_keeps_its_file_covered(self):
        cut = 'Z keeps a unit that nobody ever writes a disposition record for.'
        base_sha = self.base({HOME_X: FILLER, HOME_Z: cut + '\n' + FILLER},
                              [rule('%s:1' % HOME_X, mirrors=['%s:1' % HOME_Z])])
        # The candidate ledger moves the rule's home to Y and drops the old Z mirror entirely; Z is
        # covered only through the *base* ledger's mirrors entry.
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER, HOME_Z: FILLER}, ledger_rules=[rule('%s:1' % HOME_Y)])
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn(HOME_Z, result.stdout + result.stderr)


class StickyLedgerCoverage(GitRepoTestCase):
    """A file dropped by every current ledger (base and candidate alike) stays covered as long as
    any commit that ever touched eval/rules/ledger.json, reachable from HEAD, once named it."""

    def test_a_file_only_covered_by_an_older_ledger_still_needs_its_dispositions(self):
        cut = 'Z keeps a unit that no current ledger entry accounts for any longer today.'
        self.base({HOME_Z: cut + '\n' + FILLER}, [rule('%s:1' % HOME_Z)])
        self.write('eval/rules/ledger.json', json.dumps(ledger([]), indent=2) + '\n')
        self.commit('drops Z from the ledger entirely')
        base_sha = self.git('rev-parse', 'HEAD').stdout.strip()
        self.candidate({HOME_Z: FILLER})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn('removed unit with no disposition: %s' % HOME_Z, result.stdout + result.stderr)

    def test_the_same_sticky_coverage_with_a_valid_record_passes(self):
        cut = 'Z keeps a unit that no current ledger entry accounts for any longer today.'
        self.base({HOME_Z: cut + '\n' + FILLER}, [rule('%s:1' % HOME_Z)])
        self.write('eval/rules/ledger.json', json.dumps(ledger([]), indent=2) + '\n')
        self.commit('drops Z from the ledger entirely')
        base_sha = self.git('rev-parse', 'HEAD').stdout.strip()
        self.candidate({HOME_Z: FILLER})
        self.write_dispositions([record(HOME_Z, 1, cut, 'ruled', note='kept only for a sticky-coverage regression fixture')])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('applied', result.stdout)


class MalformedHistoricalLedgerIsSkippedNotFatal(GitRepoTestCase):
    def test_an_invalid_json_ledger_in_an_intermediate_commit_is_skipped_and_an_older_valid_one_still_covers_its_file(self):
        # Three commits: the oldest has a valid ledger covering Z; the middle one replaces the
        # ledger with invalid JSON; the base has a valid ledger again that no longer names Z. The
        # malformed commit must be skipped (never a crash) while the walk still reaches the older,
        # valid commit -- a walk that instead stops at the malformed commit would miss Z entirely.
        cut = 'Z holds a sentence that only an older, valid ledger commit ever covered at all.'
        self.base({HOME_Z: cut + '\n' + FILLER}, [rule('%s:1' % HOME_Z)])
        self.write('eval/rules/ledger.json', '{ this is not valid json,,, ')
        self.commit('a malformed intermediate ledger commit')
        self.write('eval/rules/ledger.json', json.dumps(ledger([]), indent=2) + '\n')
        self.commit('a valid ledger again, no longer naming Z')
        base_sha = self.git('rev-parse', 'HEAD').stdout.strip()
        self.candidate({HOME_Z: FILLER})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn('removed unit with no disposition: %s' % HOME_Z, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)


class CoveredFileDeletedOrRenamed(GitRepoTestCase):
    def test_a_covered_file_removed_entirely_still_needs_its_dispositions(self):
        base_sha = self.base({HOME_X: 'A sentence lives only in a file that vanishes entirely next.\n'},
                              [rule('%s:1' % HOME_X)])
        self.remove(HOME_X)
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn('removed unit with no disposition', result.stdout + result.stderr)


class DormantRecord(GitRepoTestCase):
    def test_a_valid_record_for_a_unit_that_is_not_currently_removed_is_dormant(self):
        kept = 'This sentence is present at both the base and the candidate, unchanged.'
        base_sha = self.base({HOME_X: kept + '\n'}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: kept + '\n'})
        self.write_dispositions([record(HOME_X, 1, kept, 'ruled', note='kept on purpose, recorded defensively')])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('dormant', result.stdout)

    def test_a_record_whose_own_removed_text_predates_a_later_base_stays_dormant_not_void(self):
        # A run's own resolved base necessarily advances over time (a later tag, or -- forever
        # after this commit -- this commit's own successors); a record committed for a much older
        # removal then can no longer recover its removed text from that later base's tree at all,
        # since it was already gone before that base existed. That must never make the record
        # void: both it and "currently removed" are read from the same base, so a record that
        # cannot recover from this base cannot be part of this base's removed set either.
        moved = 'A sentence moves whole from one file to a different one during this edit.'
        self.base({HOME_X: moved + '\n' + FILLER, HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER + moved + '\n'})
        self.write_dispositions([record(HOME_X, 1, moved, 'merged', destination=HOME_Y, destination_unit_sha256=sha(moved))])
        self.commit('records the disposition for the move above')
        later_base = self.git('rev-parse', 'HEAD').stdout.strip()
        # Advance further: a later commit changes an unrelated file only, so the committed record's
        # own removed text ("moved") is now further in the past than this new base.
        self.write('docs/fixtures/unrelated.md', FILLER)
        self.commit('an unrelated later change')
        result = self.run_tool(later_base)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('dormant', result.stdout)
        self.assertNotIn('void', result.stdout + result.stderr)


class BaseResolution(GitRepoTestCase):
    """The base-resolution search's own sub-cases: only tags predate the marker; a marker-bearing
    tag exists; the marker is staged, not committed; the marker's first-add commit is HEAD itself."""

    def test_only_tags_predate_the_marker_resolves_to_its_first_add_commit(self):
        self.write('README.md', 'no marker yet\n')
        self.commit('no marker')
        self.git('tag', 'v1')
        self.write('eval/rules/ledger.json', json.dumps(ledger([])) + '\n')
        self.write_dispositions([])
        self.commit('adds the marker')
        add_commit_sha = self.git('rev-parse', 'HEAD').stdout.strip()
        self.write('README.md', 'an untagged follow-up change, after the marker\n')
        self.commit('untagged follow-up')  # HEAD^ points at "adds the marker", not this commit
        result = self.run_tool('auto')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # The commit that first adds the marker, never the older tag "v1" (which predates it) and
        # never plain HEAD (a naive "always resolve to HEAD" implementation would print HEAD's own
        # sha here instead, and this assertion would catch it -- verified by planting exactly that
        # defect and observing this line fail).
        self.assertIn('base: %s' % add_commit_sha, result.stdout)

    def test_a_marker_bearing_tag_resolves_to_it(self):
        self.write('README.md', 'no marker yet\n')
        self.commit('no marker')
        self.write('eval/rules/ledger.json', json.dumps(ledger([])) + '\n')
        self.write_dispositions([])
        self.commit('adds the marker')
        self.git('tag', 'v1')
        self.write('README.md', 'an untagged follow-up change\n')
        self.commit('untagged change')
        result = self.run_tool('auto')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # The tag itself, never the untagged HEAD commit above it (a naive "always resolve to HEAD"
        # implementation would print the untagged commit's own sha instead).
        self.assertIn('base: v1', result.stdout)

    def test_a_marker_only_staged_never_committed_refuses(self):
        self.write('README.md', 'no marker at all, anywhere in history\n')
        self.commit('no marker')
        self.write_dispositions([])  # written to the working tree only, never committed
        result = self.run_tool('auto')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('error:', result.stdout + result.stderr)

    def test_the_markers_own_first_add_commit_as_head_is_a_clean_no_op(self):
        self.write('README.md', 'no marker yet\n')
        self.commit('no marker')
        self.write('eval/rules/ledger.json', json.dumps(ledger([])) + '\n')
        self.write_dispositions([])
        self.commit('adds the marker')  # this commit is HEAD
        head_sha = self.git('rev-parse', 'HEAD').stdout.strip()
        result = self.run_tool('auto')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('base: %s' % head_sha, result.stdout)


class ShippedAutoMatchFloor(GitRepoTestCase):
    def test_a_shipped_match_at_or_above_the_floor_auto_closes_with_no_record(self):
        long_enough = 'This sentence has at least eight separate words inside it for the floor.'
        base_sha = self.base({'SKILL.md': long_enough + '\n', 'references/guides/other.md': FILLER},
                              [rule('SKILL.md:1')])
        self.candidate({'SKILL.md': FILLER, 'references/guides/other.md': FILLER + long_enough + '\n'})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('auto-matched (shipped)', result.stdout)

    def test_a_shipped_match_below_the_floor_still_needs_a_record(self):
        short = 'Six short words only, nothing more.'
        self.assertLess(len(short.split()), 8)
        base_sha = self.base({'SKILL.md': short + '\n', 'references/guides/other.md': FILLER},
                              [rule('SKILL.md:1')])
        self.candidate({'SKILL.md': FILLER, 'references/guides/other.md': FILLER + short + '\n'})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('auto-matched (shipped)', result.stdout)
        self.assertIn('removed unit with no disposition', result.stdout + result.stderr)


class MaintainerOnlyNeverAutoCloses(GitRepoTestCase):
    def test_a_maintainer_only_match_never_auto_closes_regardless_of_shape(self):
        # Shaped like a real historical relocation record would be: a long, verbatim block moved
        # into maintainer-only material, on a base taken *after* that relocation's own anchor.
        relocated = 'This whole paragraph relocated verbatim into maintainer-only material during the edit.'
        base_sha = self.base({'SKILL.md': relocated + '\n'}, [rule('SKILL.md:1')])
        self.candidate({'SKILL.md': FILLER, 'MAINTAINING.md': relocated + '\n'})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('auto-matched', result.stdout)
        self.assertIn('removed unit with no disposition', result.stdout + result.stderr)


class LeakShapedNoteRefused(GitRepoTestCase):
    def test_a_bare_decision_shaped_token_in_a_note_is_refused(self):
        cut = 'A sentence gets a note that accidentally cites an internal record by id.'
        base_sha = self.base({HOME_X: cut + '\n' + FILLER}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: FILLER})
        leak_shaped = 'blocked by ' + 'D' + '-11 already, see the record'
        self.write_dispositions([record(HOME_X, 1, cut, 'ruled', note=leak_shaped)])
        result = self.run_tool(base_sha)
        self.assertIn(result.returncode, (1, 2))
        self.assertIn('error:', result.stdout + result.stderr)

    def test_the_literal_initiative_slug_in_a_dropped_reason_is_refused(self):
        removed = 'Every session must record the outcome before the reviewer closes it.'
        new_text = 'Every session must record the outcome before closing it.\n'
        base_sha = self.base({HOME_X: removed + '\n', HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER + new_text})
        leak_slug = 'seen while working the ' + 'tackle' + '-9 initiative'
        self.write_dispositions([record(HOME_X, 1, removed, 'reworded', destination=HOME_Y, note=new_text.strip(),
                                         dropped=[{'token': 'reviewer', 'reason': leak_slug}])])
        result = self.run_tool(base_sha)
        self.assertIn(result.returncode, (1, 2))
        self.assertIn('error:', result.stdout + result.stderr)


class FrontmatterLineChanged(GitRepoTestCase):
    def test_a_changed_frontmatter_line_with_no_record_fails(self):
        body = 'The body sentence stays exactly the same across both revisions of this file.\n'
        base_sha = self.base({HOME_X: '---\ndescription: v1\n---\n' + body}, [rule('%s:3' % HOME_X)])
        self.candidate({HOME_X: '---\ndescription: v2\n---\n' + body})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 1)
        self.assertIn('removed unit with no disposition: %s:2' % HOME_X, result.stdout + result.stderr)

    def test_the_same_changed_frontmatter_line_with_a_record_passes(self):
        body = 'The body sentence stays exactly the same across both revisions of this file.\n'
        base_sha = self.base({HOME_X: '---\ndescription: v1\n---\n' + body}, [rule('%s:3' % HOME_X)])
        self.candidate({HOME_X: '---\ndescription: v2\n---\n' + body})
        self.write_dispositions([record(HOME_X, 2, 'description: v1', 'reworded', destination=HOME_X, note='description: v2')])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class FrontmatterChangeNeverGlomsWithBody(unittest.TestCase):
    """The frontmatter analogue of a table row: one atomic line is its own unit, never combined
    with a neighboring body sentence -- checked directly against the removed-unit multiset itself,
    not only through the CLI's exit code."""

    def test_the_removed_unit_is_the_frontmatter_line_alone(self):
        body = 'The body sentence stays exactly the same across both revisions of this file.\n'
        base_text = '---\ndescription: v1\n---\n' + body
        candidate_text = '---\ndescription: v2\n---\n' + body
        removed = tool.removed_units_for_file(base_text, candidate_text)
        self.assertEqual([text for _, text in removed], ['description: v1'])


class BlankFrontmatterLineIsNotAUnit(GitRepoTestCase):
    def test_a_blank_frontmatter_line_removed_between_revisions_contributes_no_unit(self):
        body = 'The body sentence stays exactly the same across both revisions of this file.\n'
        base_sha = self.base({HOME_X: '---\ndescription: same value throughout\n\n---\n' + body}, [rule('%s:3' % HOME_X)])
        self.candidate({HOME_X: '---\ndescription: same value throughout\n---\n' + body})
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('void', result.stdout + result.stderr)
        self.assertNotIn('removed unit with no disposition', result.stdout + result.stderr)


class Restoration(GitRepoTestCase):
    def test_a_same_file_verbatim_restoration_needs_no_record_at_all(self):
        restored = 'A rule sentence is removed and then restored verbatim in the very same file.'
        base_sha = self.base({HOME_X: restored + '\n' + FILLER}, [rule('%s:1' % HOME_X)])
        self.candidate({HOME_X: FILLER + restored + '\n'})  # still present, just reordered
        self.write_dispositions([])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('removed unit with no disposition', result.stdout + result.stderr)

    def test_a_cross_file_verbatim_restoration_is_recorded_as_merged(self):
        restored = 'A rule sentence is removed from one file and restored verbatim in another.'
        base_sha = self.base({HOME_X: restored + '\n' + FILLER, HOME_Y: FILLER}, [rule('%s:1' % HOME_X), rule('%s:1' % HOME_Y)])
        self.candidate({HOME_X: FILLER, HOME_Y: FILLER + restored + '\n'})
        self.write_dispositions([record(HOME_X, 1, restored, 'merged', destination=HOME_Y, destination_unit_sha256=sha(restored))])
        result = self.run_tool(base_sha)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class MirrorResolutionLimits(unittest.TestCase):
    """check_ledger.py's own mirrors_ok only checks that a mirrors path *resolves*, never that its
    cited line still holds the expected content -- so a restoration's line-count shift can silently
    strand a mirror citation with nothing in check_ledger able to catch it either way. This is the
    test-local illustration of that limitation. The content helper below is not production
    enforcement and does not close the gate's gap."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def content_matches(self, path, line, fragment):
        text = path.read_text(encoding='utf-8').splitlines()
        return len(text) >= line and fragment in text[line - 1]

    def test_resolved_mirror_can_point_to_shifted_content(self):
        mirror_file = self.root / 'Y.md'
        mirror_file.write_text('line one\nline two\nMIRROR-FRAGMENT-HERE stays right on this line\n', encoding='utf-8')
        # check_ledger.py's own mirrors_ok/files.place logic: a mirrors path "resolves" whenever the
        # cited line number exists in the file, regardless of what text is actually there.
        sys.path.insert(0, str(HERE))
        import check_ledger
        files = check_ledger.Files(self.root)
        path, _ = files.place('Y.md:3')
        self.assertIsNotNone(path)  # resolves cleanly: the line exists
        self.assertEqual(check_ledger.mirrors_ok(files, {'mirrors': ['Y.md:3']}, False), (True, None))
        self.assertTrue(self.content_matches(mirror_file, 3, 'MIRROR-FRAGMENT-HERE'))

        # A restoration inserts a new line above the mirror, shifting the true fragment down to
        # line 4; the ledger citation is left un-re-pinned at Y.md:3 (the mistake this guards
        # against in an external content check, not in mirrors_ok).
        mirror_file.write_text('line one\nline two\na newly restored line lands right here\n'
                                'MIRROR-FRAGMENT-HERE stays right on this line\n', encoding='utf-8')
        path, _ = files.place('Y.md:3')
        self.assertIsNotNone(path)  # check_ledger alone still resolves the path: no error raised
        self.assertEqual(check_ledger.mirrors_ok(files, {'mirrors': ['Y.md:3']}, False), (True, None))
        self.assertFalse(self.content_matches(mirror_file, 3, 'MIRROR-FRAGMENT-HERE'))  # but the content check catches it

        # Re-pinning the citation to the shifted line restores agreement.
        self.assertTrue(self.content_matches(mirror_file, 4, 'MIRROR-FRAGMENT-HERE'))


class RealDataEquivalenceFrozen(unittest.TestCase):
    """references/guides/plan-card.md at two already-reviewed, now-immutable historical revisions
    of this repository: the real removed set equals exactly five known sentences, by hash, safe
    forever -- captured with `git show` at test time, never a live-repository read, and never a
    committed snapshot, matching this repository's own established fixture convention."""

    OLD_REVISION = '8185ab1'
    NEW_REVISION = '849521a'
    EXPECTED_HASHES = {
        '4227f7f0af1fb850ce26ac81407a9e0b5f74636d14b0e5d52e7cb8ece5155c0e',
        'acd0ce01f7b96d83cb77b4af9efcbfecab77e215a6e1d133025dce960e9be203',
        'e475fb074c751262afb7b8c894a4ec3eb66945f00771b846b1f93ebc20d210d7',
        'a8b8d842d029afb6d67aa142637d5911e44f3013d5f3996ed56a2c20cd17341a',
        'e6f5fcb6789688b122f9abb001a62fa55a0d9b449046f4893cae035fb5c001c2',
    }

    def git_show(self, revision):
        path = revision_path(REPO, revision, 'references/guides/plan-card.md')
        result = subprocess.run(['git', '-C', str(REPO), 'show', '%s:%s' % (revision, path)],
                                 capture_output=True, text=True, check=True)
        return result.stdout

    def test_the_five_reworded_whole_guide_link_sentences_are_exactly_the_removed_set(self):
        old_text = self.git_show(self.OLD_REVISION)
        new_text = self.git_show(self.NEW_REVISION)
        removed = tool.removed_units_for_file(old_text, new_text)
        self.assertEqual(len(removed), 5)
        self.assertEqual({tool.sha(text) for _, text in removed}, self.EXPECTED_HASHES)


class LeakScanCoversTheWholeFileNotJustAboveTheGuard(unittest.TestCase):
    """The guard below only scans this file's source up to its own class line, so anything appended
    after it would escape that scan entirely. This test scans the whole file instead, excluding only
    the lines holding the guard's own pattern definitions (located by content, never by line number
    or by class name), so a leak placed anywhere in this file -- including below the guard -- is
    still caught. The existing guard itself is not modified."""

    def test_no_case_label_or_decision_shaped_token_anywhere_in_this_file(self):
        source = Path(__file__).read_text(encoding='utf-8')
        case_label = re.compile(r'(?<![A-Za-z0-9_])[Cc][0-9]{1,2}(?![0-9])')
        decision_shaped = re.compile(r'(?<![A-Za-z])[PTDQRCM]-[0-9]{2}(?!:)')
        scanned = ''.join(line for line in source.splitlines(keepends=True) if 're.compile(' not in line)
        self.assertEqual(case_label.findall(scanned), [])
        self.assertEqual(decision_shaped.findall(scanned), [])


class NoLeakInCommittedTestNames(unittest.TestCase):
    """This file's own method names and docstrings carry no bare case label and no token shaped
    like an internal plan, task or decision id -- checked mechanically, on this file's own
    committed source."""

    def test_no_case_label_or_decision_shaped_token_in_this_files_own_source(self):
        source = Path(__file__).read_text(encoding='utf-8')
        case_label = re.compile(r'(?<![A-Za-z0-9_])[Cc][0-9]{1,2}(?![0-9])')
        decision_shaped = re.compile(r'(?<![A-Za-z])[PTDQRCM]-[0-9]{2}(?!:)')
        # The pattern-definition lines above necessarily spell out shapes like "C[0-9]" or
        # "[PTDQRCM]-" as regex source, not as a live case label or id; exempt only this method's
        # own enclosing class from the scan, exactly as the sibling leak-hygiene test elsewhere in
        # this repository exempts its own file for the same reason.
        self_class_start = source.index('class NoLeakInCommittedTestNames')
        scanned = source[:self_class_start]
        self.assertEqual(case_label.findall(scanned), [])
        self.assertEqual(decision_shaped.findall(scanned), [])


if __name__ == '__main__':
    unittest.main()
