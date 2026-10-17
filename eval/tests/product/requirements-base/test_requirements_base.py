"""The shipped requirements-base script parses, validates, reconciles and folds a base, and the guide states its rules.

The test imports the script `scripts/requirements_base.py` by file path and calls its functions on fixtures under
`eval/requirements-base/fixtures/`. Expected values come from the case matrix of the task brief, not from the script.
"""
import ast
import copy
import hashlib
import importlib.util
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
FIXTURES = REPO / 'eval/requirements-base/fixtures'
RECIPE = REPO / 'skills/tackle/scripts/requirements_base.py'
GUIDE = REPO / 'skills/tackle/references/guides/requirements-base.md'
README = REPO / 'skills/tackle/scripts/README.md'
FORBIDDEN = {'socket', 'ssl', 'urllib', 'http', 'subprocess', 'requests', 'asyncio', 'webbrowser', 'multiprocessing'}
FINAL = 'a1b2c3d'
OLD = 'e4f5a6b'
PLAN = 'demo-plan'
DATE = '2026-10-13'
BILLING_CHECK = '`python3 -m unittest tests.billing` exits 0'
PASSKEY_CHECK = '`python3 -m unittest tests.auth.test_passkey` exits 0'
REVIEW_CHECK = 'review: fold-safety by reviewer'
GUIDE_SENTENCES = (
    'Before the first requirements delta in a project, ask once whether `docs/requirements/` is gitignored.',
    'Validate the delta before Ready of any task that owns an entry; validation reports every problem, and an invalid delta blocks those tasks.',
    'At closure, fold only done entries whose every scenario Check passed on the final revision, and only after the owner confirms.',
    'A project without a base is valid; never offer to document the whole system, and never write a base outside a confirmed fold.',
)


def fixture(name):
    return (FIXTURES / name).read_text(encoding='utf-8')


def base_files():
    return {'auth': fixture('base/auth.md')}


def record(check, revision, passed=True):
    return {'check': check, 'revision': revision, 'passed': passed}


def script_source(path):
    return path.read_text(encoding='utf-8')


