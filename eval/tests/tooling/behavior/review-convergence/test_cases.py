"""Review-convergence oracle cases: each planted fault fails and each valid alternative passes through judge()."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCORER = ROOT / 'eval/behavior/review_convergence/scorer.py'
FIXTURES = ROOT / 'eval/behavior/review_convergence/fixtures'


def load_scorer():
    spec = importlib.util.spec_from_file_location('review_convergence_scorer', SCORER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaseOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scorer = load_scorer()

    def judge(self, case, side):
        return self.scorer.judge(FIXTURES / case / side)

    def assert_rejects(self, case):
        result = self.judge(case, 'fault')
        self.assertEqual(result['verdict'], 'fail', result)
        self.assertTrue(result['reasons'], result)

    def assert_accepts(self, case):
        result = self.judge(case, 'alternative')
        self.assertEqual(result['verdict'], 'pass', result)

    def test_repeated_finding_rejects_fault(self):
        self.assert_rejects('repeated_finding')

    def test_repeated_finding_accepts_alternative(self):
        self.assert_accepts('repeated_finding')

    def test_correction_regression_rejects_fault(self):
        self.assert_rejects('correction_regression')

    def test_correction_regression_accepts_alternative(self):
        self.assert_accepts('correction_regression')

    def test_sensitive_markdown_rejects_fault(self):
        self.assert_rejects('sensitive_markdown')

    def test_sensitive_markdown_accepts_alternative(self):
        self.assert_accepts('sensitive_markdown')

    def test_counter_evidence_rejects_fault(self):
        self.assert_rejects('counter_evidence')

    def test_counter_evidence_accepts_alternative(self):
        self.assert_accepts('counter_evidence')

    def test_unrun_phases_rejects_fault(self):
        self.assert_rejects('unrun_phases')

    def test_unrun_phases_accepts_alternative(self):
        self.assert_accepts('unrun_phases')

    def test_security_regression_rejects_fault(self):
        self.assert_rejects('security_regression')

    def test_security_regression_accepts_alternative(self):
        self.assert_accepts('security_regression')

    def test_unreachable_acceptance_rejects_fault(self):
        self.assert_rejects('unreachable_acceptance')

    def test_unreachable_acceptance_accepts_alternative(self):
        self.assert_accepts('unreachable_acceptance')

    def test_unbounded_preparation_rejects_fault(self):
        self.assert_rejects('unbounded_preparation')

    def test_unbounded_preparation_accepts_alternative(self):
        self.assert_accepts('unbounded_preparation')


if __name__ == '__main__':
    unittest.main()
