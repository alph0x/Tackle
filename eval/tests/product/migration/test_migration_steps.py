"""E2E tests for the schema-keyed migration recipes.

Each recipe file (`references/recipes/migrate/*.md`) is one fenced Python block, loaded exactly the
way this repository already loads recipes elsewhere (`eval/lint/task-contracts/test_task_contracts.py`'s
`recipe()`, `eval/templates/test_template_drift.py`'s module-level `exec`): read the file, take
its one fenced block, `exec` it into a namespace. `schema.md`'s block is loaded first and its names are
passed into each step's namespace, so every step calls the same `schema_of`/`parse_board`/... instead
of keeping its own copy that could silently diverge from it.

Fixtures live under `fixtures/` as bare workspace roots (`<case>/before/`, `<case>/after/` where an
exact after-shape is asserted, or a flat directory for detection/refusal probes) -- never under a
`docs/plans/` path, so nothing here is swallowed by the repository's `docs/plans/` or `eval/**/runs/`
gitignore rules. `census.py` reads real local workspaces separately and is not a `test_*.py`
file, so it is never discovered by the suite registry.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
import sys
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)

RECIPES = INSTALL / 'references/recipes/migrate'
FIXTURES = (Path(__file__).resolve().parents[4] / 'eval/migration') / 'fixtures'


def load_block(path, namespace=None):
    text = path.read_text(encoding='utf-8')
    block = text.split('```python\n', 1)[1].split('\n```', 1)[0]
    ns = dict(namespace or {})
    ns['__name__'] = 'tackle_migration_' + path.stem.replace('-', '_')
    exec(compile(block, str(path), 'exec'), ns)
    return ns


def load_files(directory):
    return {str(p.relative_to(directory)).replace('\\', '/'): p.read_bytes()
            for p in directory.rglob('*') if p.is_file()}


SCHEMA = load_block(RECIPES / 'schema.md')
STEP_PRE3_TO_3 = load_block(RECIPES / 'step-pre3-to-3.md', SCHEMA)
STEP_3_TO_4 = load_block(RECIPES / 'step-3-to-4.md', SCHEMA)
STEP_4_TO_5 = load_block(RECIPES / 'step-4-to-5.md', SCHEMA)
STEPS = (STEP_PRE3_TO_3, STEP_3_TO_4, STEP_4_TO_5)

CONTEXT_84 = {'date': '2026-09-25', 'run_id': 'migration-fixture-1', 'methodology': 'Tackle 8.4.0'}
CONTEXT_90 = {'date': '2026-09-25', 'run_id': 'migration-fixture-1', 'methodology': 'Tackle 9.0.0'}


class RecipesLoadTests(unittest.TestCase):
    """The four recipe files exist, each is exactly one fenced Python block, and schema.md's shared
    names actually reach every step."""

    def test_four_recipe_files_exist_with_one_python_block_and_nothing_else(self):
        # references/recipes/README.md: "Each recipe is a Markdown file that holds one fenced code
        # block and nothing else" -- matching the existing precedent, correction-lineage.md, which is
        # exactly `` ```python\n...\n``` `` with no heading or prose outside the fence.
        for name in ('schema.md', 'step-pre3-to-3.md', 'step-3-to-4.md', 'step-4-to-5.md'):
            path = RECIPES / name
            text = path.read_text()
            self.assertTrue(path.is_file(), name)
            self.assertEqual(text.count('```'), 2, name)
            self.assertTrue(text.startswith('```python\n'), name)
            self.assertTrue(text.endswith('\n```\n'), name)

    def test_every_step_shares_schema_ofs_namespace(self):
        for step in STEPS:
            self.assertIs(step['schema_of'], SCHEMA['schema_of'])
            self.assertIs(step['parse_board'], SCHEMA['parse_board'])


class SchemaDetectionTests(unittest.TestCase):
    """C1: one fixture per bucket, plus a legacy-3/ directory beside a /4 board."""

    def bucket(self, name):
        return SCHEMA['schema_of'](load_files(FIXTURES / 'detect' / name))

    def test_pre3(self):
        self.assertEqual(self.bucket('pre3'), 'pre-3')

    def test_three(self):
        self.assertEqual(self.bucket('three'), '3')

    def test_four(self):
        self.assertEqual(self.bucket('four'), '4')

    def test_five(self):
        self.assertEqual(self.bucket('five'), '5')

    def test_lite(self):
        self.assertEqual(self.bucket('lite'), 'lite')

    def test_four_with_legacy_three_beside_it_is_still_four(self):
        files = load_files(FIXTURES / 'detect/four-with-legacy')
        self.assertIn('legacy-3/board.md', files)
        self.assertEqual(SCHEMA['schema_of'](files), '4')

    def test_both_board_files_is_unknown(self):
        self.assertEqual(self.bucket('unknown-both-boards'), 'unknown')

    def test_lite_plan_beside_a_board_is_unknown(self):
        self.assertEqual(self.bucket('unknown-lite-and-board'), 'unknown')

    def test_nothing_recognizable_is_unknown(self):
        self.assertEqual(self.bucket('unknown-empty'), 'unknown')

    def test_schema_line_inside_a_fence_is_ignored(self):
        # The only unfenced content here is pre-3 shaped; a fenced 'Schema: tackle-workspace/3' must
        # not be read as a real declaration.
        self.assertEqual(self.bucket('unknown-fenced-schema'), 'pre-3')


class StepPre3To3Tests(unittest.TestCase):
    """C2: a board with all five legacy states, P-ids and T-ids, a fenced example, and a Complete
    row with its report."""

    def setUp(self):
        self.before = load_files(FIXTURES / 'pre3-to-3/before')
        self.after, self.legacy = STEP_PRE3_TO_3['transform'](self.before, CONTEXT_84)

    def test_detect_true_before_false_after(self):
        self.assertTrue(STEP_PRE3_TO_3['detect'](self.before))
        self.assertFalse(STEP_PRE3_TO_3['detect'](self.after))

    def test_bucket_after_is_3(self):
        self.assertEqual(SCHEMA['schema_of'](self.after), '3')

    def test_exact_after_board(self):
        expected = (
            '# Task board\n\nSchema: tackle-workspace/3\n\n'
            '| Task | What | Brief | Depends on | Status | Verification |\n'
            '|---|---|---|---|---|---|\n'
            '| P-01 | Draft work | points/P-01-draft.md | none | Draft |  |\n'
            '| P-02 | Active work | points/P-02-active.md | P-01 | In progress |  |\n'
            '| P-03 | Blocked work | points/P-03-blocked.md | P-01 | Blocked | reports/P-03-report.md |\n'
            '| T-04 | Done work | points/T-04-done.md | P-01 | Complete | reports/T-04-report.md |\n'
            '| P-05 | Skipped slice | points/P-05-skipped.md | none | Skipped |  |\n'
        )
        self.assertEqual(self.after['board.md'].decode(), expected)

    def test_fenced_example_row_never_appears(self):
        self.assertNotIn('P-99', self.after['board.md'].decode())

    def test_no_inferred_ready(self):
        self.assertNotIn('Ready to run', self.after['board.md'].decode())

    def test_p_and_t_ids_both_accepted(self):
        self.assertIn('| P-01 |', self.after['board.md'].decode())
        self.assertIn('| T-04 |', self.after['board.md'].decode())

    def test_legacy_mapping_returned(self):
        self.assertEqual(self.legacy, {
            'P-01': {'status': '\U0001F534', 'grade': '—'},
            'P-02': {'status': '\U0001F7E1', 'grade': 'E0'},
            'P-03': {'status': '⏸', 'grade': 'E0'},
            'T-04': {'status': '\U0001F7E2', 'grade': 'E1'},
            'P-05': {'status': '⚪', 'grade': '—'},
        })

    def test_methodology_line_updated_in_place(self):
        text = self.after['AGENTS.md'].decode()
        self.assertIn('**Methodology: Tackle 8.4.0**', text)
        self.assertIn('<!-- A future version reads this to decide whether to migrate. -->', text)

    def test_reports_and_evidence_pass_through_untouched(self):
        self.assertEqual(self.after['reports/T-04-report.md'], self.before['reports/T-04-report.md'])
        self.assertEqual(self.after['evidence/T-04/raw.txt'], self.before['evidence/T-04/raw.txt'])

    def test_verify_is_clean(self):
        result = STEP_PRE3_TO_3['verify'](self.before, self.after)
        self.assertEqual(result, {'errors': [], 'residue': []})

    # -- Columns located by header name, never by position ------------------------------------

    def test_columns_located_by_name_regardless_of_order(self):
        # The coordinator's own reordered shape: Confidence and Status both appear before Brief and
        # What. A position-based reader (the pre-fix code always read cells[1..3] relative to
        # Status) would scramble every cell here; a name-based reader must not.
        board = ('# Board — reordered columns\n\n'
                 '| Point | Confidence | Status | Brief | What | Depends on |\n'
                 '|---|---|---|---|---|---|\n'
                 '| P-01 | E2 | \U0001F534 | briefing-text.md | Some real what text | none |\n')
        files = {'board.md': board.encode()}
        self.assertEqual(SCHEMA['schema_of'](files), 'pre-3')
        after, legacy = STEP_PRE3_TO_3['transform'](files, CONTEXT_84)
        expected_row = '| P-01 | Some real what text | briefing-text.md | none | Draft |  |'
        self.assertIn(expected_row, after['board.md'].decode())
        self.assertEqual(legacy['P-01']['grade'], 'E2')
        self.assertEqual(STEP_PRE3_TO_3['verify'](files, after)['errors'], [])

    def test_verify_catches_a_scrambled_what_cell(self):
        # Insurance against a regression back to positional reading: even when transform() is not
        # touched, verify() must independently notice a What cell that no longer matches its source.
        before = load_files(FIXTURES / 'pre3-to-3/before')
        after, _ = STEP_PRE3_TO_3['transform'](before, CONTEXT_84)
        mutated = dict(after)
        mutated['board.md'] = after['board.md'].replace(b'Draft work', b'SCRAMBLED')
        result = STEP_PRE3_TO_3['verify'](before, mutated)
        self.assertTrue(any('P-01' in error and 'What' in error for error in result['errors']), result)

    def test_dropped_row_is_caught_by_verify(self):
        before = load_files(FIXTURES / 'pre3-to-3/before')
        after, _ = STEP_PRE3_TO_3['transform'](before, CONTEXT_84)
        mutated = dict(after)
        lines = mutated['board.md'].decode().split('\n')
        mutated['board.md'] = '\n'.join(line for line in lines if not line.startswith('| P-01 |')).encode()
        result = STEP_PRE3_TO_3['verify'](before, mutated)
        self.assertTrue(any('P-01' in error and 'dropped' in error for error in result['errors']), result)

    def test_nonstandard_column_layout_refused(self):
        # This reproduction shape (Point | Status | Preparation | Confidence | Note), as a
        # synthetic fixture -- never the real workspace content the review found it on.
        files = load_files(FIXTURES / 'refusals/pre3-nonstandard-columns')
        self.assertEqual(SCHEMA['schema_of'](files), 'pre-3')
        with self.assertRaisesRegex(ValueError, 'unrecognized pre-3 header layout'):
            STEP_PRE3_TO_3['transform'](files, CONTEXT_84)

    def test_ambiguous_duplicate_column_names_refused(self):
        board = ('# Board — ambiguous columns\n\n'
                 '| Point | Task | What | Brief | Depends on | Status | Confidence |\n'
                 '|---|---|---|---|---|---|---|\n'
                 '| P-01 | P-01 | Work | b.md | none | \U0001F534 | E0 |\n')
        with self.assertRaisesRegex(ValueError, 'unrecognized pre-3 header layout'):
            STEP_PRE3_TO_3['transform']({'board.md': board.encode()}, CONTEXT_84)

    def test_preexisting_verification_text_refused_rather_than_silently_discarded(self):
        # A pre-3 header may spell its last column 'Verification' instead of 'Confidence' (the
        # coordinator's named synonym). Unlike a short Confidence grade, real Verification text is a
        # citation the schema-3 board can carry forward -- so if it disagrees with the report path
        # this step would compute, refuse instead of quietly overwriting it.
        board = ('# Board — verification column fixture\n\n'
                 '| Point | What | Briefing | Depends on | Status | Verification |\n'
                 '|---|---|---|---|---|---|\n'
                 '| P-01 | Some work | points/P-01.md | none | \U0001F534 | ready: D-99 |\n')
        with self.assertRaisesRegex(ValueError, 'Verification'):
            STEP_PRE3_TO_3['transform']({'board.md': board.encode()}, CONTEXT_84)

    def test_preexisting_verification_text_matching_the_computed_report_is_accepted(self):
        board = ('# Board — verification column fixture\n\n'
                 '| Point | What | Briefing | Depends on | Status | Verification |\n'
                 '|---|---|---|---|---|---|\n'
                 '| P-01 | Some work | points/P-01.md | none | \U0001F7E2 | reports/P-01-report.md |\n')
        files = {'board.md': board.encode(), 'reports/P-01-report.md': b'# P-01 report\n'}
        after, _ = STEP_PRE3_TO_3['transform'](files, CONTEXT_84)
        self.assertIn('| P-01 | Some work | points/P-01.md | none | Complete | reports/P-01-report.md |',
                      after['board.md'].decode())

    def test_preexisting_placeholder_verification_text_is_accepted(self):
        board = ('# Board — verification column fixture\n\n'
                 '| Point | What | Briefing | Depends on | Status | Verification |\n'
                 '|---|---|---|---|---|---|\n'
                 '| P-01 | Some work | points/P-01.md | none | \U0001F534 | — |\n')
        files = {'board.md': board.encode()}
        after, _ = STEP_PRE3_TO_3['transform'](files, CONTEXT_84)
        self.assertIn('| P-01 | Some work | points/P-01.md | none | Draft |  |', after['board.md'].decode())


class Step3To4Tests(unittest.TestCase):
    """C3: a /3 workspace with points/, log.md, usage.md (with Complete rows), bare and '# Point'
    brief headings, an interrupted and pinned task; and a /3 workspace already on tasks/ and
    T-ids."""

    def setUp(self):
        self.before = load_files(FIXTURES / '3-to-4/before')
        self.after, self.id_map = STEP_3_TO_4['transform'](self.before, CONTEXT_84)

    def test_detect_true_before_false_after(self):
        self.assertTrue(STEP_3_TO_4['detect'](self.before))
        self.assertFalse(STEP_3_TO_4['detect'](self.after))

    def test_bucket_after_is_4(self):
        self.assertEqual(SCHEMA['schema_of'](self.after), '4')

    def test_id_map_recorded(self):
        self.assertEqual(self.id_map, {'P-01': 'T-01', 'P-02': 'T-02', 'P-03': 'T-03'})

    def test_exact_after_board(self):
        expected = (
            '# Task board — 3 to 4 fixture\n\nSchema: tackle-workspace/4\n\n'
            '| Task | What | Brief | Depends on | Status | Verification |\n'
            '|---|---|---|---|---|---|\n'
            '| T-01 | Bare heading work | tasks/T-01-bare.md | none | Complete | reports/T-01-report.md |\n'
            '| T-02 | Point heading work | tasks/T-02-point.md | T-01 | Draft |  |\n'
            '| T-03 | Interrupted work | tasks/T-03-interrupted.md | T-01 | Interrupted |  |\n'
        )
        self.assertEqual(self.after['task-board.md'].decode(), expected)
        self.assertNotIn('board.md', self.after)

    def test_bare_heading_becomes_task_heading(self):
        self.assertTrue(self.after['tasks/T-01-bare.md'].decode().startswith('# Task T-01 — Bare heading work\n'))

    def test_point_heading_becomes_task_heading(self):
        self.assertTrue(self.after['tasks/T-02-point.md'].decode().startswith('# Task T-02 — Point heading work\n'))

    def test_interrupted_task_keeps_its_state_and_pinned_procedure(self):
        board_text = self.after['task-board.md'].decode()
        self.assertIn('| T-03 | Interrupted work | tasks/T-03-interrupted.md | T-01 | Interrupted |  |', board_text)
        brief_text = self.after['tasks/T-03-interrupted.md'].decode()
        self.assertIn('Pinned procedure: legacy execution.', brief_text)
        self.assertIn("Interrupted after step 2; resume only at this task's boundary.", brief_text)

    def test_plan_section_5_ids_mapped(self):
        text = self.after['plan.md'].decode()
        self.assertIn('| T-01 | Bare heading work |', text)
        self.assertIn('| T-02 | Point heading work |', text)
        self.assertIn('| T-03 | Interrupted work |', text)
        self.assertNotRegex(text, r'\bP-0[123]\b')

    def test_report_renamed_and_id_mapped_including_its_raw_record_reference(self):
        self.assertNotIn('reports/P-01-report.md', self.after)
        self.assertIn('reports/T-01-report.md', self.after)
        self.assertIn('verification-records/T-01/raw.txt', self.after['reports/T-01-report.md'].decode())

    def test_evidence_directory_renamed_id_mapped_bytes_untouched(self):
        self.assertNotIn('evidence/P-01/raw.txt', self.after)
        self.assertEqual(self.after['verification-records/T-01/raw.txt'], self.before['evidence/P-01/raw.txt'])

    def test_history_keeps_original_bytes_plus_one_appended_entry(self):
        original = self.before['log.md'].decode()
        migrated = self.after['history.md'].decode()
        self.assertTrue(migrated.startswith(original))
        appended = migrated[len(original):]
        self.assertEqual(appended.count('\n## '), 1)
        self.assertIn('adoption', appended)
        self.assertIn('tackle-workspace/4', appended)
        self.assertNotIn('board.md', self.after)  # log.md itself no longer exists at root
        self.assertNotIn('log.md', self.after)

    def test_usage_ledger_keeps_its_8_column_format_ids_mapped(self):
        text = self.after['resource-usage.md'].decode()
        self.assertIn('| Point | Role | Tier | Model | Effort | Tokens in | Tokens out | Session |', text)
        self.assertIn('| T-01 | Executor |', text)
        self.assertNotIn('P-01', text)

    def test_decisions_and_design_contract_never_rewritten(self):
        self.assertEqual(self.after['decisions.md'], self.before['decisions.md'])
        self.assertEqual(self.after['design-contract.md'], self.before['design-contract.md'])

    def test_residue_flags_the_interrupted_task_for_its_own_boundary(self):
        result = STEP_3_TO_4['verify'](self.before, self.after)
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['residue']), 1)
        self.assertIn('T-03', result['residue'][0])
        self.assertIn('R-MIGRATE-02', result['residue'][0])

    def test_already_modern_workspace_only_gets_board_renamed_and_restamped(self):
        before = load_files(FIXTURES / '3-to-4-already-modern/before')
        after, id_map = STEP_3_TO_4['transform'](before, CONTEXT_84)
        self.assertEqual(id_map, {})
        self.assertNotIn('points', ''.join(p.split('/')[0] for p in after))
        self.assertNotIn('board.md', after)
        self.assertEqual(after['tasks/T-01.md'], before['tasks/T-01.md'])
        self.assertEqual(after['reports/T-01-report.md'], before['reports/T-01-report.md'])
        text = after['task-board.md'].decode()
        self.assertIn('Schema: tackle-workspace/4', text)
        self.assertIn('| T-01 | Already modern | tasks/T-01.md | none | Complete | reports/T-01-report.md |', text)
        result = STEP_3_TO_4['verify'](before, after)
        self.assertEqual(result, {'errors': [], 'residue': []})

    # -- history.md handling (only log.md; only history.md; both -> refusal) ---------------------

    def test_history_md_alone_is_kept_and_gets_one_adoption_entry(self):
        before = dict(load_files(FIXTURES / '3-to-4/before'))
        original_history = before.pop('log.md')
        before['history.md'] = original_history
        after, _ = STEP_3_TO_4['transform'](before, CONTEXT_84)
        migrated = after['history.md'].decode()
        self.assertTrue(migrated.startswith(original_history.decode()))
        appended = migrated[len(original_history.decode()):]
        self.assertEqual(appended.count('\n## '), 1)
        self.assertIn('adoption', appended)
        result = STEP_3_TO_4['verify'](before, after)
        self.assertEqual(result['errors'], [])

    def test_both_log_and_history_present_refused(self):
        before = dict(load_files(FIXTURES / '3-to-4/before'))
        before['history.md'] = b'STRAY PRE-EXISTING HISTORY.MD CONTENT, MUST NOT VANISH\n'
        snapshot = dict(before)
        with self.assertRaisesRegex(ValueError, 'rename target collision'):
            STEP_3_TO_4['transform'](before, CONTEXT_84)
        self.assertEqual(before, snapshot)

    def test_history_adoption_entry_is_not_duplicated_when_already_present(self):
        # "The entry is written exactly once. A second run appends nothing, because the entry is
        # detected." -- simulate a history file that already carries the marker (e.g. a hand-authored
        # entry, or the result of an earlier partial run) while the board is still /3, and confirm the
        # marker is not repeated.
        before = dict(load_files(FIXTURES / '3-to-4/before'))
        before['log.md'] = (before['log.md'].decode() +
                             '\n## 2020-01-01 · adoption · migrated to schema tackle-workspace/4\n\n'
                             '- Adopted earlier: none.\n').encode()
        after, _ = STEP_3_TO_4['transform'](before, CONTEXT_84)
        migrated = after['history.md'].decode()
        self.assertEqual(migrated.count('adoption · migrated to schema tackle-workspace/4'), 1)
        self.assertTrue(migrated.startswith(before['log.md'].decode()))

    def test_marker_phrase_quoted_in_prose_vs_a_real_adoption_heading(self):
        # A recheck finding: the idempotency guard was a bare substring
        # test of HISTORY_ADOPTION_MARKER, so an unrelated line that merely quotes the marker phrase
        # (e.g. a session note discussing this migration tooling itself) silently suppressed the
        # run's real adoption entry. The guard must instead recognize only the exact '## <date> ·
        # <marker>' heading line transform() itself writes. Measured by counting occurrences of
        # *today's* dated heading (CONTEXT_84['date']), so a pre-existing, differently-dated mention
        # (real or quoted) can never be confused with a genuine new entry from this run.
        today_heading = CONTEXT_84['date'] + ' · adoption · migrated to schema tackle-workspace/4'
        cases = (
            ('quoted in unrelated prose, not a heading',
             '\n## 2020-01-01 · session note\n\n'
             '- Discussed the tooling\'s own "adoption · migrated to schema tackle-workspace/4" '
             'marker phrase.\n',
             1),
            ('already a real adoption heading',
             '\n## 2020-01-01 · adoption · migrated to schema tackle-workspace/4\n\n'
             '- Adopted earlier: none.\n',
             0),
        )
        for label, addition, expected_new_entries in cases:
            with self.subTest(label):
                before = dict(load_files(FIXTURES / '3-to-4/before'))
                before['log.md'] = (before['log.md'].decode() + addition).encode()
                after, id_map = STEP_3_TO_4['transform'](before, CONTEXT_84)
                self.assertTrue(id_map, 'fixture is expected to have real P-ids to map')
                migrated = after['history.md'].decode()
                self.assertTrue(migrated.startswith(before['log.md'].decode()))
                self.assertEqual(migrated.count(today_heading), expected_new_entries, migrated)

    # -- A rename target collision is a named refusal, nothing written --------------------------

    def _minimal_board(self, status='Draft', verification=' '):
        return ('# Task board\n\nSchema: tackle-workspace/3\n\n'
                '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
                '| P-01 | First | points/P-01.md | none | %s |%s|\n') % (status, verification)

    def test_rename_collision_board_and_task_board_refused(self):
        files = {'board.md': self._minimal_board().encode(), 'task-board.md': b'STRAY pre-existing content\n'}
        snapshot = dict(files)
        with self.assertRaisesRegex(ValueError, 'rename target collision'):
            STEP_3_TO_4['transform'](files, CONTEXT_84)
        self.assertEqual(files, snapshot)

    def test_rename_collision_usage_and_resource_usage_refused(self):
        files = {'board.md': self._minimal_board().encode(), 'usage.md': b'| P-01 | real ledger row |\n',
                 'resource-usage.md': b'STRAY PRE-EXISTING resource-usage.md CONTENT, SHOULD NOT VANISH\n'}
        with self.assertRaisesRegex(ValueError, 'rename target collision'):
            STEP_3_TO_4['transform'](files, CONTEXT_84)

    def test_rename_collision_points_dir_and_tasks_dir_refused(self):
        files = {'board.md': self._minimal_board().encode(),
                 'points/P-01.md': b'OLD real content, must not vanish\n',
                 'tasks/P-01.md': b'STRAY pre-existing content\n'}
        with self.assertRaisesRegex(ValueError, 'rename target collision'):
            STEP_3_TO_4['transform'](files, CONTEXT_84)

    # -- The leftover-id residue scan also covers resource-usage.md ------------------------------

    def test_leftover_id_in_resource_usage_is_flagged_as_residue(self):
        before = dict(load_files(FIXTURES / '3-to-4/before'))
        before['usage.md'] = (before['usage.md'].decode() +
                               '| P-99 | Executor | n/a | n/a | high | n/a | n/a | s9 |\n').encode()
        after, _ = STEP_3_TO_4['transform'](before, CONTEXT_84)
        self.assertIn('P-99', after['resource-usage.md'].decode())
        result = STEP_3_TO_4['verify'](before, after)
        self.assertTrue(any('P-99' in item for item in result['residue']), result)

    # -- AGENTS.md's own prose is scanned for stale names and ids, boundary-aware -----------------

    def test_agents_md_stale_names_and_ids_flagged_as_residue(self):
        before = dict(load_files(FIXTURES / '3-to-4/before'))
        before['AGENTS.md'] = (before['AGENTS.md'].decode() +
                                '\n## File map\n\nboard.md, log.md, usage.md, points/ and P-01 are the old '
                                'names.\n').encode()
        after, _ = STEP_3_TO_4['transform'](before, CONTEXT_84)
        result = STEP_3_TO_4['verify'](before, after)
        self.assertEqual(result['errors'], [])
        for stale in ('board.md', 'log.md', 'usage.md', 'points/'):
            self.assertTrue(any(stale in item and 'AGENTS.md' in item for item in result['residue']),
                             (stale, result['residue']))
        self.assertTrue(any('P-01' in item and 'AGENTS.md' in item for item in result['residue']),
                         result['residue'])

    def test_agents_md_new_artifact_names_are_not_falsely_flagged(self):
        # 'board.md' is a literal substring of 'task-board.md', 'usage.md' of 'resource-usage.md', and
        # 'log.md' of an unrelated 'backlog.md' -- none of these already-correct or unrelated mentions
        # should be reported as a stale name.
        before = dict(load_files(FIXTURES / '3-to-4/before'))
        before['AGENTS.md'] = (before['AGENTS.md'].decode() +
                                '\n## File map\n\ntask-board.md, resource-usage.md and backlog.md are '
                                'current or unrelated names.\n').encode()
        after, _ = STEP_3_TO_4['transform'](before, CONTEXT_84)
        result = STEP_3_TO_4['verify'](before, after)
        self.assertEqual(result['errors'], [])
        self.assertEqual([item for item in result['residue'] if 'AGENTS.md' in item], [])

    def test_agents_md_stale_names_for_all_renamed_artifacts_are_flagged_as_residue(self):
        # A recheck finding: the original fix's STALE_ARTIFACT_NAMES covered
        # only 4 of the 8 tokens RENAME_FILES/RENAME_DIRS actually rename (missing coordinator.md,
        # HANDOFF.md, evidence/ and log-archive.md -- the recheck's own probe). Derived directly from
        # SCHEMA's own tables here, so a future 9th rename is covered automatically without editing
        # this test.
        stale_names = [old for old, _ in SCHEMA['RENAME_FILES'] + SCHEMA['RENAME_DIRS']]
        self.assertEqual(len(stale_names), 8)  # sanity: the recheck's probe covered 4 of these
        before = dict(load_files(FIXTURES / '3-to-4/before'))
        before['AGENTS.md'] = (before['AGENTS.md'].decode() +
                                '\n## File map\n\n' + ', '.join(stale_names) +
                                ' are the old names.\n').encode()
        after, _ = STEP_3_TO_4['transform'](before, CONTEXT_84)
        result = STEP_3_TO_4['verify'](before, after)
        self.assertEqual(result['errors'], [])
        for stale in stale_names:
            self.assertTrue(any(stale in item and 'AGENTS.md' in item for item in result['residue']),
                             (stale, result['residue']))

    def test_agents_md_new_names_for_every_renamed_artifact_are_not_falsely_flagged(self):
        # Green on arrival (the old 4-token scan never checked these either): a companion to the test
        # above, built from the new-name side of the same tables, confirming the widened scan's
        # boundary guard still holds across all 8 pairs, not only the 2 the original fix tested.
        new_names = [new for _, new in SCHEMA['RENAME_FILES'] + SCHEMA['RENAME_DIRS']]
        before = dict(load_files(FIXTURES / '3-to-4/before'))
        before['AGENTS.md'] = (before['AGENTS.md'].decode() +
                                '\n## File map\n\n' + ', '.join(new_names) +
                                ' are current names.\n').encode()
        after, _ = STEP_3_TO_4['transform'](before, CONTEXT_84)
        result = STEP_3_TO_4['verify'](before, after)
        self.assertEqual(result['errors'], [])
        self.assertEqual([item for item in result['residue'] if 'AGENTS.md' in item], [])


class RewriteContentTests(unittest.TestCase):
    """PAIRS artifact-name substitution and id mapping are each one single, boundary-guarded
    regex pass -- never a chain of independent `str.replace` calls that can re-match a pair's own new
    name where it already appears as a substring of pre-migration prose."""

    def test_pair_rewrite_does_not_double_substitute_an_existing_new_name(self):
        text = STEP_3_TO_4['rewrite_content'](
            'Append rows to resource-usage.md; today the legacy ledger is usage.md.', {})
        self.assertEqual(text, 'Append rows to resource-usage.md; today the legacy ledger is resource-usage.md.')
        self.assertNotIn('resource-resource-usage.md', text)

    def test_pair_rewrite_does_not_touch_board_md_embedded_in_task_board_md(self):
        text = STEP_3_TO_4['rewrite_content']('See task-board.md for the current board.md replacement.', {})
        self.assertEqual(text, 'See task-board.md for the current task-board.md replacement.')
        self.assertNotIn('task-task-board.md', text)

    def test_pair_rewrite_does_not_touch_log_md_embedded_in_an_unrelated_word(self):
        text = STEP_3_TO_4['rewrite_content']('See backlog.md and changelog.md; also log.md itself.', {})
        self.assertEqual(text, 'See backlog.md and changelog.md; also history.md itself.')

    def test_pair_rewrite_still_renames_a_full_directory_mention(self):
        text = STEP_3_TO_4['rewrite_content']('See evidence/P-01/raw.txt and points/P-01.md.', {'P-01': 'T-01'})
        self.assertEqual(text, 'See verification-records/T-01/raw.txt and tasks/T-01.md.')

    def test_a_short_id_does_not_swallow_a_longer_id_sharing_its_prefix(self):
        # Green on arrival: map_ids already does one single-pass, longest-id-first regex substitution
        # (the coordinator's own wording); this locks that property in as a permanent regression test.
        id_map = {'P-1': 'T-1', 'P-10': 'T-10'}
        text = SCHEMA['map_ids']('See P-10 and P-1 in the same sentence, plus P-100.', id_map)
        self.assertEqual(text, 'See T-10 and T-1 in the same sentence, plus P-100.')


class Step4To5Tests(unittest.TestCase):
    """C4: a /4 board with Ready rows with and without citations."""

    def setUp(self):
        self.before = load_files(FIXTURES / '4-to-5/before')
        self.after, self.changed = STEP_4_TO_5['transform'](self.before, CONTEXT_90)

    def test_detect_true_before_false_after(self):
        self.assertTrue(STEP_4_TO_5['detect'](self.before))
        self.assertFalse(STEP_4_TO_5['detect'](self.after))

    def test_bucket_after_is_5(self):
        self.assertEqual(SCHEMA['schema_of'](self.after), '5')

    def test_only_the_uncited_ready_row_changes(self):
        expected = (
            '# Task board — 4 to 5 fixture\n\nSchema: tackle-workspace/5\n\n'
            '| Task | What | Brief | Depends on | Status | Verification |\n'
            '|---|---|---|---|---|---|\n'
            '| T-01 | Cited ready work | tasks/T-01.md | none | Ready to run | ready: D-42 |\n'
            '| T-02 | Uncited ready work | tasks/T-02.md | none | Ready to run | ready: legacy /4 readiness |\n'
            '| T-03 | In flight | tasks/T-03.md | T-01 | In progress |  |\n'
        )
        self.assertEqual(self.after['task-board.md'].decode(), expected)

    def test_changed_rows_recorded(self):
        self.assertEqual(self.changed, {'defaulted_ready_rows': ['T-02']})

    def test_verify_is_clean(self):
        result = STEP_4_TO_5['verify'](self.before, self.after)
        self.assertEqual(result, {'errors': [], 'residue': []})

    def test_non_placeholder_verification_text_is_not_overwritten_but_flagged(self):
        board = (
            '# Task board\n\nSchema: tackle-workspace/4\n\n'
            '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
            '| T-09 | Odd note | tasks/T-09.md | none | Ready to run | ask the owner first |\n'
        )
        before = {'task-board.md': board.encode()}
        after, changed = STEP_4_TO_5['transform'](before, CONTEXT_90)
        self.assertEqual(changed, {'defaulted_ready_rows': []})
        self.assertIn('ask the owner first', after['task-board.md'].decode())
        result = STEP_4_TO_5['verify'](before, after)
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['residue']), 1)
        self.assertIn('T-09', result['residue'][0])


class IdempotenceTests(unittest.TestCase):
    """C5: every step, run on its own output, is a byte-identical no-op and verify reports no error."""

    def test_pre3_to_3(self):
        before = load_files(FIXTURES / 'pre3-to-3/before')
        after, _ = STEP_PRE3_TO_3['transform'](before, CONTEXT_84)
        second, renames = STEP_PRE3_TO_3['transform'](after, SCHEMA['PoisonContext']())
        self.assertEqual(second, after)
        self.assertEqual(renames, {})
        self.assertEqual(STEP_PRE3_TO_3['verify'](after, second)['errors'], [])

    def test_3_to_4(self):
        before = load_files(FIXTURES / '3-to-4/before')
        after, _ = STEP_3_TO_4['transform'](before, CONTEXT_84)
        second, renames = STEP_3_TO_4['transform'](after, SCHEMA['PoisonContext']())
        self.assertEqual(second, after)
        self.assertEqual(renames, {})
        self.assertEqual(STEP_3_TO_4['verify'](after, second)['errors'], [])

    def test_4_to_5(self):
        before = load_files(FIXTURES / '4-to-5/before')
        after, _ = STEP_4_TO_5['transform'](before, CONTEXT_90)
        second, changed = STEP_4_TO_5['transform'](after, SCHEMA['PoisonContext']())
        self.assertEqual(second, after)
        self.assertEqual(changed, {})
        self.assertEqual(STEP_4_TO_5['verify'](after, second)['errors'], [])

    def test_transform_never_reads_context_on_a_no_op_rerun(self):
        # PoisonContext raises on any access; a genuine no-op re-run above already proves this for
        # every step (the calls would have raised AssertionError otherwise). This test names the
        # mechanism directly so a future change that adds a context read on the no-op path is caught
        # even if it happens not to change the output bytes.
        poison = SCHEMA['PoisonContext']()
        with self.assertRaises(AssertionError):
            poison['date']
        with self.assertRaises(AssertionError):
            poison.get('date')


class ChainTests(unittest.TestCase):
    """C6: the pre-3 fixture through every step to /5, each step's verify clean, detection ending
    at 5."""

    def test_chain_reaches_5_with_clean_verify_at_every_step(self):
        pre3 = load_files(FIXTURES / 'pre3-to-3/before')
        three, _ = STEP_PRE3_TO_3['transform'](pre3, CONTEXT_84)
        self.assertEqual(STEP_PRE3_TO_3['verify'](pre3, three)['errors'], [])
        four, _ = STEP_3_TO_4['transform'](three, CONTEXT_84)
        self.assertEqual(STEP_3_TO_4['verify'](three, four)['errors'], [])
        five, _ = STEP_4_TO_5['transform'](four, CONTEXT_90)
        self.assertEqual(STEP_4_TO_5['verify'](four, five)['errors'], [])
        self.assertEqual(SCHEMA['schema_of'](five), '5')
        self.assertFalse(STEP_PRE3_TO_3['detect'](five))
        self.assertFalse(STEP_3_TO_4['detect'](five))
        self.assertFalse(STEP_4_TO_5['detect'](five))


class OriginalsPreservedTests(unittest.TestCase):
    """C7: every step, and the chain -- the input mapping is unchanged; the step's legacy-<bucket>/
    is byte-identical to it; every legacy-*/ present before a step is still present and byte-identical
    after it."""

    def assert_legacy_preserved(self, before, after):
        expected = {path: data for path, data in before.items() if path.startswith('legacy-')}
        self.assertTrue(expected, 'the fixture must contain a pre-existing legacy snapshot')
        self.assertEqual({path: after.get(path) for path in expected}, expected)

    def test_input_mapping_is_unchanged_by_transform(self):
        for step, fixture in ((STEP_PRE3_TO_3, 'pre3-to-3/before'), (STEP_3_TO_4, '3-to-4/before'),
                               (STEP_4_TO_5, '4-to-5/before')):
            before = load_files(FIXTURES / fixture)
            snapshot = dict(before)
            context = CONTEXT_90 if step is STEP_4_TO_5 else CONTEXT_84
            step['transform'](before, context)
            self.assertEqual(before, snapshot)

    def test_adopt_preserves_every_pre_existing_legacy_directory_and_adds_its_own(self):
        before = load_files(FIXTURES / 'pre3-to-3/before')
        before_with_legacy = dict(before)
        before_with_legacy['legacy-8.3/board.md'] = b'ancient snapshot, must survive untouched\n'
        adopted, _ = SCHEMA['adopt'](before_with_legacy, CONTEXT_84, STEP_PRE3_TO_3['transform'])
        self.assert_legacy_preserved(before_with_legacy, adopted)
        for path, data in before.items():
            self.assertEqual(adopted['legacy-pre-3/' + path], data)
        self.assertEqual(SCHEMA['schema_of'](adopted), '3')

    def test_chain_adoption_accumulates_every_earlier_legacy_snapshot(self):
        pre3 = load_files(FIXTURES / 'pre3-to-3/before')
        adopted3, _ = SCHEMA['adopt'](pre3, CONTEXT_84, STEP_PRE3_TO_3['transform'])
        self.assertIn('legacy-pre-3/board.md', adopted3)
        adopted4, _ = SCHEMA['adopt'](adopted3, CONTEXT_84, STEP_3_TO_4['transform'])
        self.assertIn('legacy-pre-3/board.md', adopted4)  # earlier step's snapshot survives
        self.assertIn('legacy-3/board.md', adopted4)      # this step's own snapshot
        self.assertEqual(adopted4['legacy-pre-3/board.md'], adopted3['legacy-pre-3/board.md'])
        adopted5, _ = SCHEMA['adopt'](adopted4, CONTEXT_90, STEP_4_TO_5['transform'])
        self.assertIn('legacy-pre-3/board.md', adopted5)
        self.assertIn('legacy-3/board.md', adopted5)
        self.assertIn('legacy-4/task-board.md', adopted5)

    def test_mutation_dropping_legacy_preservation_during_adoption_is_caught(self):
        """The same oracle used on real adopt() rejects missing and changed legacy bytes."""
        before = load_files(FIXTURES / 'pre3-to-3/before')
        before_with_legacy = dict(before)
        before_with_legacy['legacy-8.3/board.md'] = b'must survive\n'

        def broken_adopt(files, context, transform):
            scoped = SCHEMA['workspace_files'](files)
            new_files, renames = transform(scoped, context)
            return dict(new_files), renames  # forgets every legacy-*/ directory

        broken_result, _ = broken_adopt(before_with_legacy, CONTEXT_84, STEP_PRE3_TO_3['transform'])
        real_result, _ = SCHEMA['adopt'](before_with_legacy, CONTEXT_84, STEP_PRE3_TO_3['transform'])
        self.assert_legacy_preserved(before_with_legacy, real_result)
        corrupt_result = dict(real_result, **{'legacy-8.3/board.md': b'changed snapshot\n'})
        for label, mutant in (('missing', broken_result), ('changed', corrupt_result)):
            with self.subTest(mutant=label):
                with self.assertRaises(AssertionError):
                    self.assert_legacy_preserved(before_with_legacy, mutant)


class CheckpointTests(unittest.TestCase):
    """An in-memory checkpoint remains unchanged by transform; no disk rollback is exercised."""

    def test_transform_preserves_checkpoint_bytes_and_original_schema(self):
        before = load_files(FIXTURES / '3-to-4/before')
        checkpoint = dict(before)  # the checkpoint IS the pre-transform files mapping
        candidate, _ = STEP_3_TO_4['transform'](before, CONTEXT_84)
        self.assertNotEqual(candidate, checkpoint)
        restored = dict(checkpoint)  # "restore the checkpoint": discard the candidate entirely
        self.assertEqual(restored, before)
        self.assertEqual(SCHEMA['schema_of'](restored), '3')


class RefusalTests(unittest.TestCase):
    """C9: an unknown workspace (including both board files, or a Lite plan beside a board), a
    duplicate id, an unsupported row -- verify or transform fails with a named error; nothing is
    written."""

    def test_unknown_both_board_files_refused_by_every_step(self):
        files = load_files(FIXTURES / 'refusals/unknown-both')
        self.assertEqual(SCHEMA['schema_of'](files), 'unknown')
        for step in STEPS:
            with self.assertRaises(ValueError):
                step['transform'](files, CONTEXT_84)

    def test_lite_plan_beside_a_board_refused(self):
        files = load_files(FIXTURES / 'refusals/unknown-lite-board')
        self.assertEqual(SCHEMA['schema_of'](files), 'unknown')
        with self.assertRaises(ValueError):
            STEP_PRE3_TO_3['transform'](files, CONTEXT_84)

    def test_duplicate_id_refused_pre3_to_3(self):
        files = load_files(FIXTURES / 'refusals/duplicate-id')
        with self.assertRaisesRegex(ValueError, 'duplicate identity'):
            STEP_PRE3_TO_3['transform'](files, CONTEXT_84)

    def test_unsupported_legacy_state_refused_pre3_to_3(self):
        files = load_files(FIXTURES / 'refusals/unsupported-row')
        with self.assertRaisesRegex(ValueError, 'unsupported legacy state'):
            STEP_PRE3_TO_3['transform'](files, CONTEXT_84)

    def test_duplicate_id_refused_3_to_4(self):
        board = ('# Task board\n\nSchema: tackle-workspace/3\n\n'
                 '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
                 '| P-01 | First | tasks/P-01.md | none | Draft |  |\n'
                 '| P-01 | Second | tasks/P-01b.md | none | Draft |  |\n')
        with self.assertRaisesRegex(ValueError, 'duplicate identity'):
            STEP_3_TO_4['transform']({'board.md': board.encode()}, CONTEXT_84)

    def test_id_collision_after_mapping_refused_3_to_4(self):
        board = ('# Task board\n\nSchema: tackle-workspace/3\n\n'
                 '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
                 '| P-01 | First | tasks/P-01.md | none | Draft |  |\n'
                 '| T-01 | Collides | tasks/T-01.md | none | Draft |  |\n')
        with self.assertRaisesRegex(ValueError, 'duplicate identity after mapping'):
            STEP_3_TO_4['transform']({'board.md': board.encode()}, CONTEXT_84)

    def test_unsupported_status_refused_3_to_4(self):
        board = ('# Task board\n\nSchema: tackle-workspace/3\n\n'
                 '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
                 '| P-01 | Mystery | tasks/P-01.md | none | Mystery |  |\n')
        with self.assertRaisesRegex(ValueError, 'unsupported task row status'):
            STEP_3_TO_4['transform']({'board.md': board.encode()}, CONTEXT_84)

    def test_unknown_workspace_refused_directly_by_each_step(self):
        files = load_files(FIXTURES / 'detect/unknown-empty')
        for step, fragment in ((STEP_PRE3_TO_3, 'pre-3'), (STEP_3_TO_4, '/3'), (STEP_4_TO_5, '/4')):
            with self.assertRaisesRegex(ValueError, 'not a'):
                step['transform'](files, CONTEXT_84)

    def test_nothing_written_on_refusal(self):
        files = load_files(FIXTURES / 'refusals/duplicate-id')
        snapshot = dict(files)
        with self.assertRaises(ValueError):
            STEP_PRE3_TO_3['transform'](files, CONTEXT_84)
        self.assertEqual(files, snapshot)


class MutationTests(unittest.TestCase):
    """Method step 6: break idempotence, drop a legacy-*/ directory during adoption, infer Ready from
    a legacy not-started state, and leave a P-id in plan.md section 5 -- each mutant is shown to fail
    a real check, not merely a hand run."""

    def test_broken_idempotence_is_caught_by_verify(self):
        before = load_files(FIXTURES / '3-to-4/before')
        after, _ = STEP_3_TO_4['transform'](before, CONTEXT_84)

        original_transform = STEP_3_TO_4['transform']

        def non_idempotent_transform(files, context):
            new_files, id_map = original_transform(files, context)
            new_files = dict(new_files)
            if 'task-board.md' in new_files:
                new_files['task-board.md'] += b'\n<!-- appended on every call -->\n'
            return new_files, id_map

        # verify()'s body resolves `transform` from its own module namespace at call time (it is
        # `exec`'d code, so that namespace is its __globals__): reload the same source into a fresh
        # namespace with the mutant transform substituted, so verify() calls the mutant, not the real
        # recipe, for its internal idempotence re-run.
        source = (RECIPES / 'step-3-to-4.md').read_text().split('```python\n', 1)[1].split('\n```', 1)[0]
        mutant_ns = dict(SCHEMA)
        exec(compile(source, 'step-3-to-4-mutant', 'exec'), mutant_ns)
        mutant_ns['transform'] = non_idempotent_transform
        result = mutant_ns['verify'](before, after)
        self.assertIn('second transform is not a byte-identical no-op', result['errors'])

    def test_inferring_ready_from_not_started_is_caught_by_verify(self):
        before = load_files(FIXTURES / 'pre3-to-3/before')
        after, _ = STEP_PRE3_TO_3['transform'](before, CONTEXT_84)
        mutated = dict(after)
        mutated['board.md'] = after['board.md'].replace(b'| Draft |', b'| Ready to run |')
        result = STEP_PRE3_TO_3['verify'](before, mutated)
        self.assertTrue(any('inferred Ready to run' in error for error in result['errors']), result)

    def test_leaving_a_p_id_in_plan_section_5_is_caught_as_residue(self):
        before = load_files(FIXTURES / '3-to-4/before')
        after, id_map = STEP_3_TO_4['transform'](before, CONTEXT_84)
        mutated = dict(after)
        mutated['plan.md'] = after['plan.md'].replace(b'T-02', b'P-02')
        result = STEP_3_TO_4['verify'](before, mutated)
        self.assertTrue(any('P-02' in item for item in result['residue']), result)


class CensusHygieneTests(unittest.TestCase):
    """census.py must never open a held-out verification record, even though the workspace
    holding such records may be in the gating set. Tests census.py's
    logic directly; the script itself is never run here (it reads real local docs/plans/ workspaces,
    which do not exist in a fresh checkout)."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        path = (Path(__file__).resolve().parents[4] / 'eval/migration') / 'census.py'
        spec = importlib.util.spec_from_file_location('tackle_census_hygiene', path)
        cls.census = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.census)

    def test_named_held_out_records_are_skipped(self):
        held_out_re = re.compile(r'(^|/)verification-records/(X-a|X-b)(/|$)')
        self.assertTrue(self.census.held_out('verification-records/X-a/authoring/notes.json', held_out_re))
        self.assertTrue(self.census.held_out('verification-records/X-b/readiness/review.json', held_out_re))

    def test_other_task_records_are_not_held_out(self):
        held_out_re = re.compile(r'(^|/)verification-records/(X-a|X-b)(/|$)')
        for path in ('verification-records/X-c/report.json', 'verification-records/X-d/census.json',
                     'task-board.md', 'verification-records/X-a-notes.md'):
            self.assertFalse(self.census.held_out(path, held_out_re), path)

    def test_waiting_on_owner_counts_as_active(self):
        # lint-spec.md row 8 (already shipped) ORs in status=="Waiting on owner"; is_active()'s
        # own docstring claims to mirror row 8, so a lone Waiting-on-owner row (no other active-shaped
        # row) must also count.
        board = ('# Task board\n\nSchema: tackle-workspace/5\n\n'
                 '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
                 '| T-01 | Needs a call | tasks/T-01.md | none | Waiting on owner | waiting: Q-99 |\n')
        self.assertTrue(self.census.is_active({'task-board.md': board.encode()}))

    def test_waiting_on_owner_alone_still_inactive_before_the_fix_is_a_regression_guard(self):
        # A same-shaped board with no Waiting-on-owner row and nothing else active stays inactive --
        # guards against a fix that makes is_active() return True unconditionally.
        board = ('# Task board\n\nSchema: tackle-workspace/5\n\n'
                 '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
                 '| T-01 | Done | tasks/T-01.md | none | Complete | reports/T-01-report.md |\n')
        self.assertFalse(self.census.is_active({'task-board.md': board.encode()}))

    def test_chain_workspace_preserves_a_pre_existing_legacy_directory_through_a_rename_step(self):
        # This initiative's own real workspace carries a real legacy-8.3/ directory and is
        # always in census.py's gating set. chain_workspace must advance through schema.adopt(), never
        # transform() directly: calling step-3-to-4's transform() on the full files mapping (legacy
        # directory included) walks its rename/id-map logic into legacy-8.3/ and corrupts it -- proven
        # directly: STEP_3_TO_4['transform'] alone renames 'legacy-8.3/points/P-01.md' to
        # 'legacy-8.3/points/T-01.md' when given the unscoped mapping (the coordinator's finding,
        # reproduced here as the reason chain_workspace must not do that).
        unscoped_files = dict(load_files(FIXTURES / 'pre3-to-3/before'))
        unscoped_files['legacy-8.3/points/P-01-old.md'] = b'ancient brief, must survive untouched\n'
        after_pre3, _ = STEP_PRE3_TO_3['transform'](unscoped_files, CONTEXT_84)
        after_3to4_unscoped, _ = STEP_3_TO_4['transform'](after_pre3, CONTEXT_84)
        self.assertNotEqual(after_3to4_unscoped.get('legacy-8.3/points/P-01-old.md'),
                             unscoped_files['legacy-8.3/points/P-01-old.md'],
                             'calling transform() directly on an unscoped mapping is expected to '
                             'corrupt the legacy directory -- this is the bug chain_workspace avoids')

        files = dict(load_files(FIXTURES / 'pre3-to-3/before'))
        files['legacy-8.3/points/P-01-old.md'] = b'ancient brief, must survive untouched\n'
        final_bucket, errors, residue, refusal, originals_ok = self.census.chain_workspace(files, 'test-run')
        self.assertEqual(final_bucket, '5')
        self.assertEqual(errors, [])
        self.assertIsNone(refusal)
        self.assertTrue(originals_ok)

    def test_load_files_excludes_held_out_paths(self):
        import tempfile
        held_out_re = re.compile(r'(^|/)verification-records/(X-a|X-b)(/|$)')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'verification-records/X-a').mkdir(parents=True)
            (root / 'verification-records/X-a/secret.json').write_text('held out')
            (root / 'verification-records/X-c').mkdir(parents=True)
            (root / 'verification-records/X-c/report.json').write_text('fine')
            (root / 'board.md').write_text('# Board\n')
            files = self.census.load_files(root, held_out_re)
            self.assertNotIn('verification-records/X-a/secret.json', files)
            self.assertIn('verification-records/X-c/report.json', files)
            self.assertIn('board.md', files)


