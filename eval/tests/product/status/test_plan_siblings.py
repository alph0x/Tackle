"""A plan may depend on tasks in declared sibling workspaces; the view resolves, refuses and digests them and draws them as external nodes.

The shipped recipe builds a local workspace under a temporary repository root beside a sibling workspace. Each
case checks the page, its data island, its Mermaid text, its digests or its refusal lines against the grammar of
the sibling workspaces clause. Ids are four digits; the sibling slug differs from its folder on purpose.
"""
import hashlib
import html
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_plan_view import REPO, TEMPLATE, recipe_source

HEAD = ('# Task board\n\nSchema: tackle-workspace/5\n\nStates: Draft, Ready to run, In progress, Checking, Complete, '
        'Blocked, Interrupted, Skipped, Unverifiable, Waiting on owner.\n\n'
        '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n')
PLAN = ('# Plan — siblings\n\nThe plan links two workspaces.\n\n'
        '| Criterion | Required behavior |\n|---|---|\n| `R0001` | one |\n')
BRIEF = '# Task %s — demo\n\n- **Traces to**: R0001\n- **Goal**: demo.\n'
AGENTS_HEAD = '# AGENTS\n\n**Methodology: Tackle 9.1.0**\n\n'
DECLARED = ('## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n'
            '| api | docs/plans/beta | api split |\n')
BETA_BOARD = (HEAD + '| T-0007 | Ship the client | `tasks/T-0007-client.md` | none | In progress | v |\n'
              '| T-0008 | Ship the server | `tasks/T-0008-server.md` | none | Complete | v |\n'
              '| T-0009 | Ship the docs | `tasks/T-0009-docs.md` | none | Draft | v |\n')
ALPHA_ROWS = ('| T-0001 | First step | `tasks/T-0001-first.md` | none | Complete | v |\n'
              '| T-0002 | Second step | `tasks/T-0002-second.md` | %s | Draft | v |\n')
ESCAPE_TEXT = 'brief ../beta/tasks/../../gamma/x.md for task T-0003 is outside the workspace'
NO_BOARD = 'sibling api has no tackle-workspace/5 task-board.md at docs/plans/beta'


def stage_labels():
    """The English stage-count and state labels, read from the shipped recipe's own table."""
    namespace = {'__name__': 'recipe_under_test'}
    exec(compile(recipe_source(), 'plan-view.md', 'exec'), namespace)
    return namespace['UI']['en']


def write_files(root, files):
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')


def build(tmp, second_deps='T-0001, T-0007 [api]', agents=AGENTS_HEAD + DECLARED, beta=BETA_BOARD, extra_alpha=''):
    """Write the local workspace (alpha) and its sibling (beta) under one repository root; return both folders."""
    repo = Path(tmp) / 'repo'
    alpha, beta_dir = repo / 'docs/plans/alpha', repo / 'docs/plans/beta'
    alpha_board = HEAD + ALPHA_ROWS % second_deps + extra_alpha
    write_files(alpha, {'plan.md': PLAN, 'task-board.md': alpha_board, 'AGENTS.md': agents,
                        'tasks/T-0001-first.md': BRIEF % 'T-0001', 'tasks/T-0002-second.md': BRIEF % 'T-0002'})
    if beta is not None:
        write_files(beta_dir, {'task-board.md': beta, 'tasks/T-0007-client.md': BRIEF % 'T-0007',
                               'tasks/T-0008-server.md': BRIEF % 'T-0008', 'tasks/T-0009-docs.md': BRIEF % 'T-0009'})
    else:
        beta_dir.mkdir(parents=True, exist_ok=True)
    return alpha, beta_dir


def run(tmp, ws, options=(), output=None):
    """Run the shipped recipe on the workspace; the page goes to the given output or to a fresh file."""
    script = Path(tmp) / 'recipe-under-test.py'
    script.write_text(recipe_source(), encoding='utf-8')
    out = Path(output) if output else Path(tmp) / 'plan-view.html'
    result = subprocess.run([sys.executable, '-I', str(script), '--template', str(TEMPLATE), *options, str(ws), str(out)],
                            capture_output=True, text=True, timeout=60)
    return result, out


