"""The build warns on stderr, per field and kind, when the executive summary's reader-facing prose names an id, a file path, a backtick or a workspace.

The shipped recipe reads the same executive summary file it already loads and prints one line per field and kind
of prose that contains a Tackle id, a file path, a backtick or a workspace name. The prose is still rendered, the
exit is unchanged, the check is absent from `--check`, and it applies to Full and Focused plans alike. Ids in these
fixtures use four digits so the committed text carries no short literal id.
Guarantee: the stderr lines name the field by its path, the kind and the first match, in document order, with the
exemptions the maintainer's rule states (the top-level schema, the authority object, object keys, URLs).
Failure it catches: a check that scans only top-level strings, prints without the field path, flags object keys,
flags a URL, runs under `--check`, or runs on a summary the loader refused.
Consumer: the maintainer who authors the executive summary, and the authoring rule in the plan-view guide.
The agent's own wording of the prose is outside this oracle.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from eval.tests.product.status.test_plan_view import TEMPLATE, lite_plan, run_recipe, workspace_files

PREFIX = 'note: the executive summary field '


def summary(**fields):
    data = dict(schema='executive-presentation/1')
    data.update(fields)
    return data


def prose_lines(result):
    return [line for line in result.stderr.splitlines() if line.startswith(PREFIX)]


def build(tmp, case, export=None, extra=None, dirs=()):
    for name in dirs:
        (Path(tmp) / name).mkdir(parents=True, exist_ok=True)
    files = workspace_files()
    if export is not None:
        files['view/export-summary.json'] = json.dumps(export)
    files.update(extra or {})
    return run_recipe(tmp, files, case)


class ExecutivePayloadTests(unittest.TestCase):
    def assertBuilt(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_clean_prose_prints_no_note_and_the_build_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, 'clean', summary(
                context='Plain sentences for a reader. See https://example.com/guide.html for version 9.2.1.'))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [])
            self.assertTrue(out.is_file())

    def test_a_task_id_in_a_nested_field_names_the_field_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'task-id', summary(progress=dict(
                achievements=[dict(title='Closed', text='Closed T-0035 after review')])))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [
                PREFIX + 'progress.achievements[0].text contains a Tackle id: T-0035'])

    def test_decision_and_requirement_ids_give_one_note_per_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'decision-req', summary(
                purpose='Covers REQ-PAY-0002 for the payment rail.',
                plan=dict(key_choices=[dict(title='Route', text='Chosen in D-0058')])))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [
                PREFIX + 'purpose contains a Tackle id: REQ-PAY-0002',
                PREFIX + 'plan.key_choices[0].text contains a Tackle id: D-0058'])

    def test_a_path_with_a_slash_gives_a_file_path_note_and_an_id_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'path-slash', summary(progress=dict(evidence='see runs/P-0010/journal.md')))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [
                PREFIX + 'progress.evidence contains a Tackle id: P-0010',
                PREFIX + 'progress.evidence contains a file path: runs/P-0010/journal.md'])

    def test_a_known_extension_without_a_slash_is_a_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'extension', summary(progress=dict(
                open_work=[dict(title='Layout', text='Update Payment.storyboard')])))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [
                PREFIX + 'progress.open_work[0].text contains a file path: Payment.storyboard'])

    def test_a_backtick_gives_a_backtick_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'backtick', summary(kicker='Run `make test` '))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [PREFIX + 'kicker contains a backtick: `'])

    def test_a_workspace_path_gives_a_workspace_name_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'workspace-path', summary(context='Lives under docs/plans/payments-kit today.'))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [PREFIX + 'context contains a workspace name: docs/plans/'])

    def test_a_sibling_directory_name_with_a_hyphen_gives_a_workspace_name_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'probe', summary(combined='Compare with payments-kit in the portfolio.'),
                              dirs=('payments-kit',))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [PREFIX + 'combined contains a workspace name: payments-kit'])

    def test_the_workspace_own_hyphenated_name_gives_a_workspace_name_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'ledger-probe', summary(purpose='The ledger-probe status for the team.'))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [PREFIX + 'purpose contains a workspace name: ledger-probe'])

    def test_a_hyphenated_name_inside_a_longer_word_is_not_a_workspace_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'negatives', summary(
                context='xpayments-kit payments-kit2 payments-kit-2 payments_kit'), dirs=('payments-kit',))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [])

    def test_a_sibling_without_a_hyphen_is_not_a_workspace_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'plain', summary(context='Moved from archive last week.'), dirs=('archive',))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [])

    def test_the_schema_value_and_the_authority_object_are_not_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            export = dict(schema='executive-presentation/1 T-0035',
                          authority=dict(as_of='see T-0035', canonical_states={'T-0035': 'Complete'}))
            result, _ = build(tmp, 'skipped', export)
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [])

    def test_a_nested_key_named_schema_is_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'nested-schema', summary(plan=dict(schema='T-0035')))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [PREFIX + 'plan.schema contains a Tackle id: T-0035'])

    def test_object_keys_are_not_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'keys', summary(progress=dict(extra={'T-0035': 'plain words'})))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [])

    def test_a_url_with_leading_punctuation_is_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'url', summary(context='(https://example.com/x.html)'))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [])

    def test_notes_follow_document_order_and_kind_order_within_a_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'order', summary(kicker='Run `make test` now', context='Read T-0035 first',
                                                    progress=dict(evidence='see runs/P-0010/journal.md')))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [
                PREFIX + 'kicker contains a backtick: `',
                PREFIX + 'context contains a Tackle id: T-0035',
                PREFIX + 'progress.evidence contains a Tackle id: P-0010',
                PREFIX + 'progress.evidence contains a file path: runs/P-0010/journal.md'])

    def test_one_line_per_field_and_kind_names_the_first_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'one-line', summary(context='T-0035 and T-0036 both'))
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [PREFIX + 'context contains a Tackle id: T-0035'])

    def test_a_focused_plan_prints_the_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = {'plan.md': lite_plan(), 'history.md': '# History\n',
                     'view/export-summary.json': json.dumps(summary(kicker='Run `make test` now'))}
            result, _ = run_recipe(tmp, files, 'lite-prose')
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [PREFIX + 'kicker contains a backtick: `'])

    def test_check_mode_prints_no_prose_note_and_keeps_its_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, 'checked', summary(kicker='Run `make test` now'))
            self.assertBuilt(result)
            self.assertEqual(len(prose_lines(result)), 1)
            check = subprocess.run([sys.executable, '-I', str(Path(tmp) / 'checked-recipe.py'), '--template', str(TEMPLATE),
                                    '--check', str(Path(tmp) / 'checked'), str(out)],
                                   capture_output=True, text=True, timeout=60)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertIn('view current', check.stdout)
            self.assertEqual(prose_lines(check), [])

    def test_an_unloadable_first_candidate_prints_no_prose_note(self):
        flagged = json.dumps(summary(context='Read T-0035 first'))
        cases = {
            'invalid-json': '{not json',
            'not-an-object': '["T-0035"]',
            'unsupported-schema': json.dumps(dict(schema='unsupported/999', context='Read T-0035 first')),
        }
        for name, text in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                result, _ = build(tmp, name, extra={'view/export-summary.json': text,
                                                   'export-summary.json': flagged})
                self.assertBuilt(result)
                self.assertEqual(prose_lines(result), [])

    def test_a_root_only_export_summary_prints_its_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, 'root-only', extra={
                'export-summary.json': json.dumps(summary(context='Read T-0035 first'))})
            self.assertBuilt(result)
            self.assertEqual(prose_lines(result), [PREFIX + 'context contains a Tackle id: T-0035'])


class ExecutiveProseRuleTests(unittest.TestCase):
    """Boundary and ordering cases the rule's patterns and first-match choice must hold."""

    def notes_for(self, export):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = build(tmp, self._testMethodName, export)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return prose_lines(result)

    def test_a_file_path_token_prints_without_its_trailing_punctuation(self):
        self.assertEqual(self.notes_for(summary(progress=dict(
            open_work=[dict(title='Layout', text='Update Payment.storyboard, then review')]))), [
            PREFIX + 'progress.open_work[0].text contains a file path: Payment.storyboard'])

    def test_a_requirement_id_of_the_upper_case_letter_run_form_is_a_tackle_id(self):
        self.assertEqual(self.notes_for(summary(context='Owned by R-PAY-0014 today.')), [
            PREFIX + 'context contains a Tackle id: R-PAY-0014'])

    def test_the_single_letter_class_includes_g(self):
        self.assertEqual(self.notes_for(summary(context='Only G-0007 here.')), [
            PREFIX + 'context contains a Tackle id: G-0007'])

    def test_id_patterns_need_word_boundaries(self):
        self.assertEqual(self.notes_for(summary(context='Only XT-0035 here.')), [])

    def test_id_patterns_are_case_sensitive(self):
        self.assertEqual(self.notes_for(summary(context='Only t-0035 here.')), [])

    def test_the_first_match_is_the_earliest_by_position_not_the_first_pattern(self):
        self.assertEqual(self.notes_for(summary(purpose='Covers REQ-PAY-0002 before T-0035 here.')), [
            PREFIX + 'purpose contains a Tackle id: REQ-PAY-0002'])

    def test_each_field_names_only_its_first_file_path(self):
        self.assertEqual(self.notes_for(summary(progress=dict(evidence='see runs/a/one.md and docs/b/two.md'))), [
            PREFIX + 'progress.evidence contains a file path: runs/a/one.md'])

    def test_the_known_extension_match_is_case_insensitive(self):
        self.assertEqual(self.notes_for(summary(progress=dict(
            open_work=[dict(title='Layout', text='Update Payment.STORYBOARD')]))), [
            PREFIX + 'progress.open_work[0].text contains a file path: Payment.STORYBOARD'])

    def test_a_slash_path_accepts_a_suffix_of_up_to_ten_letters(self):
        self.assertEqual(self.notes_for(summary(context='Ship a/b.release now')), [
            PREFIX + 'context contains a file path: a/b.release'])

    def test_a_leading_quote_and_bracket_before_a_url_keep_it_exempt(self):
        self.assertEqual(self.notes_for(summary(context='["https://example.com/x.html"]')), [])
        self.assertEqual(self.notes_for(summary(context='["https://example.com/x.html')), [])


if __name__ == '__main__':
    unittest.main()
