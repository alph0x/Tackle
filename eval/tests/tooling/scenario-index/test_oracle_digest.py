"""The scenario index seals each scenario's answer sheets and oracle directories with ``oracle_sha256``.

Guarantee: an entry's ``oracle_sha256`` is the tree digest of its root answer sheet, every variant answer
sheet and every file under a variant's ``oracle/`` directory; the checker rejects drift, a null beside an
existing oracle directory, a digest with no oracle directory, and a held-out variant whose oracle digest
was not committed strictly before the first record naming it. Legacy entries without oracle files carry a
null (or no field) and stay valid. Repositories here are synthetic and built in temporary directories.
"""
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_index as base

SCENARIO = 's1-trap'
ORACLE_SET = re.compile(r'(GROUND-TRUTH\.md|variants/[^/]+/GROUND-TRUTH\.md|variants/[^/]+/oracle/.+)')


class OracleRepo(base.Repo):
    """The shared index fixture, with s1-trap's two held-out variants carrying oracle directories."""

    def __init__(self, case, sealed_oracle=True):
        self.sealed_oracle = sealed_oracle
        super().__init__(case)

    def oracle_files(self, scenario):
        prefix = 'eval/scenarios/%s/' % scenario
        return {path[len(prefix):]: text.encode() for path, text in self.files.items()
                if path.startswith(prefix) and ORACLE_SET.fullmatch(path[len(prefix):])}

    def seal(self):
        super().seal()
        for variant in ('h1', 'h2'):
            prefix = 'eval/scenarios/%s/variants/%s/oracle/' % (SCENARIO, variant)
            self.files[prefix + 'check.py'] = '# oracle for %s\n' % variant
            self.files[prefix + 'selftest/fell/final/notes.md'] = 'a final tree for %s\n' % variant
        for entry in self.entries:
            has_oracle = any('/oracle/' in '/' + path for path in self.oracle_files(entry['scenario_id']))
            entry['oracle_sha256'] = (base.digest(self.oracle_files(entry['scenario_id']))
                                      if has_oracle and self.sealed_oracle else None)


class OracleDigestTests(unittest.TestCase):
    def assertValid(self, repo):
        code, out, err = base.check(repo.root)
        self.assertEqual((code, err), (0, ''), out)
        self.assertEqual(out.splitlines(), [base.SUMMARY])

    def assertRejected(self, repo, *fragments):
        code, out, err = base.check(repo.root)
        self.assertEqual(code, 1, out + err)
        self.assertNotIn('Traceback', err)
        errors = [line for line in out.splitlines() if line.startswith('error: ')]
        for fragment in fragments:
            self.assertTrue(any(fragment in line for line in errors), (fragment, errors))

    def test_oracle_digest_matches(self):
        repo = OracleRepo(self)
        self.assertIsNotNone(repo.entry(SCENARIO)['oracle_sha256'])
        self.assertValid(repo)

    def test_oracle_digest_drift_fails(self):
        for target in ('variants/h1/oracle/check.py', 'GROUND-TRUTH.md', 'variants/h2/GROUND-TRUTH.md'):
            with self.subTest(target=target):
                repo = OracleRepo(self)
                path = repo.root / 'eval/scenarios' / SCENARIO / target
                path.write_text(path.read_text() + 'drift\n')
                self.assertRejected(repo, 'error: %s: digest: oracle_sha256' % SCENARIO)

    def test_null_oracle_digest_with_oracle_directory_fails(self):
        repo = OracleRepo(self, sealed_oracle=False)
        self.assertIsNone(repo.entry(SCENARIO)['oracle_sha256'])
        self.assertRejected(repo, 'error: %s: digest: oracle_sha256' % SCENARIO)

    def test_oracle_digest_without_oracle_directory_fails(self):
        repo = OracleRepo(self)
        repo.entry('s20-proc')['oracle_sha256'] = base.digest(repo.oracle_files('s20-proc'))
        repo.write_all(seal=False)
        self.assertRejected(repo, 'error: s20-proc: digest: oracle_sha256')

    def test_legacy_entry_with_null_oracle_digest_passes(self):
        repo = OracleRepo(self)
        legacy = repo.entry('s20-proc')
        self.assertIsNone(legacy['oracle_sha256'])
        self.assertValid(repo)
        del legacy['oracle_sha256']
        repo.write_all(seal=False)
        self.assertValid(repo)

    def test_oracle_seal_order(self):
        passing = OracleRepo(self)
        passing.cohort([(SCENARIO, 'h1')])
        passing.commit('records after the oracle seal')
        self.assertValid(passing)

        together = OracleRepo(self, sealed_oracle=False)
        together.cohort([(SCENARIO, 'h1')])
        together.sealed_oracle = True
        together.write_all()
        together.commit('oracle seal with the first record')
        self.assertRejected(together, '%s/h1: seal:' % SCENARIO)

        later = OracleRepo(self, sealed_oracle=False)
        later.cohort([(SCENARIO, 'h1')])
        later.commit('records first')
        later.sealed_oracle = True
        later.write_all()
        later.commit('oracle seal after the records')
        self.assertRejected(later, '%s/h1: seal:' % SCENARIO)


if __name__ == '__main__':
    unittest.main()