def island(page):
    """The parsed data island of a built page."""
    text = re.search(r'<script type="application/json" id="plan-view-data">(.*?)</script>', page, re.S).group(1)
    return json.loads(text)


def node_rect(page, klass, task):
    """The box of a local node, found by its data-task attribute."""
    group = re.search(r'<g class="node %s" data-task="%s"[^>]*>(.*?)</g>' % (klass, task), page, re.S).group(1)
    box = re.search(r'<rect class="node-box" x="([\d.]+)" y="([\d.]+)" width="(\d+)" height="(\d+)"/>', group)
    return tuple(float(v) for v in box.groups())


class SiblingWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.labels = stage_labels()

    def test_resolved_dependency_draws_an_external_node_and_the_island_keeps_local_deps(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertEqual(len(re.findall(r'<g class="xnode s-prog"', page)), 1)
            self.assertIn('<g class="xnode s-prog" role="img" aria-label="api · T-0007 · Ship the client · In progress">'
                          '<title>api · T-0007 · Ship the client · In progress</title>', page)
            xnode = re.search(r'<g class="xnode s-prog"[^>]*>(.*?)</g>', page, re.S).group(0)
            self.assertNotIn('tabindex', xnode)
            self.assertNotIn('data-task', xnode)
            self.assertIn('data-from="x:api:T-0007" data-to="T-0002"', page)
            tasks = {t['id']: t for t in island(page)['tasks']}
            self.assertEqual(tasks['T-0002']['deps'], ['T-0001'])

    def test_stage_placement_counts_and_needs_use_local_tasks_and_the_sibling_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            xnode = re.search(r'<g class="xnode s-prog"[^>]*>(.*?)</g>', page, re.S).group(1)
            external = tuple(float(v) for v in re.search(r'<rect class="node-box" x="([\d.]+)" y="([\d.]+)" width="(\d+)" height="(\d+)"/>',
                                                        xnode).groups())
            second = node_rect(page, 's-draft', 'T-0002')
            self.assertLess(external[0], second[0])
            self.assertEqual(external[2:], second[2:])
            self.assertIn('<text class="nid" x="', xnode)
            self.assertIn('>api · T-0007</text>', xnode)
            self.assertIn(self.labels['stage_count'].format(done=1, total=1), page)
            self.assertIn('<span class="nb">T-0001</span>, <span class="nb">api · T-0007</span>', page)
            self.assertNotIn('stage-task-id">x:', page)
            self.assertNotIn('data-task="x:', page)
            article = re.search(r'<article class="task[^"]*" id="task-T-0002".*?</article>', page, re.S).group(0)
            self.assertIn('href="#task-T-0001"', article)
            self.assertNotIn('api', article)
            self.assertNotIn('T-0007', article)

    def test_two_external_references_and_a_duplicate_give_two_nodes_in_first_reference_order(self):
        beta = HEAD + ('| T-0007 | Ship the client | `tasks/T-0007-client.md` | none | Complete | v |\n'
                       '| T-0008 | Ship the server | `tasks/T-0008-server.md` | none | In progress | v |\n')
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, second_deps='T-0008 [api], T-0007 [api], T-0008 [api]', beta=beta)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertEqual(len(re.findall(r'<g class="xnode ', page)), 2)
            self.assertLess(page.index('aria-label="api · T-0008'), page.index('aria-label="api · T-0007'))
            self.assertIn('data-from="x:api:T-0008" data-to="T-0002"', page)
            self.assertRegex(page, r'class="edge met" data-from="x:api:T-0007" data-to="T-0002"')
            self.assertRegex(page, r'class="edge open" data-from="x:api:T-0008" data-to="T-0002"')

    def test_mermaid_text_draws_external_nodes_first_and_edges_in_dependency_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            text = re.search(r'<script type="text/plain" id="plan-view-mermaid-tasks">(.*?)</script>', page, re.S).group(1)
            lines = text.split('\n')
            self.assertEqual(lines[0], 'flowchart LR')
            self.assertEqual(lines[1], '  x_api_T_0007["api · T-0007 Ship the client"]:::external')
            self.assertEqual(lines[2], '  t_T_0001["T-0001 · First step"]:::done')
            self.assertEqual(lines[3], '  t_T_0002["T-0002 · Second step"]:::draft')
            edges = [line for line in lines if ' --> ' in line]
            self.assertEqual(edges, ['  t_T_0001 --> t_T_0002', '  x_api_T_0007 --> t_T_0002'])
            class_lines = [line for line in lines if line.startswith('  classDef')]
            self.assertTrue(class_lines[0].startswith('  classDef external '))

    def test_digests_record_the_sibling_board_and_check_reports_it_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, beta_dir = build(tmp)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            found = re.search(r'<meta name="tackle-input-digest" content="([^"]*)">', page)
            record = json.loads(html.unescape(found.group(1)))
            expected = hashlib.sha256((beta_dir / 'task-board.md').read_bytes()).hexdigest()
            self.assertEqual(record['inputs']['api:task-board.md'], expected)
            current, _ = run(tmp, alpha, options=('--check',), output=out)
            self.assertEqual(current.returncode, 0, current.stdout + current.stderr)
            with open(beta_dir / 'task-board.md', 'a', encoding='utf-8') as handle:
                handle.write('\n| T-0010 | Extra | `tasks/T-0010.md` | none | Draft | v |\n')
            stale, _ = run(tmp, alpha, options=('--check',), output=out)
            self.assertEqual(stale.returncode, 1)
            self.assertIn('view stale: api:task-board.md', stale.stdout)

    def test_a_sibling_brief_resolves_and_is_keyed_by_the_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, beta_dir = build(tmp, extra_alpha='| T-0003 | Third | `../beta/tasks/T-0003-x.md` | none | Draft | v |\n')
            write_files(beta_dir, {'tasks/T-0003-x.md': '# Task T-0003 — x\n\n- **Traces to**: R0001\n'})
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            record = json.loads(html.unescape(re.search(r'<meta name="tackle-input-digest" content="([^"]*)">',
                                                        out.read_text(encoding='utf-8')).group(1)))
            self.assertIn('api:tasks/T-0003-x.md', record['inputs'])

    def test_a_brief_that_escapes_the_sibling_tasks_folder_keeps_the_outside_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, extra_alpha='| T-0003 | Third | `../beta/tasks/../../gamma/x.md` | none | Draft | v |\n')
            result, _ = run(tmp, alpha)
            self.assertEqual(result.returncode, 1)
            self.assertIn('refused: ' + ESCAPE_TEXT, result.stdout)

    def test_an_undeclared_slug_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, second_deps='T-0001, T-0007 [gamma]')
            result, _ = run(tmp, alpha)
            self.assertEqual(result.returncode, 1)
            self.assertIn('refused: task T-0002 depends on T-0007 [gamma], but no sibling named gamma is declared', result.stdout)

    def test_a_sibling_without_a_schema_5_board_is_refused_once_at_its_first_reference(self):
        cases = ((None, 'missing'), (BETA_BOARD.replace('tackle-workspace/5', 'tackle-workspace/4'), 'old'))
        for beta, label in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                alpha, _ = build(tmp, second_deps='T-0007 [api], T-0008 [api]', beta=beta)
                result, _ = run(tmp, alpha)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout.count('refused: ' + NO_BOARD), 1, result.stdout)
                self.assertNotIn('not on the sibling', result.stdout)

    def test_a_malformed_row_on_a_sibling_board_adds_no_refusal_of_its_own(self):
        beta = BETA_BOARD + '| not a task row\n'
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, beta=beta)
            result, _ = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_bad_declarations_are_ignored_so_their_references_are_undeclared(self):
        rows = {'outside path': '| api | ../../outside | x |', 'absolute path': '| api | /tmp/x | x |',
                'nested path': '| api | docs/plans/a/b | x |', 'trailing slash': '| api | docs/plans/beta/ | x |',
                'non-slug': '| Api | docs/plans/beta | x |',
                'two cells': '| api | docs/plans/beta |', 'no closing bar': '| api | docs/plans/beta | x'}
        for label, row in rows.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                agents = AGENTS_HEAD + '## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n' + row + '\n'
                alpha, _ = build(tmp, agents=agents)
                result, _ = run(tmp, alpha)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn('refused: task T-0002 depends on T-0007 [api], but no sibling named api is declared', result.stdout)

    def test_a_table_without_the_header_row_declares_nothing(self):
        agents = AGENTS_HEAD + '## Sibling workspaces\n\n| api | docs/plans/beta | api split |\n'
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, agents=agents)
            result, _ = run(tmp, alpha)
            self.assertEqual(result.returncode, 1)
            self.assertIn('refused: task T-0002 depends on T-0007 [api], but no sibling named api is declared', result.stdout)

    def test_a_same_line_comment_before_the_section_heading_is_removed_and_the_section_is_read(self):
        agents = AGENTS_HEAD + '<!-- generated --> ## Sibling workspaces\n\n' + DECLARED.split('\n\n', 1)[1]
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, agents=agents)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('xnode s-prog', out.read_text(encoding='utf-8'))

    def test_a_backticked_path_cell_declares_the_sibling(self):
        agents = AGENTS_HEAD + DECLARED.replace('| docs/plans/beta |', '| `docs/plans/beta` |')
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, agents=agents)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('xnode s-prog', out.read_text(encoding='utf-8'))

    def test_an_invalid_row_reserves_no_slug_so_a_later_valid_row_declares_it(self):
        agents = AGENTS_HEAD + ('## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n'
                                '| api | ../../outside | bad |\n| api | docs/plans/beta | api split |\n')
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, agents=agents)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('xnode s-prog', out.read_text(encoding='utf-8'))

    def test_a_valid_row_with_a_repeated_slug_is_ignored_so_the_first_row_declares(self):
        agents = AGENTS_HEAD + ('## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n'
                                '| api | docs/plans/beta | api split |\n| api | docs/plans/gamma | other |\n')
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, agents=agents)
            write_files(Path(tmp) / 'repo/docs/plans/gamma', {'task-board.md': HEAD + '| T-0007 | Other title | `tasks/T-0007.md` | none | Complete | v |\n'})
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertIn('aria-label="api · T-0007 · Ship the client · In progress"', page)
            self.assertNotIn('Other title', page)

    def test_a_blank_line_between_two_rows_keeps_both_declarations(self):
        self.assert_two_rows_declared('| api | docs/plans/beta | x |\n\n| gamma | docs/plans/gamma | y |\n')

    def test_a_one_line_comment_between_rows_keeps_both_declarations(self):
        self.assert_two_rows_declared('| api | docs/plans/beta | x |\n<!-- note -->\n| gamma | docs/plans/gamma | y |\n')

    def test_a_multi_line_comment_between_rows_keeps_both_declarations(self):
        self.assert_two_rows_declared('| api | docs/plans/beta | x |\n<!--\nnote\n-->\n| gamma | docs/plans/gamma | y |\n')

    def test_an_unclosed_comment_run_swallows_rows_until_its_close(self):
        agents = AGENTS_HEAD + ('## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n'
                                '| api | docs/plans/beta | x |\n<!-- open\n| gamma | docs/plans/gamma | y |\n-->\n')
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, second_deps='T-0007 [api], T-0010 [gamma]', agents=agents)
            write_files(Path(tmp) / 'repo/docs/plans/gamma', {'task-board.md': HEAD + '| T-0010 | Gamma | `tasks/T-0010.md` | none | Complete | v |\n'})
            result, _ = run(tmp, alpha)
            self.assertEqual(result.returncode, 1)
            self.assertIn('refused: task T-0002 depends on T-0010 [gamma], but no sibling named gamma is declared', result.stdout)
            self.assertNotIn('no sibling named api', result.stdout)

    def test_a_fenced_block_holding_a_valid_row_declares_nothing(self):
        agents = AGENTS_HEAD + ('```\n## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n'
                                '| api | docs/plans/beta | x |\n```\n')
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, agents=agents)
            result, _ = run(tmp, alpha)
            self.assertEqual(result.returncode, 1)
            self.assertIn('refused: task T-0002 depends on T-0007 [api], but no sibling named api is declared', result.stdout)

    def test_a_brief_inside_the_sibling_but_outside_its_tasks_folder_is_refused_as_outside(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, extra_alpha='| T-0003 | Third | `../beta/other/T-0003-x.md` | none | Draft | v |\n')
            result, _ = run(tmp, alpha)
            self.assertEqual(result.returncode, 1)
            self.assertIn('refused: brief ../beta/other/T-0003-x.md for task T-0003 is outside the workspace', result.stdout)

    def assert_two_rows_declared(self, rows):
        """Two valid rows that a comment or a blank line separates both declare; the second sibling holds task T-0010."""
        agents = AGENTS_HEAD + '## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n' + rows
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, second_deps='T-0007 [api], T-0010 [gamma]', agents=agents)
            write_files(Path(tmp) / 'repo/docs/plans/gamma', {'task-board.md': HEAD + '| T-0010 | Gamma | `tasks/T-0010.md` | none | Complete | v |\n'})
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(len(re.findall(r'<g class="xnode ', out.read_text(encoding='utf-8'))), 2)

    def test_a_commented_example_declares_nothing(self):
        agents = AGENTS_HEAD + '<!--\n## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n| api | docs/plans/beta | api split |\n-->\n'
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, second_deps='T-0001', agents=agents)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn('class="xnode', out.read_text(encoding='utf-8'))

    def test_a_missing_id_on_the_sibling_board_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, second_deps='T-0001, T-0009 [api]')
            beta = BETA_BOARD.replace('| T-0009 |', '| T-0010 |')
            write_files(Path(tmp) / 'repo/docs/plans/beta', {'task-board.md': beta})
            result, _ = run(tmp, alpha)
            self.assertEqual(result.returncode, 1)
            self.assertIn('refused: task T-0002 depends on T-0009 [api], which is not on the sibling\'s board', result.stdout)

    def test_the_unknown_local_dependency_line_comes_before_the_sibling_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, second_deps='T-0099, T-0009 [gamma]')
            result, _ = run(tmp, alpha)
            self.assertEqual(result.returncode, 1)
            lines = [line for line in result.stdout.splitlines() if line.startswith('refused: ')]
            self.assertTrue(lines[0].startswith('refused: task T-0002 depends on unknown task T-0099'), lines)
            self.assertIn('no sibling named gamma is declared', lines[1])

    def test_the_grammar_reads_only_one_space_and_a_lowercase_slug_as_a_sibling_reference(self):
        for cell in ('T-0007[api]', 'T-0007  [api]', 'T-0007 [Api]'):
            with self.subTest(cell=cell), tempfile.TemporaryDirectory() as tmp:
                alpha, _ = build(tmp, second_deps=cell)
                result, _ = run(tmp, alpha)
                self.assertEqual(result.returncode, 1)
                self.assertIn('refused: task T-0002 depends on unknown task T-0007', result.stdout)

    def test_a_plan_without_sibling_references_draws_no_external_node_or_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, _ = build(tmp, second_deps='T-0001', agents=AGENTS_HEAD)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertNotIn('class="xnode', page)
            self.assertNotIn('x_api', page)
            record = json.loads(html.unescape(re.search(r'<meta name="tackle-input-digest" content="([^"]*)">', page).group(1)))
            self.assertFalse([name for name in record['inputs'] if name.startswith('api:')])


if __name__ == '__main__':
    unittest.main()
