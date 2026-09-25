import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


def recipe(name, ordinal=0):
    text = (ROOT / name).read_text()
    block = text.split('```python\n')[ordinal + 1].split('\n```')[0]
    namespace = {'__name__': 'tested_recipe'}
    exec(compile(block, name, 'exec'), namespace)
    return namespace


COMPILER = recipe('references/guides/decompose-and-lint.md')
LINEAGE = recipe('references/recipes/correction-lineage.md')
LINT = recipe('references/guides/full-checks.md', 1)


def task(identity='P-01', requirement='R01'):
    return dict(id=identity, requirements=[requirement], outcome='Preserve parsed output',
                write_scope=['result.json'], inputs={'spec': 'revision-1'},
                acceptance_check='python3 check.py', regression_check='python3 regression.py',
                record='records/check', produces={}, consumes=[],
                cases=[dict(requirement=requirement, input='', expected=[], check='empty-array round trip')],
                semantic_review='passed', boundary_fixtures='passed')


def preparation(tasks=None, selected=None, available=None, requirements=None):
    tasks = tasks if tasks is not None else [task()]
    return COMPILER['prepare_tasks'](
        requirements or ['R01'], tasks, selected or ['P-01'], available or {},
        dict(contract='c1', source='s1', configuration='cfg1', dependencies='d1',
             selectors=['input.json'], runtime='Python 3'),
        [dict(owner='coordinator', check='consumer round trip', record='records/delivery')])


def row(number, files):
    source = (ROOT / 'references/guides/lint-spec.md').read_bytes()
    commands = LINT['canonical_rows'](source, hashlib.sha256(source).hexdigest(), 'sample')
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / 'docs/plans/sample'
        workspace.mkdir(parents=True)
        for name, data in files.items():
            target = workspace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(data)
        return subprocess.run(['sh', '-c', commands[number]['command'].decode()], cwd=tmp,
                              capture_output=True, text=True)


def board(state, proof='', schema=True):
    return ('Schema: tackle-workspace/3\n' if schema else '') + (
        '| Task | What | Brief | Depends on | Status | Verification |\n'
        '|---|---|---|---|---|---|\n'
        f'| P-01 | Work | points/P-01.md | none | {state} | {proof} |\n')


