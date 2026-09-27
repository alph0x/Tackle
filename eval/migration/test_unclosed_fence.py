"""An unclosed fenced example inside a workspace board is refused, not silently mishandled.

Historically the plain-Python board reader raised a plain `ValueError('unclosed fenced example')`
when a fence opened by a board's illustrative code block was still open at the end of the text. This
suite locks the same refusal into the schema-keyed recipes: the strict board-shaped reads (locating a
workspace's own table, right before that table's rows are trusted) refuse instead of quietly returning
a table that stops wherever the broken fence happens to swallow the rest of the file. The lenient
reads used only to notice a `Schema:` stamp, or to recognize an already-written history heading, are
untouched -- an unrelated file may quote sample text whose fence is never meant to close.

Loaded exactly the way the sibling migration-steps suite loads the recipe files: read, take the one
fenced Python block, `exec` it into a namespace, `schema.md`'s names shared into every step so each
step calls the very same `schema_of`/`parse_board`/... this suite exercises directly.
"""
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECIPES = ROOT / 'references/recipes/migrate'

OPEN_FENCE = '```\nan example that opens a fence and never closes it\n'


def load_block(path, namespace=None):
    text = path.read_text(encoding='utf-8')
    block = text.split('```python\n', 1)[1].split('\n```', 1)[0]
    ns = dict(namespace or {})
    ns['__name__'] = 'fence_fixture_' + path.stem.replace('-', '_')
    exec(compile(block, str(path), 'exec'), ns)
    return ns


SCHEMA = load_block(RECIPES / 'schema.md')
STEP_PRE3_TO_3 = load_block(RECIPES / 'step-pre3-to-3.md', SCHEMA)
STEP_3_TO_4 = load_block(RECIPES / 'step-3-to-4.md', SCHEMA)
STEP_4_TO_5 = load_block(RECIPES / 'step-4-to-5.md', SCHEMA)

CONTEXT_84 = {'date': '2026-09-25', 'run_id': 'fence-fixture-1', 'methodology': 'Tackle 8.4.0'}
CONTEXT_90 = {'date': '2026-09-25', 'run_id': 'fence-fixture-1', 'methodology': 'Tackle 9.0.0'}


def pre3_board_with_open_fence():
    # A real header, delimiter and first row, all readable on their own; the fence then opens and
    # never closes, with a second row sitting after it -- a row that a version reading only up to
    # the broken fence would never see at all.
    return (
        '# Board\n\n'
        '| Point | What | Brief | Depends on | Status | Confidence |\n'
        '|---|---|---|---|---|---|\n'
        '| P-a | Real work | brief.md | none | \U0001F534 | E0 |\n' + OPEN_FENCE +
        '| P-b | More work | brief2.md | none | \U0001F534 | E0 |\n'
    ).encode('utf-8')


def three_board_with_open_fence():
    return (
        '# Task board\n\nSchema: tackle-workspace/3\n\n'
        '| Task | What | Brief | Depends on | Status | Verification |\n'
        '|---|---|---|---|---|---|\n'
        '| T-a | Real work | tasks/T-a.md | none | Draft |  |\n' + OPEN_FENCE +
        '| T-b | More work | tasks/T-b.md | none | Draft |  |\n'
    ).encode('utf-8')


def four_board_with_open_fence():
    return (
        '# Task board\n\nSchema: tackle-workspace/4\n\n'
        '| Task | What | Brief | Depends on | Status | Verification |\n'
        '|---|---|---|---|---|---|\n'
        '| T-a | Real work | tasks/T-a.md | none | Draft |  |\n' + OPEN_FENCE +
        '| T-b | More work | tasks/T-b.md | none | Ready to run |  |\n'
    ).encode('utf-8')


def four_board_clean():
    return (
        '# Task board\n\nSchema: tackle-workspace/4\n\n'
        '| Task | What | Brief | Depends on | Status | Verification |\n'
        '|---|---|---|---|---|---|\n'
        '| T-a | Real work | tasks/T-a.md | none | Draft |  |\n'
    ).encode('utf-8')


