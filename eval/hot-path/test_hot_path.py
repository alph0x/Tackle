"""T-33 hot-path checks: the RUN-chain measure, the duplicate detector and the RUN card's transitions.

Fixture cases build disposable repositories in temporary directories (D-36) and never touch this
checkout. Repository cases read this checkout: the RUN chain is within budget (C1), it holds no
near-duplicate unit (C3), the card's transition table is structurally complete (C5), and every depth
section of run.md is reached from the card. Standard library only; no network or model call.
"""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import duplicates  # noqa: E402
import load_chain  # noqa: E402

CARD = ROOT / 'references/guides/run-card.md'
RUN_MD = ROOT / 'references/guides/run.md'
STATES = ('Draft', 'Ready to run', 'In progress', 'Checking', 'Complete', 'Blocked', 'Interrupted', 'Skipped',
          'Unverifiable', 'Waiting on owner')
ENTRY_STATE = 'Entry state'


def filler(count, word='word'):
    return ' '.join([word] * count)


def write(root, name, text):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def run_tool(script, *args):
    return subprocess.run([sys.executable, str(HERE / script)] + [str(arg) for arg in args],
                          capture_output=True, text=True)


def chain_fixture(root, card, skill_words=100, brief_words=200, files=None):
    write(root, 'SKILL.md', filler(skill_words) + '\n')
    write(root, 'references/task.tmpl.md', filler(brief_words) + '\n')
    write(root, 'references/guides/run-card.md', card)
    for name, text in (files or {}).items():
        write(root, name, text)


def table_rows(text, heading):
    """Cells of the first table after `heading`, header and delimiter excluded."""
    lines = text.split('\n')
    start = lines.index(heading)
    rows, seen_table = [], False
    for line in lines[start + 1:]:
        if line.startswith('#'):
            break
        if line.strip().startswith('|'):
            seen_table = True
            cells = duplicates.table_cells(line)
            if not duplicates.is_delimiter(line):
                rows.append(cells)
        elif seen_table:
            break
    return rows[1:]


def state_list(cell):
    names = [name.strip().strip('`').strip() for name in re.split(r',|\bor\b', cell)]
    return [name for name in names if name]


def transition_problems(card_text):
    """C5: problems with the card's transition table, as strings (empty when the table is complete)."""
    problems, exits = [], {}
    rows = table_rows(card_text, '## State transitions')
    if not rows:
        return ['no transition table under ## State transitions']
    for cells in rows:
        if len(cells) != 4:
            problems.append('row without 4 cells: %r' % cells)
            continue
        sources, targets, trigger, budget = state_list(cells[0]), state_list(cells[1]), cells[2], cells[3]
        for name in sources:
            if name not in STATES:
                problems.append('unknown From state: %r' % name)
        for name in targets:
            if name not in STATES and name != ENTRY_STATE:
                problems.append('unknown To state: %r' % name)
        if ENTRY_STATE in targets and not set(sources) <= {'Waiting on owner', 'Interrupted'}:
            problems.append('entry state as a destination of %r' % sources)
        for name in sources:
            exits.setdefault(name, []).append((set(targets), trigger.lower(), budget.lower()))
    for name in STATES:
        if not exits.get(name):
            problems.append('no exit from ' + name)
    for targets, trigger, budget in exits.get('Complete', []):
        if 'authorized reopening' not in trigger or 'keeps spent cycles' not in budget:
            problems.append('Complete exits other than by an authorized reopening that keeps spent cycles')
    waiting = set().union(*(targets for targets, _, _ in exits.get('Waiting on owner', []))) \
        if exits.get('Waiting on owner') else set()
    if waiting != {ENTRY_STATE, 'Skipped'}:
        problems.append('Waiting on owner exits to %r, not exactly its entry state and Skipped' % sorted(waiting))
    return problems


class WordCountTests(unittest.TestCase):
    def test_counts_like_wc_under_the_c_locale(self):
        self.assertEqual(load_chain.count_words(b''), 0)
        self.assertEqual(load_chain.count_words(b'a \xe2\x80\x94 b\n'), 3)
        self.assertEqual(load_chain.count_words('x y'.encode()), 1)
        self.assertEqual(load_chain.count_words(b'\ta\n\nb\x0bc\x0cd\re  '), 5)
        self.assertEqual(load_chain.count_words(b'| From | To |\n|---|---|\n'), 6)


