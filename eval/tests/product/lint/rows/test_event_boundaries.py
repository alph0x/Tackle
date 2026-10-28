# Row 16 closes lifecycle event records at real headings of levels one to three, keeps fenced lines inert,
# and keeps keys under a heading of any level counted. Each test runs the real row 16 in a disposable workspace.
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
ROWS = ROOT / 'eval/tests/product/lint/rows'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROWS))

# The sibling module owns the disposable-workspace helper and the ledger header.
import test_row_contracts as row_contracts  # noqa: E402


V2_SCHEMA = 'Schema: tackle-observability/2\n'
RUN = 'run-1'
ABSENCE = ('### Event e1\n\nTask ID: T-A\nRun ID: ' + RUN + '\n'
           'Kind: observed-absence\nObserved: nothing ran\n')
FENCE = '`' * 3


def ledger(*events):
    return V2_SCHEMA + row_contracts.HEADER + ''.join(events)


def finish_row(attempts, source, verification='n/a'):
    return ledger(row_contracts.event('start', run=RUN),
                  row_contracts.event('finish', run=RUN, attempts=attempts,
                                      verification=verification, source=source))


def correction(result='exit 1; expected valid output'):
    return ('Task ID: T-A\nEvent ID: e1\nRun ID: ' + RUN + '\nKind: correction-validation\n'
            'Failure ID: fault-alpha\nObserved failure: checker exited 1\n'
            'Correction: added the output guard\nValidation command: python3 check.py\n'
            'Result: ' + result + '\nCycle count: 1\n')


class EventBoundaryTests(unittest.TestCase):
    def assert_accepted(self, files):
        result = row_contracts.run_row(16, files)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def assert_rejected(self, files, diagnostic):
        result = row_contracts.run_row(16, files)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stderr, '')
        self.assertIn(diagnostic, result.stdout)

    def test_level_two_section_closes_event(self):
        report = ABSENCE + '\n## Phase\n\nRun ID: run-2\n'
        self.assert_accepted({'resource-usage.md': finish_row('0', 'report.md'), 'report.md': report})

    def test_level_one_section_closes_event(self):
        report = ABSENCE + '\n# Notes\n\nRun ID: run-2\n'
        self.assert_accepted({'resource-usage.md': finish_row('0', 'report.md'), 'report.md': report})

    def test_level_four_heading_stays_inside(self):
        report = ('### Event e1\n\nTask ID: T-A\nRun ID: ' + RUN + '\n\n#### Detail\n\n'
                  'Kind: observed-absence\nObserved: nothing ran\n')
        self.assert_accepted({'resource-usage.md': finish_row('0', 'report.md'), 'report.md': report})

    def test_fenced_heading_stays_inert(self):
        report = ('### Event e1\n\nTask ID: T-A\nRun ID: ' + RUN + '\nKind: observed-absence\n\n'
                  + FENCE + 'text\n### Fake\n' + FENCE + '\nObserved: nothing ran\n')
        self.assert_accepted({'resource-usage.md': finish_row('0', 'report.md'), 'report.md': report})

    def test_fenced_keys_stay_inert(self):
        history = ('### Event e1\n\nTask ID: T-A\nRun ID: run-9\nKind: correction-validation\n\n'
                   + FENCE + 'text\n### Event e1\nTask ID: T-A\nRun ID: ' + RUN + '\n'
                   'Kind: observed-absence\nObserved: fake\n' + FENCE + '\n')
        self.assert_rejected({'resource-usage.md': finish_row('0', 'history.md#e1'),
                              'history.md': history},
                             'zero Attempts lacks observed absence')

    def test_failed_correction_still_counts(self):
        history = ('### Event e1\n\n' + correction()
                   + '\n## Phase\n\nPlain prose without record keys.\n')
        self.assert_accepted({'resource-usage.md': finish_row('1', 'history.md#e1'),
                              'history.md': history})

    def test_missing_evidence_still_rejects(self):
        history = ('### Event e1\n\n' + correction(result='exit 0; all checks passed')
                   + '\n## Phase\n\nPlain prose without record keys.\n')
        self.assert_rejected({'resource-usage.md': finish_row('1', 'history.md#e1'),
                              'history.md': history},
                             'Attempts lacks task-linked failed correction or authorized escalation evidence')

    def test_keys_under_level_two_heading_count(self):
        history = '# Synthetic task history\n\n## Failure record\n\n' + correction()
        self.assert_accepted({'resource-usage.md': finish_row('1', 'history.md#e1'),
                              'history.md': history})


if __name__ == '__main__':
    unittest.main()