class TaskContracts(unittest.TestCase):
    def test_complete_brief_accepts_explicit_empty_boundary(self):
        result = preparation()
        self.assertEqual(result['states']['P-01'], 'Ready to run')
        self.assertFalse(result['execution_authorized'])
        self.assertFalse(result['product_pass'])

    def test_missing_product_decision_blocks_selected_task(self):
        item = task()
        item['pending_product_decisions'] = ['empty input policy']
        self.assertEqual(preparation([item])['states']['P-01'], 'Draft')

    def test_delegated_choice_does_not_become_blocker(self):
        item = task()
        item['technical_choices'] = ['dictionary or dataclass']
        self.assertEqual(preparation([item])['states']['P-01'], 'Ready to run')

    def test_missing_requirement_case_is_not_covered_by_id(self):
        item = task()
        item['cases'] = [dict(requirement='other', input='x', expected='x', check='identity')]
        self.assertIn('missing observable case: R01', preparation([item])['findings']['P-01'])

    def test_missing_record_or_regression_check_prevents_readiness(self):
        for key in ('record', 'regression_check', 'write_scope', 'inputs'):
            item = task()
            del item[key]
            self.assertEqual(preparation([item])['states']['P-01'], 'Draft')

    def test_missing_semantic_or_boundary_review_prevents_readiness(self):
        for key in ('semantic_review', 'boundary_fixtures'):
            item = task()
            item[key] = 'pending'
            self.assertEqual(preparation([item])['states']['P-01'], 'Draft')

    def test_milestone_retains_draft_requirement_owner(self):
        later = task('P-02', 'R02')
        later.update(milestone='release', future_check='final package reconstruction')
        later.pop('cases')
        result = preparation([task(), later], requirements=['R01', 'R02'])
        self.assertEqual(result['states'], {'P-01': 'Ready to run', 'P-02': 'Draft'})
        self.assertEqual(result['owners']['R02'], ['P-02'])

    def test_deferred_missing_future_check_is_not_hidden(self):
        later = task('P-02', 'R02')
        later['milestone'] = 'later'
        with self.assertRaisesRegex(ValueError, 'deferred'):
            preparation([task(), later], requirements=['R01', 'R02'])

    def test_unowned_requirement_and_unjustified_task_reject(self):
        with self.assertRaisesRegex(ValueError, 'unowned requirement'):
            preparation(requirements=['R01', 'R02'])
        with self.assertRaisesRegex(ValueError, 'unjustified'):
            preparation([task(requirement='R02')])

    def test_duplicate_and_missing_task_identity_reject(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            preparation([task(), task()])
        item = task()
        item['consumes'] = [dict(task='P-99', artifact='schema', interface='v1', revision='abc')]
        with self.assertRaisesRegex(ValueError, 'missing dependency'):
            preparation([item])

    def test_dependency_cycle_rejects_before_execution(self):
        first, second = task(), task('P-02', 'R02')
        for item, producer in ((first, 'P-02'), (second, 'P-01')):
            item['produces'] = {'schema': dict(interface='v1', revision='abc')}
            item['consumes'] = [dict(task=producer, artifact='schema', interface='v1', revision='abc')]
        with self.assertRaisesRegex(ValueError, 'cyclic'):
            preparation([first, second], selected=['P-01', 'P-02'], requirements=['R01', 'R02'])

    def test_existing_artifact_wrong_interface_or_revision_rejects(self):
        first, second = task(), task('P-02', 'R02')
        first.update(produces={'schema': dict(interface='v1', revision='abc')},
                     milestone='producer', future_check='schema consumer')
        second['consumes'] = [dict(task='P-01', artifact='schema', interface='v1', revision='abc')]
        for observed in ({}, {'P-01/schema': dict(interface='v1', revision='old')},
                         {'P-01/schema': dict(interface='v2', revision='abc')}):
            result = preparation([first, second], ['P-02'], observed, ['R01', 'R02'])
            self.assertEqual(result['states']['P-02'], 'Draft')
        valid = {'P-01/schema': dict(interface='v1', revision='abc')}
        result = preparation([first, second], ['P-02'], valid, ['R01', 'R02'])
        self.assertEqual(result['states']['P-02'], 'Ready to run')
        second['consumes'][0]['interface'] = 'different'
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            preparation([first, second], ['P-02'], valid, ['R01', 'R02'])

    def test_title_or_translation_does_not_change_stable_task_id(self):
        item = task()
        item['title'] = 'Tarea de exportación'
        self.assertEqual(set(preparation([item])['states']), {'P-01'})

    def test_field_aliases_preserve_value_and_reject_conflict(self):
        old = '- **Touches**: src/\n**Done-signal**: python3 check.py\n'
        new = '- **Write scope**: src/\n**Acceptance check**: python3 check.py\n'
        parse = COMPILER['task_fields']
        self.assertEqual(parse(old), parse(new))
        self.assertEqual(parse("**Touches:** src/\n**Run:** python3 check.py\n"), parse(new))
        self.assertEqual(parse(old + new), parse(new))
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            parse(old + '**Write scope**: unrelated/\n')

    def test_split_merge_share_original_cycle_pool(self):
        events = [dict(cycle_id=f'c{i}', pool_id='original', kind='failed-correction') for i in range(3)]
        pools = LINEAGE['transfer_lineage'](['failure'], {'P-02': ['failure'], 'P-03': ['failure']},
                                          ['failure'], {'failure': 'original'})
        for assigned in pools.values():
            self.assertTrue(LINEAGE['correction_usage'](events, assigned)['exhausted'])
        merged = pools['P-02'] + pools['P-03']
        self.assertEqual(LINEAGE['correction_usage'](events + [events[0]], merged)['spent'], 3)

    def test_unrelated_work_is_not_charged_old_cycles(self):
        events = [dict(cycle_id='c1', pool_id='old', kind='failed-correction')]
        self.assertEqual(LINEAGE['correction_usage'](events, ['new'])['spent'], 0)
        with self.assertRaisesRegex(ValueError, 'lineage'):
            LINEAGE['transfer_lineage'](['old'], {'P-02': []}, ['old'], {'old': 'old-pool'})

    def test_conflicting_cycle_id_rejects_instead_of_reset(self):
        event = dict(cycle_id='one', pool_id='old', kind='failed-correction')
        altered = dict(event, pool_id='new')
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            LINEAGE['correction_usage']([event, altered], ['new'])

    def test_unowned_integration_pool_is_exhausted_at_two(self):
        self.assertEqual((LINEAGE['TASK_POOL_LIMIT'], LINEAGE['UNOWNED_INTEGRATION_POOL_LIMIT']), (3, 2))
        events = [dict(cycle_id=f'i{i}', pool_id='integration', kind='failed-correction') for i in range(2)]
        limit = {'integration': LINEAGE['UNOWNED_INTEGRATION_POOL_LIMIT']}
        one = LINEAGE['correction_usage'](events[:1], ['integration'], limit)
        self.assertEqual((one['spent'], one['remaining'], one['exhausted']), (1, 1, False))
        two = LINEAGE['correction_usage'](events, ['integration'], limit)
        self.assertEqual((two['spent'], two['remaining'], two['exhausted']), (2, 0, True))
        as_task_pool = LINEAGE['correction_usage'](events, ['integration'])
        self.assertEqual((as_task_pool['remaining'], as_task_pool['exhausted']), (1, False))
        for invented in ({'integration': 5}, {'integration': 1}, {'unselected': 2}):
            with self.assertRaisesRegex(ValueError, 'pool limit'):
                LINEAGE['correction_usage'](events, ['integration'], invented)

    def test_legacy_board_states_still_read_without_upgrading(self):
        for state in ('🔴', '🟡', '⏸', '🟢', '⚪'):
            result = row(3, {'board.md': board(state, schema=False)})
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        result = row(10, {'board.md': board('🟢', schema=False)})
        self.assertIn('without grade', result.stdout)

    def test_v3_states_need_explicit_schema(self):
        for state in ('Draft', 'Ready to run', 'In progress', 'Checking', 'Complete', 'Blocked',
                      'Interrupted', 'Skipped', 'Unverifiable'):
            self.assertEqual(row(3, {'board.md': board(state)}).stdout, '')
            self.assertIn('bad status', row(3, {'board.md': board(state, schema=False)}).stdout)
        self.assertIn('bad status', row(3, {'board.md': board('Success-ish')}).stdout)

    def test_v3_terminal_state_requires_task_record_reference(self):
        for state in ('Complete', 'Blocked', 'Unverifiable'):
            self.assertIn('without verification', row(10, {'board.md': board(state)}).stdout)
            self.assertEqual(row(10, {'board.md': board(state, 'reports/P-01-report.md')}).stdout, '')

    def test_v3_complete_still_requires_report_and_usage(self):
        files = {'board.md': board('Complete', 'reports/P-01-report.md'), 'usage.md': '# Usage\n'}
        self.assertIn('without closure report', row(14, files).stdout)
        self.assertNotEqual(row(11, files).returncode, 0)
        files.update({'reports/P-01-report.md': 'Command result with raw pointer\n',
                      'usage.md': '| role | P-01 | observed |\n'})
        self.assertEqual(row(14, files).stdout, '')
        self.assertEqual(row(11, files).returncode, 0)

    def test_v3_task_heading_preserves_dependency_identity_checks(self):
        files = {'plan.md': '## 5. Task decomposition\n| **P-01 · Work** | one |\n',
                 'board.md': board('Draft'), 'points/P-01.md': '# Task P-01\n- **Depends on**: P-99\n'}
        self.assertIn('unresolved: P-99', row(2, files).stdout)
        files['points/P-01.md'] = '# Task P-01\n- **Depends on**: none\n'
        self.assertEqual(row(2, files).stdout, '')

    def test_legacy_named_ids_are_stable_and_unsafe_ids_reject(self):
        for identity in ('P-tc-core', 'P-s27-greet'):
            item = task(identity)
            self.assertEqual(preparation([item], [identity])['states'][identity], 'Ready to run')
        for identity in ('../P-01', 'P-01/path', 'P-01;echo'):
            with self.assertRaisesRegex(ValueError, 'identity'):
                preparation([task(identity)], [identity])

    def test_board_migration_preserves_states_grades_and_original_bytes(self):
        convert = recipe('maintaining/migrations.md')['candidate_board']
        original = board('🟢', 'E1', schema=False)
        before = original.encode()
        candidate, legacy = convert(original, {'reports/P-01-report.md'})
        self.assertEqual(original.encode(), before)
        self.assertIn('| Complete | reports/P-01-report.md |', candidate)
        self.assertEqual(legacy, {'P-01': {'status': '🟢', 'grade': 'E1'}})
        self.assertEqual(row(3, {'board.md': candidate}).stdout, '')
        with self.assertRaisesRegex(ValueError, 'missing historical'):
            convert(original, set())
        with self.assertRaisesRegex(ValueError, 'unsupported legacy'):
            convert(original + '| P-01/path | invalid | brief | none | 🔴 | |\n', {'reports/P-01-report.md'})
        with self.assertRaisesRegex(ValueError, 'already adopted'):
            convert(candidate, {'reports/P-01-report.md'})

    def test_board_migration_never_infers_readiness_or_acceptance(self):
        convert = recipe('maintaining/migrations.md')['candidate_board']
        result, legacy = convert(board('🔴', schema=False), set())
        self.assertIn('| Draft |', result)
        self.assertNotIn('Ready to run', result)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            convert(board('🔴', schema=False) + '| P-01 | repeated | brief | none | 🔴 | |\n', set())

    def test_board_migration_ignores_fenced_examples_and_rejects_unclosed_fence(self):
        convert = recipe('maintaining/migrations.md')['candidate_board']
        for fence in ('```', '````', '~~~', '~~~~'):
            original = board('🔴', schema=False)
            example = '| P-99 | Example only | points/P-99.md | none | 🔴 | |\n'
            candidate, legacy = convert(original + fence + 'markdown\n' + example + fence + '\n', set())
            self.assertEqual(set(legacy), {'P-01'})
            self.assertNotIn('P-99', candidate)
            with self.assertRaisesRegex(ValueError, 'unclosed'):
                convert(original + fence + '\n' + example, set())

    def test_merge_retains_distinct_allowances_and_shared_event_identity(self):
        events = [dict(cycle_id=f'{pool}-{i}', pool_id=pool, kind='failed-correction')
                  for pool in ('left', 'right') for i in range(2)]
        result = LINEAGE['correction_usage'](events, ['left', 'right'])
        self.assertEqual(result['spent'], 4)
        self.assertEqual(result['pools'], {'left': 2, 'right': 2})
        self.assertFalse(result['exhausted'])
        shared = dict(cycle_id='joint', pool_ids=['left', 'right'], kind='failed-correction')
        result = LINEAGE['correction_usage'](events + [shared, shared], ['left', 'right'])
        self.assertEqual(result['spent'], 5)
        self.assertEqual(result['pools'], {'left': 3, 'right': 3})
        self.assertTrue(result['exhausted'])

    def test_new_workspace_runs_all_canonical_rows(self):
        source = (ROOT / 'references/guides/lint-spec.md').read_bytes()
        commands = LINT['canonical_rows'](source, hashlib.sha256(source).hexdigest(), 'sample')
        files = {'plan.md': '## 5. Task decomposition\n| **P-01 · Work** | one |\n',
                 'board.md': board('Ready to run'),
                 'points/P-01.md': '# Task P-01\n- **Depends on**: none\n- **Write scope**: src/\n- **Effort**: high\n',
                 'decisions.md': '# Decisions\n', 'reference.md': '# References\n',
                 'log.md': '# History\n\n## 2026-09-22 · prepared\nReady records are indexed.\n',
                 'usage.md': '# Resource usage\n\nSchema: tackle-observability/2\n\n| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n'}
        for number in range(1, 17):
            result = row(number, files)
            record = dict(child_exit=result.returncode, timeout=False, launch_error=None,
                          signal=None, inputs_stable=True, artifacts_present=True)
            verdict = LINT['lint_verdict'](number, record, result.stdout.encode(), result.stderr.encode())
            self.assertEqual(verdict, 'PASS', (number, result.stdout, result.stderr))
        self.assertEqual(set(commands), set(range(1, 17)))

    def test_new_status_declaration_outside_board_is_rejected(self):
        files = {'plan.md': '# Plan\n', 'board.md': board('Draft'),
                 'points/P-01.md': '# Task P-01\n**Status**: Complete\n'}
        result = row(5, files)
        self.assertIn('duplicated Status', result.stdout)
        self.assertEqual(result.returncode, 0)
        files['points/P-01.md'] = '# Task P-01\n```text\n**Status**: example\n```\n'
        result = row(5, files)
        self.assertEqual((result.returncode, result.stdout), (1, ''))

    def test_new_write_scope_and_checking_detect_cross_workspace_collision(self):
        files = {'plan.md': '# Plan\n', 'board.md': board('Checking'),
                 'points/P-01.md': '# Task P-01\n- **Write scope**: src/\n',
                 '../neighbor/board.md': board('In progress'),
                 '../neighbor/points/P-01.md': '# Task P-01\n- **Touches**: src/result.py\n'}
        self.assertIn('collision: ', row(8, files).stdout)

    def test_missing_or_wrong_typed_fingerprints_cannot_mark_ready(self):
        valid = dict(contract='c1', source='s1', configuration='cfg1', dependencies='none',
                     selectors={'optional.txt': []}, runtime='Python 3')
        delivery = [dict(owner='coordinator', check='round trip', record='records/delivery')]
        for key in valid:
            for missing in (None, '', {}, [], False, 0):
                changed = dict(valid, **{key: missing})
                with self.assertRaisesRegex(ValueError, 'fingerprint'):
                    COMPILER['prepare_tasks'](['R01'], [task()], ['P-01'], {}, changed, delivery)
        result = COMPILER['prepare_tasks'](['R01'], [task()], ['P-01'], {}, valid, delivery)
        self.assertEqual(result['states']['P-01'], 'Ready to run')


    def test_retro_queries_read_both_state_formats_without_counting_other_columns(self):
        template = (ROOT / 'references/retro.tmpl.md').read_text()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'board.md').write_text(board('Complete') +
                '| P-02 | Legacy | brief | none | 🟢 | E1 |\n' +
                '| P-03 | Complete 🟢 example | brief | none | In progress | |\n')
            (root / 'log.md').write_text('## 2026-09-22\nP-01 Complete → In progress\n'
                'P-02 🟢 → 🟡\nP-03 Blocked\nP-04 ⏸\n')
            for metric, expected in [('Comprehension debt', ['P-01', 'P-02']),
                                     ('Reopened tasks', ['P-01', 'P-02']),
                                     ('Blocked durations', ['P-03', 'P-04'])]:
                command = template.split('| ' + metric + ' | `', 1)[1].split('`', 1)[0]
                result = subprocess.run(['sh', '-c', command], cwd=root, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(all(identity in result.stdout for identity in expected), result.stdout)
                if metric == 'Comprehension debt':
                    self.assertNotIn('P-03', result.stdout)


if __name__ == '__main__':
    unittest.main()