class LoadChainFixtureTests(unittest.TestCase):
    """C1 and C2 on fixture repositories."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_mandatory_link_adds_its_target_and_depth_links_do_not(self):
        card = ('# Card\n\nSee [the guide](extra.md) first.\n\n## Depth (on demand)\n\n'
                '[deep](deep.md)\n')
        chain_fixture(self.root, card, files={'references/guides/extra.md': filler(300) + '\n',
                                              'references/guides/deep.md': filler(5000) + '\n'})
        words, card_words, mandatory = load_chain.measure(self.root)
        self.assertEqual(card_words, load_chain.count_words(card.encode()))
        self.assertEqual(words, 100 + card_words + 300 + 200)
        self.assertEqual(mandatory, ['SKILL.md', 'references/guides/run-card.md', 'references/guides/extra.md',
                                     'references/task.tmpl.md'])
        without = card.replace('See [the guide](extra.md) first.', 'See the guide first.')
        write(self.root, 'references/guides/run-card.md', without)
        self.assertEqual(load_chain.measure(self.root)[0], 100 + load_chain.count_words(without.encode()) + 200)

    def test_an_anchored_link_adds_only_its_section(self):
        guide = ('# Guide\n\n' + filler(50) + '\n\n## Part one\n\n' + filler(70) + '\n\n'
                 '<a id="second"></a>\n## Part two\n\n' + filler(30) + '\n\n### Inside two\n\n' + filler(9) +
                 '\n\n## Part three\n\n' + filler(400) + '\n')
        card = '# Card\n\nRead [one](extra.md#part-one) and [two](extra.md#second).\n'
        chain_fixture(self.root, card, files={'references/guides/extra.md': guide})
        words, card_words, mandatory = load_chain.measure(self.root)
        part_one = load_chain.count_words(b'## Part one\n\n' + filler(70).encode())
        part_two = load_chain.count_words(('<a id="second"></a>\n## Part two\n\n' + filler(30) +
                                           '\n\n### Inside two\n\n' + filler(9)).encode())
        self.assertEqual(words, 100 + card_words + part_one + part_two + 200)
        self.assertIn('references/guides/extra.md#part-one', mandatory)
        self.assertIn('references/guides/extra.md#second', mandatory)

    def test_reference_links_count_and_fenced_external_and_self_links_do_not(self):
        card = ('# Card\n\nRead [the guide][g], [the web](https://example.com) and [this](#depth-on-demand).\n\n'
                '```text\n[fenced](fenced.md)\n```\n\n[g]: extra.md\n\n## Depth (on demand)\n\nNothing.\n')
        chain_fixture(self.root, card, files={'references/guides/extra.md': filler(40) + '\n'})
        words, card_words, mandatory = load_chain.measure(self.root)
        self.assertEqual(words, 100 + card_words + 40 + 200)
        self.assertEqual(mandatory[2:-1], ['references/guides/extra.md'])

    def test_a_chain_over_budget_exits_1(self):
        chain_fixture(self.root, '# Card\n\n' + filler(300) + '\n', skill_words=3000, brief_words=1000)
        result = run_tool('load_chain.py', '--repo', self.root)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertRegex(result.stdout, r'^run-chain words=4302 card=302 mandatory=SKILL\.md,'
                                        r'references/guides/run-card\.md,references/task\.tmpl\.md\n$')

    def test_a_card_over_budget_exits_1_even_inside_the_chain_budget(self):
        chain_fixture(self.root, filler(801) + '\n')
        result = run_tool('load_chain.py', '--repo', self.root)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('card=801 ', result.stdout)

    def test_the_budget_boundaries_pass(self):
        chain_fixture(self.root, filler(800) + '\n', skill_words=1600, brief_words=1600)
        result = run_tool('load_chain.py', '--repo', self.root)
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertIn('run-chain words=4000 card=800 ', result.stdout)

    def test_a_missing_card_link_or_anchor_exits_2(self):
        write(self.root, 'SKILL.md', 'x\n')
        write(self.root, 'references/task.tmpl.md', 'y\n')
        self.assertEqual(run_tool('load_chain.py', '--repo', self.root).returncode, 2)
        write(self.root, 'references/guides/run-card.md', 'Read [gone](gone.md).\n')
        self.assertEqual(run_tool('load_chain.py', '--repo', self.root).returncode, 2)
        write(self.root, 'references/guides/extra.md', '# Guide\n')
        write(self.root, 'references/guides/run-card.md', 'Read [gone](extra.md#nowhere).\n')
        result = run_tool('load_chain.py', '--repo', self.root)
        self.assertEqual(result.returncode, 2)
        self.assertIn('anchor missing', result.stderr)


class DuplicateDetectorTests(unittest.TestCase):
    """C4 and the pairing rules, on fixture files."""

    LONG = ('Before repeating an interrupted command or completion update the coordinator inspects the '
            'working tree, the process results, the board and report revisions, the latest checkpoint and '
            'every raw record to determine whether the effect already occurred.')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def found(self, first, second):
        entries = [('a.md', unit) for unit in duplicates.units(first)]
        entries += [('b.md', unit) for unit in duplicates.units(second)]
        return duplicates.pairs(entries)

    def test_a_verbatim_copy_is_reported(self):
        found = self.found('Intro line here.\n\n' + self.LONG + '\n', self.LONG + '\n')
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][0], 1.0)
        self.assertEqual((found[0][1], found[0][2]), (('a.md', 3), ('b.md', 1)))

    def test_a_near_verbatim_copy_with_three_words_changed_is_reported(self):
        changed = self.LONG.replace('interrupted', 'stopped').replace('latest', 'newest').replace('already',
                                                                                                    'really')
        self.assertEqual(len(duplicates.words(self.LONG)), 36)
        found = self.found(self.LONG + '\n', changed + '\n')
        self.assertEqual(len(found), 1)
        self.assertAlmostEqual(found[0][0], 26 / 42)
        self.assertGreaterEqual(found[0][0], duplicates.THRESHOLD)

    def test_two_distinct_sentences_do_not_pair(self):
        found = self.found(self.LONG + '\n', 'Release work records the explicit workspace scope before the sweep '
                                             'runs, and an unknown scope blocks the tag.\n')
        self.assertEqual(found, [])

    def test_similar_rows_of_one_table_never_pair_but_rows_of_two_tables_do(self):
        first = '| In progress | Blocked | an unresolved contradiction stops the task with its packet | none |'
        second = '| Checking | Blocked | an unresolved contradiction stops the task with its packet | none |'
        header = '| From | To | Trigger | Budget effect |\n|---|---|---|---|\n'
        one_table = header + first + '\n' + second + '\n'
        self.assertGreaterEqual(duplicates.jaccard(duplicates.trigrams(duplicates.words(first)),
                                                   duplicates.trigrams(duplicates.words(second))), 0.5)
        entries = [('a.md', unit) for unit in duplicates.units(one_table)]
        self.assertEqual(duplicates.pairs(entries), [])
        two_tables = header + first + '\n\nBetween the tables.\n\n' + header + second + '\n'
        entries = [('a.md', unit) for unit in duplicates.units(two_tables)]
        self.assertEqual(len(duplicates.pairs(entries)), 1)
        prose = 'Blocked: an unresolved contradiction stops the task with its packet, and none is spent.'
        self.assertEqual(len(self.found(one_table, prose + '\n')), 2)

    def test_a_paraphrase_is_missed_by_design_and_left_to_the_reviewer(self):
        # Same rule, different words: a 3-gram detector cannot see it. The fresh reviewer's comparison of
        # the rule diff, the card and the depth owns semantic duplicates.
        original = 'Two identical no-progress observations stop the task even if fewer than three cycles were spent.'
        paraphrase = ('When the same failure shows up twice without any change, halt the work before the '
                      'three-cycle cap is reached.')
        self.assertEqual(self.found(original + '\n', paraphrase + '\n'), [])

    def test_markup_does_not_reach_the_eight_word_floor(self):
        row = '| **Stop** | the `task` | once the pool empties |'
        self.assertGreaterEqual(load_chain.count_words(row.encode()), 8)
        self.assertEqual(len(duplicates.words(row)), 7)
        self.assertEqual(self.found(row + '\n', row + '\n'), [])
        sentence = 'Stop the task once the shared pool empties.'
        self.assertEqual(len(self.found(sentence + '\n', sentence + '\n')), 1)

    def test_fenced_code_headings_and_anchors_are_not_units(self):
        fenced = '```text\n' + self.LONG + '\n```\n\n# ' + self.LONG + '\n\n<a id="x"></a>\n'
        self.assertEqual(duplicates.units(fenced), [])
        self.assertEqual(self.found(fenced, self.LONG + '\n'), [])

    def test_sentences_split_inside_paragraphs_and_list_items(self):
        text = ('Intro.\n\n1. **Read.** Read the board and record its hash. Then pick\n   the first row.\n'
                '- Second item. `Code` starts here.\n')
        found = [(unit.line, unit.text) for unit in duplicates.units(text)]
        self.assertEqual(found, [(1, 'Intro.'), (3, '**Read.** Read the board and record its hash.'),
                                 (3, 'Then pick the first row.'), (5, 'Second item.'), (5, '`Code` starts here.')])

    def test_the_command_prints_each_pair_and_the_count(self):
        write(self.root, 'a.md', self.LONG + '\n')
        write(self.root, 'b.md', 'Intro line here.\n\n' + self.LONG + '\n')
        result = run_tool('duplicates.py', '--repo', self.root, '--files', 'a.md', 'b.md')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, 'duplicate a.md:1 ~ b.md:3 j=1.00\nduplicates=1\n')
        write(self.root, 'b.md', 'Nothing alike.\n')
        result = run_tool('duplicates.py', '--repo', self.root, '--files', 'a.md', 'b.md')
        self.assertEqual((result.returncode, result.stdout), (0, 'duplicates=0\n'))
        self.assertEqual(run_tool('duplicates.py', '--repo', self.root, '--files', 'gone.md').returncode, 2)


class RepositoryTests(unittest.TestCase):
    """C1, C3 and C5 on this checkout."""

    def test_c1_the_run_chain_is_within_budget(self):
        result = run_tool('load_chain.py', '--repo', ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        match = re.fullmatch(r'run-chain words=(\d+) card=(\d+) mandatory=(\S+)\n', result.stdout)
        self.assertIsNotNone(match, result.stdout)
        self.assertLessEqual(int(match.group(1)), load_chain.CHAIN_LIMIT)
        self.assertLessEqual(int(match.group(2)), load_chain.CARD_LIMIT)

    def test_c3_the_run_chain_has_no_near_duplicate_unit(self):
        result = run_tool('duplicates.py', '--repo', ROOT, '--chain', 'run')
        self.assertEqual((result.returncode, result.stdout), (0, 'duplicates=0\n'), result.stderr)

    def test_c5_the_card_transition_table_is_complete(self):
        self.assertEqual(transition_problems(CARD.read_text(encoding='utf-8')), [])

    def test_c5_the_structural_check_rejects_an_incomplete_table(self):
        text = CARD.read_text(encoding='utf-8')
        rows = [line for line in text.split('\n') if line.startswith('| Unverifiable |')]
        self.assertTrue(rows)
        broken = '\n'.join(line for line in text.split('\n') if not line.startswith('| Unverifiable |'))
        broken = re.sub(r'(?m)^(\|[^|\n]*)\bUnverifiable, ', r'\1', broken)
        self.assertIn('no exit from Unverifiable', transition_problems(broken))
        self.assertIn('| Complete | In progress | Authorized reopening |', text)
        reopened = text.replace('| Complete | In progress | Authorized reopening |',
                                '| Complete | In progress | A new request |')
        self.assertTrue(transition_problems(reopened))

    def test_the_pick_step_holds_every_write_scope_that_may_hold_edits(self):
        text = ' '.join(CARD.read_text(encoding='utf-8').split())
        pick = text.split('2. **Pick.**', 1)[1].split('3. **Claim.**', 1)[0]
        clause = re.search(r'write scope intersects no (.+?) row', pick)
        self.assertIsNotNone(clause, pick)
        self.assertEqual(set(state_list(clause.group(1))),
                         {'In progress', 'Checking', 'Interrupted', 'Waiting on owner'})

    def test_one_state_transitions_heading_in_the_run_chain_and_it_is_the_cards(self):
        card, depth = CARD.read_text(encoding='utf-8'), RUN_MD.read_text(encoding='utf-8')
        self.assertEqual((card + depth).count('## State transitions'), 1)
        self.assertIn('\n## State transitions\n', card)

    def test_every_depth_section_is_reached_from_the_card(self):
        card_lines = CARD.read_text(encoding='utf-8').split('\n')
        depth = load_chain.depth_range(card_lines)
        self.assertIsNotNone(depth, 'the card has no ## Depth (on demand) section')
        self.assertEqual(depth[1], len(card_lines), 'Depth is not the closing section')
        depth_text = '\n'.join(card_lines[depth[0]:depth[1]])
        run_lines = RUN_MD.read_text(encoding='utf-8').split('\n')
        self.assertIn('](run-card.md)', run_lines[0])
        linked = set(re.findall(r'\]\(run\.md#([^)]+)\)', depth_text))
        reached = set()
        for fragment in linked:
            section = load_chain.section_lines(run_lines, fragment, 'run.md')
            reached |= {index for index, level, _ in load_chain.headings(run_lines)
                        if level == 2 and index in section}
        sections = {index for index, level, _ in load_chain.headings(run_lines) if level == 2}
        self.assertTrue(sections)
        self.assertEqual(sorted(sections - reached), [], 'depth sections the card does not reach')


if __name__ == '__main__':
    unittest.main()
