"""Physical receipt additions preserve closed-report bytes; owner truth is separate."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root


class ClosedReportReceiptTests(unittest.TestCase):
    def test_required_receipt_addition_preserves_existing_report_bytes(self):
        path = current_root(ROOT) / 'scripts/migrate/compact.py'
        spec = importlib.util.spec_from_file_location('tackle_closed_report_receipts', path)
        compact = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compact)
        preserves = compact._closed_report_body_preserved
        body = b'# T-' b'01 report\n\nObserved legacy closure.\n'
        baseline = b'**Brief sha256**: ' + b'a' * 64 + b'\n'
        erratum = ('**Brief erratum**: D-' '07 · sha256 ' + 'b' * 64 + '\n').encode('utf-8')
        none = b'**Remains**: none\n'
        obligations = b'**Remains**: O-01, O-02\n'
        existing = body + b'\n' + none
        fenced = body + b'\n```text\n**Brief sha256**: historical-example\n**Remains**: none\n```\n'
        quoted = body + b'\n> **Brief sha256**: historical-example\n> **Remains**: none\n'
        # These literals are independent contract cases, not candidate-generated expectations.
        cases = [
            ('required-none', body, body + b'\n' + baseline + none, 'Complete', True),
            ('actual-obligation-alternative', body, body + baseline + obligations, 'Complete', True),
            ('row17-list-carrier-alternative', body, body + b'- **Remains**: O-01,O-02\n', 'Complete', True),
            ('unchanged-receipt', existing, body + b'\n' + baseline + none, 'Complete', True),
            ('missing-receipt-before-new-erratum', body, body + b'\n' + baseline + none + erratum, 'Complete', True),
            ('unchanged-body', body, body, 'Complete', True),
            ('fenced-examples-preserved', fenced, fenced + baseline + obligations, 'Complete', True),
            ('quoted-examples-preserved', quoted, quoted + baseline + none, 'Complete', True),
            ('body-without-final-lf-preserved', body[:-1], body[:-1] + b'\n' + none, 'Complete', True),
            ('existing-value-changed', existing, body + b'\n' + obligations, 'Complete', False),
            ('existing-unknown-overwritten', body + b'**Remains**: unknown\n', existing, 'Complete', False),
            ('duplicate-carriers', body, body + none + obligations, 'Complete', False),
            ('prior-bullet-carrier-is-not-missing', body + b'  - **Remains**: none\n', body + b'  - **Remains**: none\n' + none, 'Complete', False),
            ('unknown-value', body, body + b'**Remains**: unknown\n', 'Complete', False),
            ('empty-value', body, body + b'**Remains**:\n', 'Complete', False),
            ('malformed-id', body, body + b'**Remains**: O-1\n', 'Complete', False),
            ('overwide-id', body, body + b'**Remains**: O-123\n', 'Complete', False),
            ('trailing-comma', body, body + b'**Remains**: O-01,\n', 'Complete', False),
            ('unrecognized-separator', body, body + b'**Remains**: O-01; O-02\n', 'Complete', False),
            ('only-fenced-carrier', body, body + b'```text\n' + none + b'```\n', 'Complete', False),
            ('only-quoted-carrier', body, body + b'> ' + none, 'Complete', False),
            ('unrelated-body-edit', body, body.replace(b'Observed', b'Invented') + none, 'Complete', False),
            ('fenced-baseline-cannot-hide-edit', fenced, fenced.replace(b'historical-example', b'rewritten') + none, 'Complete', False),
            ('quoted-baseline-cannot-hide-edit', quoted, quoted.replace(b'historical-example', b'rewritten') + none, 'Complete', False),
            ('original-lf-lost', body, body.rstrip(b'\n') + none, 'Complete', False),
            ('extra-after-receipt', body, body + none + b'Unrelated new claim.\n', 'Complete', False),
            ('unclosed-fence', body, body + b'```text\n' + none, 'Complete', False),
            ('skipped-has-no-new-required-carrier', body, body + none, 'Skipped', False),
            ('unverifiable-has-no-new-required-carrier', body, body + none, 'Unverifiable', False),
        ]
        for name, before, after, status, expected in cases:
            with self.subTest(name=name):
                self.assertIs(preserves(before, after, status), expected)


if __name__ == '__main__':
    unittest.main()