class StepRefusalTests(unittest.TestCase):
    """Every board-reading step's transform refuses a board whose fenced example never closes, and
    no row past the break is ever silently folded into a successful result."""

    def test_pre3_detect_and_transform_both_raise_on_its_own_board(self):
        files = {'board.md': pre3_board_with_open_fence()}
        with self.assertRaisesRegex(ValueError, '^unclosed fenced example$'):
            STEP_PRE3_TO_3['detect'](files)
        with self.assertRaisesRegex(ValueError, '^unclosed fenced example$'):
            STEP_PRE3_TO_3['transform'](files, CONTEXT_84)

    def test_3_to_4_transform_raises_but_its_own_detect_stays_lenient(self):
        files = {'board.md': three_board_with_open_fence()}
        self.assertTrue(STEP_3_TO_4['detect'](files))  # the Schema: line keeps detection lenient
        with self.assertRaisesRegex(ValueError, '^unclosed fenced example$'):
            STEP_3_TO_4['transform'](files, CONTEXT_84)

    def test_4_to_5_transform_raises_but_its_own_detect_stays_lenient(self):
        files = {'task-board.md': four_board_with_open_fence()}
        self.assertTrue(STEP_4_TO_5['detect'](files))
        with self.assertRaisesRegex(ValueError, '^unclosed fenced example$'):
            STEP_4_TO_5['transform'](files, CONTEXT_90)

    def test_4_to_5_detect_raises_only_when_the_root_also_holds_a_broken_legacy_board(self):
        # A /4 workspace whose own task-board.md is entirely clean still has its own detect() raise
        # once a stray, Schema-less legacy board.md also sits in the root with a fence that never
        # closes: bucket resolution reaches that stray file's own strict pre-3 check regardless of
        # what task-board.md says.
        files = {'task-board.md': four_board_clean(), 'board.md': pre3_board_with_open_fence()}
        with self.assertRaisesRegex(ValueError, '^unclosed fenced example$'):
            STEP_4_TO_5['detect'](files)


class DetectionRefusalTests(unittest.TestCase):
    """The lower-level header check refuses on its own once its only table follows a fence that
    never closes."""

    def test_board_header_has_raises_when_its_only_table_follows_an_unclosed_fence(self):
        text = OPEN_FENCE + '| Point | Status |\n|---|---|\n| P-a | \U0001F534 |\n'
        with self.assertRaisesRegex(ValueError, '^unclosed fenced example$'):
            SCHEMA['board_header_has'](text, {'Point', 'Task'})


class ClosedFenceStillWorksTests(unittest.TestCase):
    """A board whose fenced example opens and closes normally still reads exactly as before."""

    def test_closed_fence_then_real_table_parses_normally(self):
        text = (
            '# Board\n\n'
            '```\nan example that opens and closes its fence\n```\n\n'
            '| Point | What | Brief | Depends on | Status | Confidence |\n'
            '|---|---|---|---|---|---|\n'
            '| P-a | Real work | brief.md | none | \U0001F534 | E0 |\n'
        )
        self.assertTrue(SCHEMA['board_header_has'](text, {'Point', 'Task'}))
        _, _, _, rows = SCHEMA['parse_board'](text)
        self.assertEqual(len(rows), 1)


class HistoryStaysLenientTests(unittest.TestCase):
    """A history entry that merely quotes an unclosed code sample is not a board, and the adoption
    heading check that reads history files keeps its lenient scan."""

    def test_history_with_an_unclosed_fenced_quote_is_not_refused(self):
        history_text = (
            '## 2026-09-25 · a session note\n\n'
            '- Quoted an example that never closes its own fence:\n' + OPEN_FENCE
        )
        self.assertFalse(STEP_3_TO_4['_has_real_adoption_entry'](history_text))


class CensusRefusalTests(unittest.TestCase):
    """The local census tool reports the refusal instead of crashing, and treats a refused board as
    gating rather than silently excluding it."""

    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parent / 'census.py'
        spec = importlib.util.spec_from_file_location('fence_fixture_census', path)
        cls.census = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.census)

    def census_board_text(self):
        return (
            '# Board\n\n'
            '| Point | What | Brief | Depends on | Status | Confidence |\n'
            '|---|---|---|---|---|---|\n'
            '| P-a | Draft work | brief.md | none | \U0001F534 | E0 |\n' + OPEN_FENCE
        )

    def test_chain_workspace_reports_the_refusal_without_raising(self):
        files = {'board.md': self.census_board_text().encode('utf-8')}
        final_bucket, errors, residue, refusal, originals_ok = self.census.chain_workspace(
            files, 'fence-fixture-2')
        self.assertEqual(final_bucket, 'unknown')
        self.assertEqual(refusal, 'unclosed fenced example')

    def test_is_active_true_on_the_refusal(self):
        files = {'board.md': self.census_board_text().encode('utf-8')}
        self.assertTrue(self.census.is_active(files))

    def test_census_over_a_temporary_plans_root_never_raises_and_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            plans_dir = Path(tmp) / 'plans'
            out_dir = Path(tmp) / 'out'
            record_dir = Path(tmp) / 'record'
            workspace = plans_dir / 'fence-workspace'
            workspace.mkdir(parents=True)
            (workspace / 'board.md').write_text(self.census_board_text(), encoding='utf-8')
            held_out_re = re.compile(r'(^|/)verification-records/(X-a|X-b)(/|$)')
            rows, _counts, concurrent_edits = self.census.census(plans_dir, out_dir, record_dir, set(), held_out_re)
            self.assertEqual(concurrent_edits, [])
            row = next(r for r in rows if r['workspace'] == 'fence-workspace')
            self.assertEqual(row['bucket'], 'unknown')
            self.assertEqual(row['refusal'], 'unclosed fenced example')
            self.assertTrue(row['gates'])


if __name__ == '__main__':
    unittest.main()
