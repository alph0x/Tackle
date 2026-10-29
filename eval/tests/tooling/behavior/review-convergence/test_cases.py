"""Review-convergence oracle cases: each fault variant fails and each alternative passes through judge().

Expected verdicts come from cases.json, never from the fixture directory name.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCORER = ROOT / 'eval/behavior/review_convergence/scorer.py'
CATALOG = ROOT / 'eval/behavior/review_convergence/cases.json'
FIXTURES = ROOT / 'eval/behavior/review_convergence/fixtures'
CASE_NAMES = ['repeated_finding', 'correction_regression', 'sensitive_markdown', 'counter_evidence',
              'unrun_phases', 'security_regression', 'unreachable_acceptance', 'unbounded_preparation']
NEUTRAL_FORBIDDEN = ('fault', 'alternative', 'pass', 'fail')


def load_scorer():
    spec = importlib.util.spec_from_file_location('review_convergence_scorer', SCORER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_catalog():
    return json.loads(CATALOG.read_text(encoding='utf-8'))


class CaseOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scorer = load_scorer()
        cls.catalog = load_catalog()

    def variants(self, case, expect):
        return [name for name, spec in self.catalog['cases'][case]['variants'].items() if spec['expect'] == expect]

    def assert_variant(self, case, name, expect):
        result = self.scorer.judge(FIXTURES / case / name)
        self.assertEqual(result['verdict'], expect, result)
        if expect == 'fail':
            self.assertTrue(result['reasons'], result)
        else:
            self.assertEqual(result['reasons'], [], result)

    def assert_variants(self, case, expect):
        names = self.variants(case, expect)
        self.assertTrue(names, 'cases.json lists no %s variant for %s' % (expect, case))
        for name in names:
            with self.subTest(variant=name):
                self.assert_variant(case, name, expect)

    def test_repeated_finding_rejects_fault(self):
        self.assert_variants('repeated_finding', 'fail')

    def test_repeated_finding_accepts_alternative(self):
        self.assert_variants('repeated_finding', 'pass')

    def test_correction_regression_rejects_fault(self):
        self.assert_variants('correction_regression', 'fail')

    def test_correction_regression_accepts_alternative(self):
        self.assert_variants('correction_regression', 'pass')

    def test_sensitive_markdown_rejects_fault(self):
        self.assert_variants('sensitive_markdown', 'fail')

    def test_sensitive_markdown_accepts_alternative(self):
        self.assert_variants('sensitive_markdown', 'pass')

    def test_counter_evidence_rejects_fault(self):
        self.assert_variants('counter_evidence', 'fail')

    def test_counter_evidence_accepts_alternative(self):
        self.assert_variants('counter_evidence', 'pass')

    def test_unrun_phases_rejects_fault(self):
        self.assert_variants('unrun_phases', 'fail')

    def test_unrun_phases_accepts_alternative(self):
        self.assert_variants('unrun_phases', 'pass')

    def test_security_regression_rejects_fault(self):
        self.assert_variants('security_regression', 'fail')

    def test_security_regression_rejects_fault_literal(self):
        self.assert_variant('security_regression', 'v06', 'fail')

    def test_security_regression_rejects_fault_sniff(self):
        self.assert_variant('security_regression', 'v07', 'fail')

    def test_security_regression_accepts_alternative(self):
        self.assert_variants('security_regression', 'pass')

    def test_unreachable_acceptance_rejects_fault(self):
        self.assert_variants('unreachable_acceptance', 'fail')

    def test_unreachable_acceptance_accepts_alternative(self):
        self.assert_variants('unreachable_acceptance', 'pass')

    def test_unbounded_preparation_rejects_fault(self):
        self.assert_variants('unbounded_preparation', 'fail')

    def test_unbounded_preparation_accepts_alternative(self):
        self.assert_variants('unbounded_preparation', 'pass')


class CatalogStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_catalog_lists_the_eight_measurement_cases(self):
        self.assertEqual(sorted(self.catalog['cases']), sorted(CASE_NAMES))

    def test_each_case_has_two_faults_and_two_alternatives(self):
        for case in CASE_NAMES:
            expects = [spec['expect'] for spec in self.catalog['cases'][case]['variants'].values()]
            with self.subTest(case=case):
                self.assertGreaterEqual(expects.count('fail'), 2)
                self.assertGreaterEqual(expects.count('pass'), 2)

    def test_variant_names_are_neutral_and_match_the_directories(self):
        for case in CASE_NAMES:
            names = sorted(self.catalog['cases'][case]['variants'])
            with self.subTest(case=case):
                for name in names:
                    self.assertFalse([word for word in NEUTRAL_FORBIDDEN if word in name], name)
                on_disk = sorted(path.name for path in (FIXTURES / case).iterdir())
                self.assertEqual(on_disk, names)


if __name__ == '__main__':
    unittest.main()
