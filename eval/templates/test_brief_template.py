"""The brief template's compiled contract: `references/task.tmpl.md` holds the sections a compiled brief keeps, it
names no external worker prerequisite, and its Effort is a placeholder the compiler resolves. Compiled briefs in
that shape (`fixtures/compiled-brief/`) keep an omitted requirement visible for semantic review, and the complete
one's own acceptance command passes valid output and rejects invalid output.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'references/task.tmpl.md'
LINT = (ROOT / 'references/guides/lint-spec.md').read_text()
FIXTURES = Path(__file__).resolve().parent / 'fixtures/compiled-brief'
BOARD = ('Schema: tackle-workspace/5\n\n| Task | What | Brief | Depends on | Status | Verification |\n'
         '|---|---|---|---|---|---|\n| T-A | Work | tasks/T-A.md | none | Draft | pending |\n')


def literal_row(number):
    line = next(line for line in LINT.splitlines() if line.startswith(f'| {number} ·'))
    return line.split(' | `', 1)[1].rsplit('` |', 1)[0]


def run_row12(brief):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        workspace = root / 'docs/plans/demo'
        (workspace / 'tasks').mkdir(parents=True)
        (workspace / 'task-board.md').write_text(BOARD)
        (workspace / 'tasks/T-A.md').write_text(brief)
        return subprocess.run(['sh', '-c', literal_row(12).replace('<slug>', 'demo')], cwd=root,
                              capture_output=True, text=True, timeout=10)


def structural_contract_shape(text):
    """Shape only; semantic completeness belongs to the independent review rubric."""
    return all(section in text for section in [
        '## Purpose and scope', '## Contract and cases', '## Approach', '## Acceptance and recovery',
    ]) and '### Case matrix' in text and '### Shared clauses (compiled)' in text


def effort_declaration(text):
    lines = [line for line in text.splitlines() if line.startswith('- **Effort**: ')]
    if len(lines) != 1:
        return None
    return lines[0].split(': ', 1)[1].strip()


def run_acceptance(brief_path, *, valid, pretty=False, missing_json=False):
    command = brief_path.read_text().split('```sh\n', 1)[1].split('\n```', 1)[0]
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        if valid:
            (root / 'result.csv').write_bytes(b'name,score\nBo,3\nAda,2\n')
            result = '{"score": 3, "name": "Bo"}\n' if not pretty else '{\n  "name": "Bo",\n  "score": 3\n}\n'
            if not missing_json:
                (root / 'result.json').write_text(result)
        else:
            (root / 'result.csv').write_bytes(b'name,score\nAda,2\nBo,3\n')
            if not missing_json:
                (root / 'result.json').write_text('{"score": 3, "name": "Bo"}\n')
        return subprocess.run(['sh', '-c', command], cwd=root, capture_output=True, text=True, timeout=10)


def run_generated_unit_tests():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for name in ['normalize.py', 'normalize_check.py']:
            shutil.copyfile(FIXTURES / name, root / name)
        return subprocess.run(['python3', '-m', 'unittest', '-v', 'normalize_check.py'],
                              cwd=root, capture_output=True, text=True, timeout=10)


class BriefTemplateContractTests(unittest.TestCase):
    def test_template_has_the_compiled_contract_and_no_external_worker_prerequisite(self):
        template = TEMPLATE.read_text()
        for section in ['Purpose and scope', 'Contract and cases', 'Approach', 'Acceptance and recovery']:
            self.assertIn(section, template)
        self.assertIn('file alone', template)
        self.assertIn('clause id', template)
        self.assertIn('sha256', template)
        self.assertIn('valid semantic equivalents', template)
        self.assertIn('discovery', template)
        self.assertIn('experiment', template)
        effort = effort_declaration(template)
        self.assertTrue(effort.startswith('{{') and effort.endswith('}}'), effort)
        for level in ('low', 'medium', 'high', 'max'):
            self.assertIn(level, effort)
        invalid_effort = (FIXTURES / 'effort-invalid.md').read_text()
        self.assertNotIn(effort_declaration(invalid_effort), {'low', 'medium', 'high', 'max'})
        for number in [6, 11, 16]:
            self.assertNotIn('|', literal_row(number))
        valid = run_row12('# Task T-A\n- **Effort**: low\n')
        invalid = run_row12(invalid_effort)
        self.assertEqual((valid.returncode, valid.stdout), (0, ''))
        self.assertEqual(invalid.returncode, 0)
        self.assertIn('heroic', invalid.stdout)

    def test_compiled_briefs_keep_the_template_shape_and_expose_an_omission_for_review(self):
        self.assertTrue(structural_contract_shape(TEMPLATE.read_text()))
        complete = FIXTURES / 'complete.md'
        self.assertTrue(structural_contract_shape(complete.read_text()))
        self.assertTrue(structural_contract_shape((FIXTURES / 'omitted-requirement.md').read_text()))
        self.assertFalse(structural_contract_shape((FIXTURES / 'keyword-only.md').read_text()))
        valid = run_acceptance(complete, valid=True)
        pretty = run_acceptance(complete, valid=True, pretty=True)
        invalid = run_acceptance(complete, valid=False)
        missing_json = run_acceptance(complete, valid=True, missing_json=True)
        self.assertEqual((valid.returncode, valid.stdout), (0, 'PASS task\n'))
        self.assertEqual((pretty.returncode, pretty.stdout), (0, 'PASS task\n'))
        self.assertNotEqual(invalid.returncode, 0)
        self.assertNotIn('PASS task', invalid.stdout)
        self.assertNotEqual(missing_json.returncode, 0)
        self.assertNotIn('PASS task', missing_json.stdout)
        self.assertEqual(run_generated_unit_tests().returncode, 0)


if __name__ == '__main__':
    unittest.main()