def load_recipe():
    source = script_source(RECIPE)
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported |= {a.name.split('.')[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split('.')[0])
    assert not imported & FORBIDDEN, 'the requirements-base recipe imports %s' % sorted(imported & FORBIDDEN)
    spec = importlib.util.spec_from_file_location('requirements_base_script', RECIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return vars(module)


def reorder_with_prose(text):
    """The same delta with each entry block reversed within its section and a prose line after each."""
    chunks = []
    for line in text.split('\n'):
        if line.startswith('## ') or line.startswith('### ') or not chunks:
            chunks.append([line])
        else:
            chunks[-1].append(line)
    prose = 'Some prose between entries.'
    result, group = [], []
    for chunk in chunks:
        if chunk[0].startswith('### '):
            group.append(chunk)
            continue
        result.extend(line for block in reversed(group) for line in block + [prose])
        group = []
        result.extend(chunk)
    result.extend(line for block in reversed(group) for line in block + [prose])
    return '\n'.join(result)


class RequirementsBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = load_recipe()

    def fold(self, files, delta_text, records, revision=FINAL):
        return self.recipe['fold'](files, delta_text, records, revision, PLAN, DATE)

    def test_add_creates_domain_file(self):
        out = self.fold({}, fixture('delta/billing-add.md'), [record(BILLING_CHECK, FINAL)])
        self.assertEqual(sorted(out), ['billing'])
        text = out['billing']
        self.assertIn('# Requirements — Billing', text)
        self.assertLess(text.index('## Active'), text.index('### REQ-BILLING-01 · Receipts are issued'))
        self.assertLess(text.index('### REQ-BILLING-01 · Receipts are issued'), text.index('## Retired'))

    def test_modify_replaces_in_place(self):
        out = self.fold(base_files(), fixture('delta/auth-modify.md'), [record(PASSKEY_CHECK, FINAL)])
        text = out['auth']
        self.assertIn('sign in with a password or a passkey', text)
        self.assertNotIn('The system SHALL let a user sign in with a password.', text)
        self.assertNotIn('#### Scenario: Valid password', text)
        self.assertIn('#### Scenario: Valid passkey', text)
        self.assertLess(text.index('### REQ-AUTH-01'), text.index('### REQ-AUTH-02'))

    def test_remove_moves_to_retired(self):
        out = self.fold(base_files(), fixture('delta/auth-remove.md'), [])
        text = out['auth']
        retired_at = text.index('## Retired')
        self.assertIn('### REQ-AUTH-02 · Sign out\nRetired: demo-plan · 2026-10-13 · sessions end on browser close\n', text)
        self.assertGreater(text.index('### REQ-AUTH-02'), retired_at)
        self.assertLess(text.index('### REQ-AUTH-01'), retired_at)

    def test_validate_reports_every_problem(self):
        problems = self.recipe['validate'](self.recipe['parse_base'](base_files()),
                                           self.recipe['parse_delta'](fixture('delta/invalid.md')))
        self.assertEqual(sorted(p['kind'] for p in problems), ['conflict', 'duplicate', 'unchecked', 'unknown'])

    def test_malformed_entry(self):
        problems = self.recipe['validate'](self.recipe['parse_base'](base_files()),
                                           self.recipe['parse_delta'](fixture('delta/malformed.md')))
        self.assertEqual(sorted(p['kind'] for p in problems), ['malformed', 'malformed', 'malformed'])

    def test_planned_entry_never_folds(self):
        delta = self.recipe['parse_delta'](fixture('delta/planned.md'))
        reconciled, unreconciled = self.recipe['reconcile'](delta, [record(BILLING_CHECK, FINAL)], FINAL)
        self.assertEqual(reconciled, [])
        self.assertEqual(unreconciled, [{'id': 'REQ-BILLING-01', 'scenario': None, 'check': None, 'reason': 'planned'}])
        self.assertEqual(self.fold({}, fixture('delta/planned.md'), [record(BILLING_CHECK, FINAL)]), {})

    def test_unreconciled_entry_not_folded(self):
        delta = self.recipe['parse_delta'](fixture('delta/billing-add.md'))
        reconciled, unreconciled = self.recipe['reconcile'](delta, [], FINAL)
        self.assertEqual(reconciled, [])
        self.assertEqual(unreconciled, [{'id': 'REQ-BILLING-01', 'scenario': 'Completed payment',
                                         'check': BILLING_CHECK, 'reason': 'no passing record'}])
        self.assertEqual(self.fold({}, fixture('delta/billing-add.md'), []), {})

    def test_stale_record_not_folded(self):
        delta = self.recipe['parse_delta'](fixture('delta/billing-add.md'))
        reconciled, unreconciled = self.recipe['reconcile'](delta, [record(BILLING_CHECK, OLD)], FINAL)
        self.assertEqual(reconciled, [])
        self.assertEqual(unreconciled[0]['reason'], 'stale record')
        self.assertEqual(self.fold({}, fixture('delta/billing-add.md'), [record(BILLING_CHECK, OLD)]), {})

    def test_review_check_reconciles(self):
        delta = self.recipe['parse_delta'](fixture('delta/review.md'))
        reconciled, unreconciled = self.recipe['reconcile'](delta, [record(REVIEW_CHECK, FINAL)], FINAL)
        self.assertEqual(reconciled, ['REQ-BILLING-01'])
        self.assertEqual(unreconciled, [])
        self.assertIn('billing', self.fold({}, fixture('delta/review.md'), [record(REVIEW_CHECK, FINAL)]))

    def test_brownfield_modify_is_unknown(self):
        problems = self.recipe['validate'](self.recipe['parse_base']({}), self.recipe['parse_delta'](fixture('delta/auth-modify.md')))
        self.assertEqual([p['kind'] for p in problems], ['unknown'])

    def test_fold_refuses_invalid_delta(self):
        with self.assertRaises(ValueError) as caught:
            self.fold(base_files(), fixture('delta/invalid.md'), [])
        self.assertIn('REQ-AUTH-01', str(caught.exception))

    def test_repository_problems(self):
        base = self.recipe['parse_base']({})
        delta = self.recipe['parse_delta'](fixture('delta/repository.md'))
        problems = self.recipe['validate'](base, delta, {'api', 'web'})
        self.assertEqual(sorted(p['kind'] for p in problems), ['repository', 'repository'])
        self.assertEqual(self.recipe['validate'](base, delta), [])

    def test_problem_order_and_prose_free(self):
        base = self.recipe['parse_base'](base_files())

        def problem_set(text):
            return sorted((p['kind'], p['id']) for p in self.recipe['validate'](base, self.recipe['parse_delta'](text)))

        original = fixture('delta/invalid.md')
        self.assertEqual(len(problem_set(original)), 4)
        self.assertEqual(problem_set(reorder_with_prose(original)), problem_set(original))

    def test_script_is_one_stdlib_module(self):
        text = RECIPE.read_text(encoding='utf-8')
        self.assertNotIn('```', text)
        imported = set()
        for node in ast.walk(ast.parse(script_source(RECIPE))):
            if isinstance(node, ast.Import):
                imported |= {a.name.split('.')[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split('.')[0])
        self.assertFalse(imported & FORBIDDEN)

    def test_guide_states_the_rules(self):
        guide = GUIDE.read_text(encoding='utf-8')
        for sentence in GUIDE_SENTENCES:
            self.assertIn(sentence, guide)
        self.assertIn('](../../scripts/requirements_base.py)', guide)

    def test_readme_hash_row_matches(self):
        readme = README.read_text(encoding='utf-8')
        row = re.search(r'\| \[requirements_base\.py\]\(requirements_base\.py\) \| `([0-9a-f]{64})` \|', readme)
        self.assertIsNotNone(row)
        self.assertEqual(row.group(1), hashlib.sha256(RECIPE.read_bytes()).hexdigest())


    def test_every_scenario_must_reconcile(self):
        delta_text = fixture('delta/two-scenarios.md')
        delta = self.recipe['parse_delta'](delta_text)
        reconciled, unreconciled = self.recipe['reconcile'](delta, [record('`python3 -m unittest tests.billing` exits 0', FINAL)], FINAL)
        self.assertEqual(reconciled, [])
        self.assertEqual(unreconciled, [{'id': 'REQ-BILLING-01', 'scenario': 'Refunded payment',
                                         'check': '`python3 -m unittest tests.billing_refund` exits 0',
                                         'reason': 'no passing record'}])
        self.assertEqual(self.fold({}, delta_text, [record('`python3 -m unittest tests.billing` exits 0', FINAL)]), {})
        reconciled, unreconciled = self.recipe['reconcile'](delta, [], FINAL)
        self.assertEqual([row['scenario'] for row in unreconciled], ['Completed payment', 'Refunded payment'])

    def test_failed_record_does_not_reconcile(self):
        delta_text = fixture('delta/billing-add.md')
        failed = [record(BILLING_CHECK, FINAL, passed=False)]
        reconciled, unreconciled = self.recipe['reconcile'](self.recipe['parse_delta'](delta_text), failed, FINAL)
        self.assertEqual(reconciled, [])
        self.assertEqual(unreconciled[0]['reason'], 'no passing record')
        self.assertEqual(self.fold({}, delta_text, failed), {})

    def test_fold_output_ends_with_one_newline(self):
        outputs = [
            self.fold({}, fixture('delta/billing-add.md'), [record(BILLING_CHECK, FINAL)]),
            self.fold(base_files(), fixture('delta/auth-modify.md'), [record(PASSKEY_CHECK, FINAL)]),
            self.fold(base_files(), fixture('delta/auth-remove.md'), []),
        ]
        for out in outputs:
            self.assertTrue(out)
            for text in out.values():
                self.assertTrue(text.endswith('\n'))
                self.assertFalse(text.endswith('\n\n'))

    def test_retired_entry_keeps_statement_and_scenarios(self):
        out = self.fold(base_files(), fixture('delta/auth-remove.md'), [])
        retired = out['auth'][out['auth'].index('## Retired'):]
        self.assertIn('### REQ-AUTH-02 · Sign out', retired)
        self.assertIn('The system MUST end the session when the user signs out.', retired)
        self.assertIn('#### Scenario: Sign out', retired)
        self.assertIn('- Check: `python3 -m unittest tests.auth.test_sign_out` exits 0', retired)

    def test_fold_output_round_trips(self):
        cases = [
            self.fold({}, fixture('delta/billing-add.md'), [record(BILLING_CHECK, FINAL)]),
            self.fold(base_files(), fixture('delta/auth-modify.md'), [record(PASSKEY_CHECK, FINAL)]),
            self.fold(base_files(), fixture('delta/auth-remove.md'), []),
        ]
        for out in cases:
            for domain, text in out.items():
                parsed = self.recipe['parse_base']({domain: text})
                self.assertEqual(parsed['problems'], [])
                self.assertTrue(all(req['domain'] == domain for req in parsed['requirements'].values()))

    def test_validate_retired_add_is_duplicate(self):
        base = self.recipe['parse_base']({'auth': fixture('base/retired.md')})
        problems = self.recipe['validate'](base, self.recipe['parse_delta'](fixture('delta/readd-retired.md')))
        self.assertEqual([(p['kind'], p['id']) for p in problems], [('duplicate', 'REQ-AUTH-03')])

    def test_validate_repeated_add_is_duplicate(self):
        problems = self.recipe['validate'](self.recipe['parse_base']({}), self.recipe['parse_delta'](fixture('delta/repeated.md')))
        self.assertEqual([(p['kind'], p['id']) for p in problems], [('duplicate', 'REQ-BILLING-01')])

    def test_validate_unknown_removed(self):
        problems = self.recipe['validate'](self.recipe['parse_base'](base_files()), self.recipe['parse_delta'](fixture('delta/unknown-removed.md')))
        self.assertEqual([(p['kind'], p['id']) for p in problems], [('unknown', 'REQ-AUTH-09')])

    def test_planned_entries_never_fold_in_any_section(self):
        cases = [
            ('delta/planned.md', [record(BILLING_CHECK, FINAL)], 'REQ-BILLING-01'),
            ('delta/planned-modified.md', [record(PASSKEY_CHECK, FINAL)], 'REQ-AUTH-01'),
            ('delta/planned-removed.md', [record('`python3 -m unittest tests.auth.test_sign_out` exits 0', FINAL)], 'REQ-AUTH-02'),
        ]
        for name, records, id_ in cases:
            with self.subTest(fixture=name):
                files = base_files()
                before = copy.deepcopy(files)
                reconciled, unreconciled = self.recipe['reconcile'](self.recipe['parse_delta'](fixture(name)), records, FINAL)
                self.assertEqual(reconciled, [])
                self.assertEqual(unreconciled, [{'id': id_, 'scenario': None, 'check': None, 'reason': 'planned'}])
                self.assertEqual(self.fold(files, fixture(name), records), {})
                self.assertEqual(files, before)

    def test_stale_reason_needs_a_passing_older_record(self):
        delta = self.recipe['parse_delta'](fixture('delta/billing-add.md'))
        cases = [
            ([record(BILLING_CHECK, OLD, passed=False)], 'no passing record'),
            ([record(BILLING_CHECK, FINAL, passed=False)], 'no passing record'),
            ([record(BILLING_CHECK, OLD, passed=True)], 'stale record'),
            ([record(BILLING_CHECK, OLD, passed=True), record(BILLING_CHECK, FINAL, passed=False)], 'stale record'),
            ([record(BILLING_CHECK, OLD, passed=False), record(BILLING_CHECK, FINAL, passed=False)], 'no passing record'),
            ([record('`python3 -m unittest tests.other` exits 0', OLD, passed=True)], 'no passing record'),
        ]
        for records, reason in cases:
            with self.subTest(records=records):
                reconciled, unreconciled = self.recipe['reconcile'](delta, records, FINAL)
                self.assertEqual(reconciled, [])
                self.assertEqual([row['reason'] for row in unreconciled], [reason])

    def test_inputs_are_not_changed(self):
        files = base_files()
        base = self.recipe['parse_base'](files)
        delta_text = fixture('delta/mixed.md')
        delta = self.recipe['parse_delta'](delta_text)
        records = [record(BILLING_CHECK, OLD, passed=False), record(BILLING_CHECK, FINAL)]
        snapshot = copy.deepcopy((files, base, delta, records))
        self.recipe['parse_base'](files)
        self.recipe['parse_delta'](delta_text)
        self.recipe['validate'](base, delta)
        self.recipe['reconcile'](delta, records, FINAL)
        self.recipe['fold'](files, delta_text, records, FINAL, PLAN, DATE)
        self.assertEqual((files, base, delta, records), snapshot)

    def test_fold_changes_only_touched_domains(self):
        files = {'auth': fixture('base/auth.md'), 'billing': fixture('base/billing.md')}
        out = self.fold(files, fixture('delta/auth-modify.md'), [record(PASSKEY_CHECK, FINAL)])
        self.assertEqual(sorted(out), ['auth'])
        self.assertEqual(sorted(self.recipe['parse_base'](out)['requirements']), ['REQ-AUTH-01', 'REQ-AUTH-02'])
        removed = self.fold(files, fixture('delta/auth-remove.md'), [])
        after = self.recipe['parse_base'](removed)['requirements']
        self.assertEqual(sorted(after), ['REQ-AUTH-01', 'REQ-AUTH-02'])
        self.assertEqual((after['REQ-AUTH-01']['state'], after['REQ-AUTH-02']['state']), ('active', 'retired'))

    def test_fold_appends_added_under_active(self):
        out = self.fold(base_files(), fixture('delta/auth-add.md'), [record('`python3 -m unittest tests.auth.test_lock` exits 0', FINAL)])
        text = out['auth']
        self.assertLess(text.index('### REQ-AUTH-01'), text.index('### REQ-AUTH-02'))
        self.assertLess(text.index('### REQ-AUTH-02'), text.index('### REQ-AUTH-04'))
        self.assertLess(text.index('### REQ-AUTH-04'), text.index('## Retired'))

    def test_new_domain_title_follows_hyphenated_domain(self):
        out = self.fold({}, fixture('delta/hyphen-domain.md'), [record('`python3 -m unittest tests.billing_api` exits 0', FINAL)])
        self.assertEqual(sorted(out), ['billing-api'])
        self.assertTrue(out['billing-api'].startswith('# Requirements — Billing Api\n'))
        self.assertEqual(self.recipe['parse_base'](out)['requirements']['REQ-BILLING-API-01']['domain'], 'billing-api')

    def test_fold_applies_only_reconciled_entries(self):
        delta_text = fixture('delta/mixed.md')
        records = [record(BILLING_CHECK, FINAL)]
        reconciled, unreconciled = self.recipe['reconcile'](self.recipe['parse_delta'](delta_text), records, FINAL)
        self.assertEqual(reconciled, ['REQ-BILLING-01'])
        self.assertEqual(unreconciled, [
            {'id': 'REQ-BILLING-07', 'scenario': None, 'check': None, 'reason': 'planned'},
            {'id': 'REQ-BILLING-06', 'scenario': 'Chargeback', 'check': '`python3 -m unittest tests.billing_chargeback` exits 0',
             'reason': 'no passing record'},
        ])
        text = self.fold({}, delta_text, records)['billing']
        self.assertIn('### REQ-BILLING-01', text)
        self.assertNotIn('REQ-BILLING-06', text)
        self.assertNotIn('REQ-BILLING-07', text)

    def test_fold_refuses_every_problem_kind(self):
        for name in ('delta/malformed.md', 'delta/unknown-removed.md', 'delta/repeated.md', 'delta/invalid.md', 'delta/invalid-shapes.md'):
            with self.subTest(fixture=name):
                with self.assertRaises(ValueError):
                    self.fold(base_files(), fixture(name), [])
        with self.assertRaises(ValueError) as caught:
            self.fold(base_files(), fixture('delta/invalid.md'), [])
        message = str(caught.exception)
        for expected in ('duplicate REQ-AUTH-01', 'unknown REQ-AUTH-09', 'conflict REQ-AUTH-02', 'unchecked REQ-BILLING-02'):
            self.assertIn(expected, message)

    def test_entries_without_scenarios_and_short_ids_are_malformed(self):
        problems = self.recipe['validate'](self.recipe['parse_base'](base_files()), self.recipe['parse_delta'](fixture('delta/invalid-shapes.md')))
        self.assertEqual(sorted((p['kind'], p['id']) for p in problems),
                         [('malformed', ''), ('malformed', 'REQ-AUTH-01'), ('malformed', 'REQ-BILLING-05')])

    def test_parsed_shapes_match_the_interface(self):
        base = self.recipe['parse_base'](base_files())
        self.assertEqual(set(base), {'requirements', 'problems'})
        req = base['requirements']['REQ-AUTH-01']
        self.assertEqual(set(req), {'id', 'domain', 'title', 'statement', 'scenarios', 'state', 'retired'})
        self.assertEqual((req['domain'], req['title'], req['state'], req['retired']),
                         ('auth', 'Sign in with a password', 'active', None))
        self.assertEqual(set(req['scenarios'][0]), {'name', 'given', 'when', 'then', 'check'})
        retired = self.recipe['parse_base']({'auth': fixture('base/retired.md')})['requirements']['REQ-AUTH-03']
        self.assertEqual((retired['state'], retired['retired']), ('retired', 'legacy-plan · 2026-01-02 · replaced by passkeys'))
        delta = self.recipe['parse_delta'](fixture('delta/billing-add.md'))
        self.assertEqual(set(delta), {'base_revision', 'entries', 'problems'})
        self.assertEqual(delta['base_revision'], 'none')
        entry = delta['entries'][0]
        self.assertEqual(set(entry), {'section', 'id', 'title', 'task', 'state', 'repository', 'statement', 'scenarios', 'reason'})
        self.assertEqual((entry['section'], entry['task'], entry['state'], entry['repository']), ('ADDED', 'T-0N', 'done', None))
        self.assertEqual(self.recipe['parse_delta'](fixture('delta/repository.md'))['entries'][0]['repository'], 'api')
        for problem in self.recipe['validate'](base, self.recipe['parse_delta'](fixture('delta/invalid.md'))):
            self.assertEqual(set(problem), {'kind', 'id', 'detail'})
            self.assertIn(problem['kind'], ('duplicate', 'unknown', 'conflict', 'malformed', 'unchecked', 'repository'))

    def test_scenario_grammar_parses(self):
        scenario = self.recipe['parse_delta'](fixture('delta/scenario-grammar.md'))['entries'][0]['scenarios'][0]
        self.assertEqual(scenario, {'name': 'Grammar', 'given': ['a registered customer'],
                                    'when': ['the customer pays', 'the payment is approved'],
                                    'then': ['a receipt is issued', 'the receipt is emailed'],
                                    'check': '`python3 -m unittest tests.billing_grammar` exits 0'})

    def test_base_ids_are_unique(self):
        problems = self.recipe['parse_base']({'auth': fixture('base/duplicate.md')})['problems']
        self.assertEqual([(p['kind'], p['id']) for p in problems], [('duplicate', 'REQ-AUTH-01')])

    def test_brownfield_removed_is_unknown(self):
        problems = self.recipe['validate'](self.recipe['parse_base']({}), self.recipe['parse_delta'](fixture('delta/auth-remove.md')))
        self.assertEqual([(p['kind'], p['id']) for p in problems], [('unknown', 'REQ-AUTH-02')])

    def test_removed_entry_needs_no_record_and_keeps_base(self):
        base = self.recipe['parse_base'](base_files())
        delta = self.recipe['parse_delta'](fixture('delta/auth-remove.md'))
        self.assertEqual(self.recipe['validate'](base, delta), [])
        self.assertEqual(self.recipe['reconcile'](delta, [], FINAL), (['REQ-AUTH-02'], []))

    def test_script_has_no_file_access(self):
        source = script_source(RECIPE)
        for pattern in (r'\bopen\(', r'read_text', r'write_text', r'pathlib', r'\bos\b', r'\bshutil\b', r'\bio\b'):
            self.assertIsNone(re.search(pattern, source), pattern)

    def test_fold_keeps_existing_retired_entries(self):
        out = self.fold({'auth': fixture('base/retired.md')}, fixture('delta/auth-add.md'), [record('`python3 -m unittest tests.auth.test_lock` exits 0', FINAL)])
        tail = ('## Retired\n\n### REQ-AUTH-03 · Legacy login\n'
                'Retired: legacy-plan · 2026-01-02 · replaced by passkeys\n\n'
                'The system SHALL accept a legacy password form.\n\n'
                '#### Scenario: Legacy form\n- WHEN the legacy form is submitted\n- THEN the user is signed in\n'
                '- Check: `python3 -m unittest tests.auth.test_legacy_form` exits 0\n')
        self.assertTrue(out['auth'].endswith(tail))
        self.assertLess(out['auth'].index('### REQ-AUTH-04'), out['auth'].index('## Retired'))

    def test_retired_id_is_unknown_for_modified_and_removed(self):
        base = self.recipe['parse_base']({'auth': fixture('base/retired.md')})
        for name in ('delta/modify-retired.md', 'delta/remove-retired.md'):
            with self.subTest(fixture=name):
                problems = self.recipe['validate'](base, self.recipe['parse_delta'](fixture(name)))
                self.assertEqual([(p['kind'], p['id']) for p in problems], [('unknown', 'REQ-AUTH-03')])

    def test_conflict_for_added_with_modified_and_removed(self):
        for name in ('delta/conflict-added-modified.md', 'delta/conflict-added-removed.md'):
            with self.subTest(fixture=name):
                problems = self.recipe['validate'](self.recipe['parse_base']({}), self.recipe['parse_delta'](fixture(name)))
                self.assertEqual(sorted((p['kind'], p['id']) for p in problems),
                                 [('conflict', 'REQ-BILLING-07'), ('unknown', 'REQ-BILLING-07')])

    def test_modified_statement_needs_shall_or_must(self):
        problems = self.recipe['validate'](self.recipe['parse_base'](base_files()), self.recipe['parse_delta'](fixture('delta/modified-no-shall.md')))
        self.assertEqual([(p['kind'], p['id']) for p in problems], [('malformed', 'REQ-AUTH-01')])

    def test_modified_scenario_needs_a_check(self):
        problems = self.recipe['validate'](self.recipe['parse_base'](base_files()), self.recipe['parse_delta'](fixture('delta/modified-no-check.md')))
        self.assertEqual([(p['kind'], p['id']) for p in problems], [('unchecked', 'REQ-AUTH-01')])

    def test_multi_repo_checks_modified_and_removed(self):
        base = self.recipe['parse_base'](base_files())
        delta = self.recipe['parse_delta'](fixture('delta/multi-repo-modified-removed.md'))
        problems = self.recipe['validate'](base, delta, {'api', 'web'})
        self.assertEqual([(p['kind'], p['id']) for p in problems], [('repository', 'REQ-AUTH-01'), ('repository', 'REQ-AUTH-02')])
        self.assertEqual(self.recipe['validate'](base, delta), [])

    def test_reconcile_matches_check_text_exactly(self):
        delta = self.recipe['parse_delta'](fixture('delta/billing-add.md'))
        variants = [
            BILLING_CHECK + ' now',
            BILLING_CHECK[:-1],
            BILLING_CHECK.upper(),
            BILLING_CHECK.replace('tests.billing', 'tests.Billing'),
            BILLING_CHECK.replace(' ', '  ', 1),
            BILLING_CHECK + ' ',
        ]
        for variant in variants:
            with self.subTest(check=variant):
                reconciled, unreconciled = self.recipe['reconcile'](delta, [record(variant, FINAL)], FINAL)
                self.assertEqual(reconciled, [])
                self.assertEqual([row['reason'] for row in unreconciled], ['no passing record'])

    def test_new_domain_file_layout_is_exact(self):
        out = self.fold({}, fixture('delta/billing-add.md'), [record(BILLING_CHECK, FINAL)])
        self.assertEqual(out['billing'], (
            '# Requirements — Billing\n\n## Active\n\n'
            '### REQ-BILLING-01 · Receipts are issued\n\n'
            'The system SHALL issue a receipt for every completed payment.\n\n'
            '#### Scenario: Completed payment\n- WHEN a payment completes\n- THEN a receipt is issued\n'
            '- Check: `python3 -m unittest tests.billing` exits 0\n\n'
            '## Retired\n'))

    def test_modified_replaces_the_title(self):
        out = self.fold(base_files(), fixture('delta/auth-modify.md'), [record(PASSKEY_CHECK, FINAL)])
        self.assertIn('### REQ-AUTH-01 · Sign in with a password or a passkey\n', out['auth'])
        self.assertNotIn('### REQ-AUTH-01 · Sign in with a password\n', out['auth'])

    def test_fold_keeps_given_and_and_lines(self):
        added = self.fold({}, fixture('delta/scenario-grammar.md'), [record('`python3 -m unittest tests.billing_grammar` exits 0', FINAL)])
        self.assertIn('- GIVEN a registered customer\n- WHEN the customer pays\n- AND the payment is approved\n'
                      '- THEN a receipt is issued\n- AND the receipt is emailed\n', added['billing'])
        modified = self.fold(base_files(), fixture('delta/grammar-modified.md'), [record('`python3 -m unittest tests.auth.test_grammar` exits 0', FINAL)])
        self.assertIn('- GIVEN a registered user\n- WHEN the user confirms a passkey\n- AND the passkey is valid\n'
                      '- THEN the user is signed in\n- AND a session starts\n', modified['auth'])

    def test_unknown_state_value_is_malformed(self):
        problems = self.recipe['validate'](self.recipe['parse_base'](base_files()), self.recipe['parse_delta'](fixture('delta/bad-state.md')))
        self.assertEqual([(p['kind'], p['id']) for p in problems], [('malformed', 'REQ-BILLING-01')])

    def test_removed_without_reason_is_malformed(self):
        problems = self.recipe['validate'](self.recipe['parse_base'](base_files()), self.recipe['parse_delta'](fixture('delta/no-reason.md')))
        self.assertEqual([(p['kind'], p['id']) for p in problems], [('malformed', 'REQ-AUTH-02')])

    def test_shall_and_must_match_whole_uppercase_words(self):
        problems = self.recipe['validate'](self.recipe['parse_base'](base_files()), self.recipe['parse_delta'](fixture('delta/shall-words.md')))
        self.assertEqual(sorted((p['kind'], p['id']) for p in problems),
                         [('malformed', 'REQ-BILLING-01'), ('malformed', 'REQ-BILLING-02')])

    def test_existing_domain_keeps_its_title(self):
        titled = fixture('base/auth.md').replace('# Requirements — Auth', '# Requirements — Sign-in rules', 1)
        out = self.fold({'auth': titled}, fixture('delta/auth-add.md'), [record('`python3 -m unittest tests.auth.test_lock` exits 0', FINAL)])
        self.assertTrue(out['auth'].startswith('# Requirements — Sign-in rules\n\n## Active\n'))

    def test_added_entry_keeps_every_scenario_in_order(self):
        out = self.fold({}, fixture('delta/two-scenarios.md'), [
            record('`python3 -m unittest tests.billing` exits 0', FINAL),
            record('`python3 -m unittest tests.billing_refund` exits 0', FINAL),
        ])
        self.assertIn('### REQ-BILLING-01 · Receipts are issued\n\n'
                      'The system SHALL issue a receipt for every completed payment.\n\n'
                      '#### Scenario: Completed payment\n- WHEN a payment completes\n- THEN a receipt is issued\n'
                      '- Check: `python3 -m unittest tests.billing` exits 0\n\n'
                      '#### Scenario: Refunded payment\n- WHEN a payment is refunded\n- THEN the receipt is marked refunded\n'
                      '- Check: `python3 -m unittest tests.billing_refund` exits 0\n\n## Retired\n', out['billing'])

    def test_modified_entry_keeps_every_scenario_in_order(self):
        out = self.fold(base_files(), fixture('delta/modify-two-scenarios.md'), [
            record('`python3 -m unittest tests.auth.test_passkey_sign_in` exits 0', FINAL),
            record('`python3 -m unittest tests.auth.test_password_sign_in` exits 0', FINAL),
        ])
        self.assertIn('### REQ-AUTH-01 · Sign in with a password or a passkey\n\n'
                      'The system SHALL let a user sign in with a password or a passkey.\n\n'
                      '#### Scenario: Passkey sign in\n- GIVEN a registered user\n- WHEN the user confirms a passkey\n'
                      '- AND the passkey is valid\n- THEN the user is signed in\n- AND a session starts\n'
                      '- Check: `python3 -m unittest tests.auth.test_passkey_sign_in` exits 0\n\n'
                      '#### Scenario: Password sign in\n- GIVEN a registered user\n- WHEN the user submits a password\n'
                      '- THEN the user is signed in\n- Check: `python3 -m unittest tests.auth.test_password_sign_in` exits 0\n\n',
                      out['auth'])

    def test_base_scenarios_survive_an_unrelated_fold(self):
        base_block = fixture('base/multi.md')[fixture('base/multi.md').index('### REQ-BILLING-09'):fixture('base/multi.md').index('## Retired')]
        out = self.fold({'billing': fixture('base/multi.md')}, fixture('delta/billing-unrelated.md'),
                        [record('`python3 -m unittest tests.billing_unrelated` exits 0', FINAL)])
        self.assertIn(base_block, out['billing'])

    def test_removed_requirement_keeps_both_scenarios_under_retired(self):
        out = self.fold({'billing': fixture('base/multi.md')}, fixture('delta/remove-multi.md'), [])
        self.assertTrue(out['billing'].endswith(
            '## Retired\n\n### REQ-BILLING-09 · Existing receipts\nRetired: demo-plan · 2026-10-13 · replaced\n\n'
            'The system SHALL keep existing receipts.\n\n'
            '#### Scenario: Existing\n- WHEN a receipt exists\n- THEN it is kept\n'
            '- Check: `python3 -m unittest tests.billing_existing` exits 0\n\n'
            '#### Scenario: Reissued\n- GIVEN a receipt was reissued\n- WHEN the reissue is requested\n'
            '- AND the original is found\n- THEN the reissued receipt replaces the original\n'
            '- Check: `python3 -m unittest tests.billing_reissue` exits 0\n'))

    def test_modified_check_line_is_kept(self):
        out = self.fold(base_files(), fixture('delta/auth-modify.md'), [record(PASSKEY_CHECK, FINAL)])
        self.assertIn('### REQ-AUTH-01 · Sign in with a password or a passkey\n', out['auth'])
        self.assertIn('- Check: `python3 -m unittest tests.auth.test_passkey` exits 0\n', out['auth'])

    def test_every_scenario_of_an_entry_needs_a_check(self):
        problems = self.recipe['validate'](self.recipe['parse_base'](base_files()),
                                           self.recipe['parse_delta'](fixture('delta/second-scenario-unchecked.md')))
        unchecked = sorted((p['id'], p['detail']) for p in problems if p['kind'] == 'unchecked')
        self.assertEqual([p['kind'] for p in problems], ['unchecked'] * 3)
        self.assertEqual([entry for entry, _ in unchecked], ['REQ-AUTH-01', 'REQ-BILLING-11', 'REQ-BILLING-12'])
        for (entry, detail), scenario in zip(unchecked, ('Wrong password', 'Partial refund', 'Void before capture')):
            with self.subTest(entry=entry):
                self.assertIn(scenario, detail)

if __name__ == '__main__':
    unittest.main()