class MigrateGuideTests(unittest.TestCase):
    """The five sections are appended after the existing content; each recipe link resolves;
    the 8.x checklists are byte-identical to d024a3f; every migrate.md:N citation elsewhere in the
    repository and in this workspace still resolves (lint row 4); install-inventory and the eight
    gates stay green."""

    def setUp(self):
        self.text = (INSTALL / 'references/guides/migrate.md').read_text(encoding='utf-8')
        self.lines = self.text.split('\n')

    def test_five_new_sections_appended_after_existing_content(self):
        for anchor in ('schema-keyed-migration', 'migration-steps', 'read-compatibility-promise',
                       'pre-migration-originals', 'migration-rollback'):
            self.assertIn('<a id="%s"></a>' % anchor, self.text)
        # every new anchor appears after the line that used to be the file's last line
        last_original_line = 'A failed check leaves it active and unchanged.'
        self.assertIn(last_original_line, self.text)
        boundary = self.text.index(last_original_line)
        for anchor in ('schema-keyed-migration', 'migration-steps', 'read-compatibility-promise',
                       'pre-migration-originals', 'migration-rollback'):
            self.assertGreater(self.text.index('<a id="%s"></a>' % anchor), boundary)

    def test_first_90_lines_are_byte_identical_to_d024a3f(self):
        # The pinned fixture is this task's own preflight capture of migrate.md's first 90 lines at
        # d024a3f (the two 8.x checklists plus their preamble), taken before any edit in this task.
        pinned = (FIXTURES / 'migrate-md-prefix-d024a3f.txt').read_text(encoding='utf-8')
        self.assertEqual('\n'.join(self.lines[:90]) + '\n', pinned)

    def test_recipe_links_resolve(self):
        for match in re.findall(r'\]\(([^)]+)\)', self.text):
            if match.startswith('../'):
                target = (INSTALL / 'references/guides' / match).resolve()
                self.assertTrue(target.is_file(), match)

    def test_two_checklists_still_present_and_not_touched(self):
        self.assertIn('## v8.4.0 → v8.4.1 checklist', self.text)
        self.assertIn('## v8.3 → v8.4 checklist', self.text)
        self.assertIn('<a id="candidate-workspace-format"></a>', self.text)

    def test_the_pinned_citation_still_resolves(self):
        # references/guides/migrate.md:6 -- "Select the 8.3 → 8.4 checklist" (pinned by a prior release task's own citation)
        self.assertIn('Select the 8.3 → 8.4 checklist', self.lines[5])

    def test_no_longer_claims_a_changed_contract_surfaces_as_residue(self):
        # Only the Interrupted-task check exists in step-3-to-4's verify(); the guide must not
        # overclaim residue for a changed design-contract.md too (whitespace-normalized, since the
        # prose wraps across lines).
        normalized = ' '.join(self.text.split())
        self.assertNotIn('changed contract', normalized)

    def test_rename_target_collision_is_a_transform_refusal_not_a_verify_error(self):
        # A recheck finding: step-3-to-4.md's verify() body never mentions
        # 'collision' -- the check is a ValueError raised inside transform() itself, before anything
        # is written, so a colliding workspace's adoption never reaches verify() at all. The guide
        # must not group the collision with the four properties verify()'s own `errors` list reports.
        normalized = ' '.join(self.text.split())
        self.assertNotIn(
            'an old artifact name left in the root, or a rename-target collision', normalized)
        self.assertIn(
            '`errors` gate adoption: the wrong bucket after the step, a second `transform` that is '
            'not byte-identical, a board invariant, or an old artifact name left in the root',
            normalized)
        self.assertIn(
            'A rename-target collision is a separate, transform-time refusal, not a `verify` error',
            normalized)
        self.assertIn('adoption never reaches `verify`', normalized)

    def test_historical_content_strings_stay_out_of_the_install(self):
        for stale in ('## v8.2 → v8.3 checklist', '## v7.3 → v8.0 checklist',
                      '## v2.0 → v2.1.0 checklist', 'F-1 · Agent contract'):
            self.assertNotIn(stale, self.text)


if __name__ == '__main__':
    unittest.main()
