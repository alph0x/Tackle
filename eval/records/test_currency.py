"""Record currency: every claim is classified, every record is tracked, pinned and free of leaks.

``check_currency.py`` and ``sanitize.py`` are driven by subprocess, the way CI runs them, over git
repositories built here in temporary directories. Nothing is written inside this repository.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / 'eval/records/check_currency.py'
SANITIZER = ROOT / 'eval/records/sanitize.py'
COHORTS = ROOT / 'eval/protocol-v2/fixtures'
WORKFLOW = ROOT / '.github/workflows/ci.yml'
RECORD = 'eval/runs/2026-01-01-s9-demo.md'
NOTE = 'note: deterministic checks verify records, fixtures and harnesses, not agent behavior'
KEY_HEADER = '-----BEGIN ' + 'RSA PRIVATE ' + 'KEY-----'  # assembled so secret scanners see no key block
GIT_ENV = {'GIT_AUTHOR_NAME': 'fixture', 'GIT_AUTHOR_EMAIL': 'fixture@invalid', 'GIT_COMMITTER_NAME': 'fixture',
           'GIT_COMMITTER_EMAIL': 'fixture@invalid', 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def summary(**counts):
    base = dict(records=1, tracked=1, local_only=0, claims=2, record=1, cohort=0, no_record=0, mention=1, retired=0)
    base.update(counts)
    return ' '.join('%s=%d' % item for item in base.items())


class Repo:
    """A disposable git repository shaped like the parts of this one the checker reads."""

    def __init__(self, case):
        self.temporary = tempfile.TemporaryDirectory(prefix='tackle-records-')
        case.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'repo'
        self.root.mkdir()
        self.git('init', '-q')
        self.files = {
            'CHANGELOG.md': '# Changelog\n\n## Tackle 1.0.0\n\n- The s9 trap discriminates in one seed.\n',
            'README.md': '# Demo\n\n## Evaluation\n\nThe catalog holds s9.\n',
            'eval/scenarios/s9-demo/GROUND-TRUTH.md': 'answer sheet\n',
            RECORD: 'verdict: discriminates\n',
            'eval/rules/historical-index.json': None,
        }
        self.index = {RECORD: ['s9-demo']}
        self.hashes = {}
        self.claims = [
            dict(source='CHANGELOG.md', section='Tackle 1.0.0', unit='s9', kind='record', records=[RECORD]),
            dict(source='README.md', section='Evaluation', unit='s9', kind='mention', reason='catalog listing'),
        ]
        self.pin(RECORD, recorded_on='2026-01-01')
        self.write_all()
        self.commit('2026-01-05T12:00:00Z')
        self.git('tag', '-a', '-m', 'v1.0.0', 'v1.0.0', env={'GIT_COMMITTER_DATE': '2026-01-05T12:00:00Z'})

    def git(self, *args, env=None, check=True):
        full = dict(os.environ, **GIT_ENV, **(env or {}))
        return subprocess.run(['git', '-C', str(self.root)] + list(args), capture_output=True, text=True, env=full,
                              check=check)

    def pin(self, path, recorded_on, tracked=True, retired=(), **extra):
        data = self.files[path].encode()
        self.hashes[path] = dict(sha256=sha(data), bytes=len(data), tracked=tracked, recorded_on=recorded_on,
                                 retired_scenarios=list(retired), **extra)

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def write_all(self):
        self.files['eval/rules/historical-index.json'] = json.dumps(dict(
            schema='tackle-historical-index/1',
            records={path: [dict(scenario_id=s) for s in scenarios] for path, scenarios in self.index.items()}))
        for path, text in self.files.items():
            self.write(path, text)
        self.write('eval/records/historical-hashes.json',
                   json.dumps(dict(schema='tackle-historical-hashes/1', records=self.hashes), indent=1))
        self.write('eval/records/claims.json',
                   json.dumps(dict(schema='tackle-claims/1', gate_version='1.0.0', claims=self.claims), indent=1))

    def stage(self):
        self.write_all()
        self.git('add', '-A')

    def commit(self, when):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'fixture', env={'GIT_AUTHOR_DATE': when, 'GIT_COMMITTER_DATE': when})

    def tree(self):
        return {str(p.relative_to(self.root)): sha(p.read_bytes()) for p in sorted(self.root.rglob('*'))
                if p.is_file() and '.git' not in p.relative_to(self.root).parts}


def check(root):
    child = subprocess.run([sys.executable, str(CHECKER), '--repo', str(root)], capture_output=True, text=True,
                           timeout=60)
    return child.returncode, child.stdout, child.stderr


class CheckerTests(unittest.TestCase):
    def assertValid(self, repo, expected):
        code, out, err = check(repo.root)
        self.assertEqual((code, err), (0, ''), out)
        lines = out.splitlines()
        self.assertEqual(lines[0], expected)
        self.assertEqual(lines[-1], NOTE)
        return lines

    def assertRejected(self, repo, *fragments):
        code, out, err = check(repo.root)
        self.assertEqual(code, 1, out + err)
        errors = [line for line in out.splitlines() if line.startswith('error: ')]
        self.assertTrue(errors, out)
        for fragment in fragments:
            self.assertTrue(any(fragment in line for line in errors), (fragment, errors))
        self.assertNotIn(NOTE, out)

    def test_minimal_repository_is_current(self):
        self.assertValid(Repo(self), summary())

    def test_edited_record_fails(self):
        repo = Repo(self)
        repo.files[RECORD] += 'x'
        repo.stage()
        self.assertRejected(repo, RECORD + ': hash:')

    def test_untracked_record_fails(self):
        repo = Repo(self)
        path = 'eval/runs/2026-01-02-s9-demo.md'
        repo.files[path] = 'second record\n'
        repo.pin(path, recorded_on='2026-01-02')
        repo.stage()
        repo.git('rm', '-q', '--cached', path)
        self.assertRejected(repo, path + ': untracked:')

    def test_unledgered_record_fails(self):
        repo = Repo(self)
        repo.files['eval/runs/2026-01-03-extra.md'] = 'extra\n'
        repo.stage()
        self.assertRejected(repo, 'eval/runs/2026-01-03-extra.md: unledgered:')

    def test_index_record_without_entry_fails(self):
        repo = Repo(self)
        repo.index['eval/runs/2026-01-04-s9-demo.md'] = ['s9-demo']
        repo.stage()
        self.assertRejected(repo, 'eval/runs/2026-01-04-s9-demo.md: unledgered:')

    def test_claim_without_entry_fails(self):
        repo = Repo(self)
        repo.files['CHANGELOG.md'] += '- The s8 trap fell for the control.\n'
        repo.stage()
        self.assertRejected(repo, 'unmapped:')

    def test_duplicate_claim_fails(self):
        repo = Repo(self)
        repo.claims.append(dict(repo.claims[1]))
        repo.stage()
        self.assertRejected(repo, 'duplicate:')

    def test_stale_claim_fails(self):
        repo = Repo(self)
        repo.claims.append(dict(source='README.md', section='Evaluation', unit='s7', kind='mention', reason='gone'))
        repo.stage()
        self.assertRejected(repo, 'stale:')

    def test_record_after_release_fails(self):
        repo = Repo(self)
        path = 'eval/runs/2026-01-09-s9-demo.md'
        repo.files[path] = 'later record\n'
        repo.index[path] = ['s9-demo']
        repo.pin(path, recorded_on='2026-01-09')
        repo.claims[0]['records'] = [path]
        repo.stage()
        self.assertRejected(repo, 'record-after-release:')

    def test_record_naming_another_scenario_fails(self):
        repo = Repo(self)
        repo.files['CHANGELOG.md'] += '- The s8 trap fell for the control.\n'
        repo.files['eval/scenarios/s8-other/GROUND-TRUTH.md'] = 'answer sheet\n'
        repo.claims.append(dict(source='CHANGELOG.md', section='Tackle 1.0.0', unit='s8', kind='record',
                                records=[RECORD]))
        repo.stage()
        self.assertRejected(repo, 'wrong-scenario:')

    def test_no_record_after_the_gate_fails(self):
        repo = Repo(self)
        repo.files['CHANGELOG.md'] = repo.files['CHANGELOG.md'].replace(
            '## Tackle 1.0.0', '## Tackle 2.0.0\n\n- The s9 trap was run again.\n\n## Tackle 1.0.0')
        repo.claims.append(dict(source='CHANGELOG.md', section='Tackle 2.0.0', unit='s9', kind='no-record',
                                reason='record lost'))
        repo.stage()
        self.assertRejected(repo, 'no-record:')

    def test_no_record_at_the_gate_passes(self):
        repo = Repo(self)
        repo.claims[0] = dict(source='CHANGELOG.md', section='Tackle 1.0.0', unit='s9', kind='no-record',
                              reason='the run record was not retained')
        repo.stage()
        self.assertValid(repo, summary(record=0, no_record=1))

    def test_claim_without_reason_fails(self):
        repo = Repo(self)
        repo.claims[1]['reason'] = ''
        repo.stage()
        self.assertRejected(repo, 'mention:')

    def test_leaking_record_fails(self):
        repo = Repo(self)
        repo.files[RECORD] = 'read /Users/somebody/.tackle/cache\n'
        repo.pin(RECORD, recorded_on='2026-01-01')
        repo.stage()
        self.assertRejected(repo, RECORD + ': leak:')

    def test_leaking_claim_map_fails(self):
        repo = Repo(self)
        repo.claims[1]['reason'] = 'ask somebody@example.org'
        repo.stage()
        self.assertRejected(repo, 'eval/records/claims.json: leak:')

    def test_local_original_with_sanitized_copy_passes(self):
        repo = Repo(self)
        original = 'eval/runs/2026-01-02-s9-demo.md'
        copy = 'eval/records/sanitized/2026-01-02-s9-demo.md'
        repo.files[original] = 'read ~/.tackle/cache\n'
        repo.files[copy] = 'read <home>/.tackle/cache\n'
        repo.index[original] = ['s9-demo']
        repo.pin(original, recorded_on='2026-01-02', tracked=False, sanitized_copy=copy)
        repo.pin(copy, recorded_on='2026-01-02', source=original, source_sha256=repo.hashes[original]['sha256'])
        repo.claims[0]['records'] = [copy]
        repo.write('.gitignore', original + '\n')
        repo.stage()
        self.assertValid(repo, summary(records=3, tracked=2, local_only=1))
        (repo.root / original).unlink()
        self.assertValid(repo, summary(records=3, tracked=2, local_only=1))

    def test_tracked_original_fails(self):
        repo = Repo(self)
        original = 'eval/runs/2026-01-02-s9-demo.md'
        copy = 'eval/records/sanitized/2026-01-02-s9-demo.md'
        repo.files[original] = 'read ~/.tackle/cache\n'
        repo.files[copy] = 'read <home>/.tackle/cache\n'
        repo.index[original] = ['s9-demo']
        repo.pin(original, recorded_on='2026-01-02', tracked=False, sanitized_copy=copy)
        repo.pin(copy, recorded_on='2026-01-02', source=original, source_sha256=repo.hashes[original]['sha256'])
        repo.stage()
        self.assertRejected(repo, original + ': tracked-original:')

    def test_leak_free_original_kept_local_fails(self):
        for copy_text, keep_original in (('clean record\n', False), ('clean <home> record\n', True)):
            with self.subTest(keep_original=keep_original):
                repo = Repo(self)
                original = 'eval/runs/2026-01-02-s9-demo.md'
                copy = 'eval/records/sanitized/2026-01-02-s9-demo.md'
                repo.files[original] = 'clean record\n'
                repo.files[copy] = copy_text
                repo.index[original] = ['s9-demo']
                repo.pin(original, recorded_on='2026-01-02', tracked=False, sanitized_copy=copy)
                repo.pin(copy, recorded_on='2026-01-02', source=original, source_sha256=repo.hashes[original]['sha256'])
                repo.write('.gitignore', original + '\n')
                repo.stage()
                if not keep_original:
                    (repo.root / original).unlink()
                self.assertRejected(repo, original + ': should-be-tracked:')

    def test_sanitized_copy_of_another_original_fails(self):
        repo = Repo(self)
        original = 'eval/runs/2026-01-02-s9-demo.md'
        copy = 'eval/records/sanitized/2026-01-02-s9-demo.md'
        repo.files[original] = 'read ~/.tackle/cache\n'
        repo.files[copy] = 'read <home>/.tackle/cache\n'
        repo.index[original] = ['s9-demo']
        repo.pin(original, recorded_on='2026-01-02', tracked=False, sanitized_copy=copy)
        repo.pin(copy, recorded_on='2026-01-02', source=original, source_sha256='0' * 64)
        repo.write('.gitignore', original + '\n')
        repo.stage()
        self.assertRejected(repo, 'sanitized:')

    def test_original_naming_a_missing_copy_fails(self):
        repo = Repo(self)
        original = 'eval/runs/2026-01-02-s9-demo.md'
        repo.files[original] = 'read ~/.tackle/cache\n'
        repo.index[original] = ['s9-demo']
        repo.pin(original, recorded_on='2026-01-02', tracked=False,
                 sanitized_copy='eval/records/sanitized/2026-01-02-s9-demo.md')
        repo.write('.gitignore', original + '\n')
        repo.stage()
        self.assertRejected(repo, original + ': sanitized:')

    def test_fenced_units_are_not_claims(self):
        repo = Repo(self)
        repo.files['CHANGELOG.md'] += '\n```text\ns8 appears only in an example\n```\n'
        repo.stage()
        self.assertValid(repo, summary())

    def test_range_claimed_as_a_record_fails(self):
        repo = Repo(self)
        repo.files['CHANGELOG.md'] += '- The s9–s10 traps were run again.\n'
        repo.claims.append(dict(source='CHANGELOG.md', section='Tackle 1.0.0', unit='s9–s10', kind='record',
                                records=[RECORD]))
        repo.stage()
        self.assertRejected(repo, 'wrong-scenario:')

    def test_untracked_cohort_claim_fails(self):
        repo = Repo(self)
        cohort_id = json.loads((COHORTS / 'valid-discriminates' / 'manifest.json').read_text())['cohort_id']
        repo.files['CHANGELOG.md'] += '- The s1 trap was measured in a cohort.\n'
        repo.claims.append(dict(source='CHANGELOG.md', section='Tackle 1.0.0', unit='s1', kind='cohort',
                                cohort=cohort_id))
        repo.stage()
        shutil.copytree(COHORTS / 'valid-discriminates', repo.root / 'eval/cohorts' / cohort_id)
        self.assertRejected(repo, 'cohort:')

    def test_backdated_record_fails(self):
        repo = Repo(self)
        path = 'eval/runs/2026-01-09-s9-demo.md'
        repo.files[path] = 'later record\n'
        repo.index[path] = ['s9-demo']
        repo.pin(path, recorded_on='2026-01-04')
        repo.claims[0]['records'] = [path]
        repo.stage()
        self.assertRejected(repo, path + ': recorded-on:')

    def test_answer_sheet_record_names_its_scenario_and_date(self):
        repo = Repo(self)
        sheet = 'eval/scenarios/s9-demo/GROUND-TRUTH.md'
        repo.files[sheet] = 'answer sheet\n\n## Run record — 2026-01-03\n\nMethod avoided, read ~/.tackle/profile.\n'
        repo.pin(sheet, recorded_on='2026-01-03')
        repo.claims[0]['records'] = [sheet]
        repo.stage()
        self.assertValid(repo, summary(records=2, tracked=2))

    def test_answer_sheet_without_its_date_fails(self):
        repo = Repo(self)
        sheet = 'eval/scenarios/s9-demo/GROUND-TRUTH.md'
        repo.pin(sheet, recorded_on='2026-01-03')
        repo.stage()
        self.assertRejected(repo, sheet + ': recorded-on:')

    def test_leaking_answer_sheet_fails(self):
        repo = Repo(self)
        sheet = 'eval/scenarios/s9-demo/GROUND-TRUTH.md'
        repo.files[sheet] = 'answer sheet 2026-01-03, log at /Users/somebody/run.log\n'
        repo.pin(sheet, recorded_on='2026-01-03')
        repo.stage()
        self.assertRejected(repo, sheet + ': leak:')

    def test_outcome_claimed_as_mention_after_the_gate_fails(self):
        for source, section, line in (('CHANGELOG.md', 'Tackle 2.0.0', '- s9 discriminates in a new run.\n'),
                                      ('README.md', 'Evaluation', 'The s9 control fell.\n')):
            with self.subTest(source=source):
                repo = Repo(self)
                if source == 'README.md':
                    repo.files[source] += line
                    repo.claims[1]['reason'] = 'catalog listing'
                else:
                    repo.files[source] = repo.files[source].replace('## Tackle 1.0.0', '## Tackle 2.0.0\n\n' + line + '\n## Tackle 1.0.0')
                    repo.claims.append(dict(source=source, section=section, unit='s9', kind='mention', reason='named'))
                repo.stage()
                self.assertRejected(repo, 'mention-outcome:')

    def test_staged_bytes_are_checked_not_the_working_tree(self):
        repo = Repo(self)
        good = repo.files[RECORD]
        repo.files[RECORD] += 'x'
        repo.stage()
        repo.write(RECORD, good)
        self.assertRejected(repo, RECORD + ': hash:')

    def test_untracked_claim_map_fails(self):
        repo = Repo(self)
        repo.git('rm', '-q', '--cached', 'eval/records/claims.json')
        self.assertRejected(repo, 'eval/records/claims.json: untracked:')

    def test_changed_local_original_fails(self):
        repo = Repo(self)
        original = 'eval/runs/2026-01-02-s9-demo.md'
        copy = 'eval/records/sanitized/2026-01-02-s9-demo.md'
        repo.files[original] = 'read ~/.tackle/cache\n'
        repo.files[copy] = 'read <home>/.tackle/cache\n'
        repo.index[original] = ['s9-demo']
        repo.pin(original, recorded_on='2026-01-02', tracked=False, sanitized_copy=copy)
        repo.pin(copy, recorded_on='2026-01-02', source=original, source_sha256=repo.hashes[original]['sha256'])
        repo.write('.gitignore', original + '\n')
        repo.stage()
        repo.write(original, 'read ~/.tackle/cache, edited\n')
        self.assertRejected(repo, original + ': hash:')

    def test_cohort_without_the_scenario_fails(self):
        repo = Repo(self)
        cohort_id = json.loads((COHORTS / 'valid-discriminates' / 'manifest.json').read_text())['cohort_id']
        shutil.copytree(COHORTS / 'valid-discriminates', repo.root / 'eval/cohorts' / cohort_id)
        repo.files['CHANGELOG.md'] += '- The s8 trap was measured in a cohort.\n'
        repo.claims.append(dict(source='CHANGELOG.md', section='Tackle 1.0.0', unit='s8', kind='cohort',
                                cohort=cohort_id))
        repo.stage()
        self.assertRejected(repo, 'cohort:')

    def test_retired_scenario_is_reported(self):
        repo = Repo(self)
        repo.index[RECORD] = ['s9-demo', 's8-gone']
        repo.pin(RECORD, recorded_on='2026-01-01', retired=['s8-gone'])
        repo.stage()
        lines = self.assertValid(repo, summary(retired=1))
        self.assertIn('retired: %s: s8-gone' % RECORD, lines)

    def test_unlisted_retired_scenario_fails(self):
        repo = Repo(self)
        repo.index[RECORD] = ['s9-demo', 's8-gone']
        repo.stage()
        self.assertRejected(repo, RECORD + ': retired:')

    def test_cohort_claims(self):
        for fixture, valid in (('valid-discriminates', True), ('bad-chain', False)):
            with self.subTest(fixture=fixture):
                repo = Repo(self)
                cohort_id = json.loads((COHORTS / fixture / 'manifest.json').read_text())['cohort_id']
                shutil.copytree(COHORTS / fixture, repo.root / 'eval/cohorts' / cohort_id)
                repo.files['CHANGELOG.md'] += '- The s1 trap was measured in a cohort.\n'
                repo.claims.append(dict(source='CHANGELOG.md', section='Tackle 1.0.0', unit='s1',
                                        kind='cohort', cohort=cohort_id))
                repo.stage()
                if valid:
                    self.assertValid(repo, summary(claims=3, cohort=1))
                else:
                    self.assertRejected(repo, 'cohort:')

    def test_repository_without_tags_fails(self):
        repo = Repo(self)
        repo.git('tag', '-d', 'v1.0.0')
        self.assertRejected(repo, 'tags-missing:')

    def test_invalid_hashes_schema_fails(self):
        repo = Repo(self)
        repo.stage()
        repo.write('eval/records/historical-hashes.json', json.dumps(dict(schema='other', records={})))
        repo.git('add', '-A')
        self.assertRejected(repo, 'schema:')

    def test_reordered_maps_give_the_same_result(self):
        repo = Repo(self)
        first = check(repo.root)
        self.assertEqual(first[0], 0, first)
        repo.claims.reverse()
        repo.hashes = dict(reversed(list(repo.hashes.items())))
        repo.stage()
        self.assertEqual(check(repo.root), first)

    def test_checker_never_writes(self):
        repo = Repo(self)
        before = repo.tree()
        self.assertEqual(check(repo.root)[0], 0)
        self.assertEqual(repo.tree(), before)
        repo.files[RECORD] += 'x'
        repo.stage()
        staged = repo.tree()
        self.assertEqual(check(repo.root)[0], 1)
        self.assertEqual(repo.tree(), staged)

    def test_usage_errors_exit_2(self):
        repo = Repo(self)
        with tempfile.TemporaryDirectory() as plain:
            for argv in ([], ['--repo'], ['--repo', plain], ['--repo', str(repo.root), 'extra'], ['--other', str(repo.root)]):
                with self.subTest(argv=argv):
                    child = subprocess.run([sys.executable, str(CHECKER)] + argv, capture_output=True, text=True)
                    self.assertEqual(child.returncode, 2, child.stdout + child.stderr)
                    self.assertIn('usage: check_currency.py', child.stderr)


class SanitizerTests(unittest.TestCase):
    def run_sanitizer(self, text, existing=None):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-sanitize-')
        self.addCleanup(temporary.cleanup)
        source, target = Path(temporary.name) / 'in.md', Path(temporary.name) / 'out.md'
        source.write_text(text)
        if existing is not None:
            target.write_text(existing)
        child = subprocess.run([sys.executable, str(SANITIZER), str(source), str(target)], capture_output=True,
                               text=True)
        return child, source, target

    def test_recognized_leaks_are_replaced(self):
        text = 'read /Users/alice/p and ~/.tackle/x, mail bob@example.com, key sk-%s\n' % ('a' * 24)
        child, source, target = self.run_sanitizer(text)
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertEqual(source.read_text(), text)
        result = target.read_text()
        self.assertEqual(result, 'read <home>/p and <home>/.tackle/x, mail <email>, key <secret>\n')
        self.assertIn('replacements=4', child.stdout)
        self.assertIn(sha(target.read_bytes()), child.stdout)

    def test_private_key_is_refused(self):
        child, _, target = self.run_sanitizer(KEY_HEADER + '\nabc\n')
        self.assertEqual(child.returncode, 1)
        self.assertIn('private-key block', child.stderr)
        self.assertFalse(target.exists())

    def test_unrecognized_leak_is_refused(self):
        child, _, target = self.run_sanitizer('scratch at /private/tmp/run-1\n')
        self.assertEqual(child.returncode, 1)
        self.assertIn('unrecognized leak remains', child.stderr)
        self.assertFalse(target.exists())

    def test_existing_destination_is_refused(self):
        child, _, target = self.run_sanitizer('/home/x/y\n', existing='keep\n')
        self.assertEqual(child.returncode, 1)
        self.assertIn('destination exists', child.stderr)
        self.assertNotIn('Traceback', child.stderr)
        self.assertEqual(target.read_text(), 'keep\n')

    def test_usage_error_exits_2(self):
        child = subprocess.run([sys.executable, str(SANITIZER)], capture_output=True, text=True)
        self.assertEqual(child.returncode, 2)
        self.assertIn('usage: sanitize.py', child.stderr)


class WorkflowTests(unittest.TestCase):
    def test_ci_fetches_tags_installs_every_awk_and_checks_currency(self):
        text = WORKFLOW.read_text()
        self.assertRegex(text, r'fetch-depth: 0')
        self.assertIn('python3 eval/records/check_currency.py --repo .', text)
        install = re.search(r'- name: [^\n]*awk[^\n]*\n(?:(?![ ]*- )[^\n]*\n)+', text)
        self.assertIsNotNone(install, 'no awk installation step')
        for awk in ('gawk', 'mawk', 'original-awk', 'busybox'):
            self.assertIn(awk, install.group(0))
        self.assertIn('exit 1', install.group(0))
        self.assertGreaterEqual(text.count('not agent behavior'), 2)


class RepositoryTests(unittest.TestCase):
    def test_repository_is_current(self):
        code, out, err = check(ROOT)
        self.assertEqual((code, err), (0, ''), out)
        self.assertEqual(out.splitlines()[-1], NOTE)


if __name__ == '__main__':
    unittest.main()
