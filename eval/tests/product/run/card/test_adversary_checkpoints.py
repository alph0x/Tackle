"""The adversary-checkpoint recipe judges fixture workspaces as the RUN guide says, and the card, the
PLAN card and the guide's subsection point at each other."""
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)
RECIPE = INSTALL / 'references/recipes/adversary-checkpoints.md'
GUIDES = INSTALL / 'references/guides'

ONE, TWO = 'T-%02d' % 1, 'T-%02d' % 2
LIVE, ABSENT = 'decisions.md#D' + '-%d' % 12, 'decisions.md#D' + '-%d' % 999
PATHS = {'reviews/one-adversary.json', 'reviews/two-adversary.json', 'reviews/lock.json', 'decisions.md', LIVE}
F, A = ('failure', 'cmd=x; class=implementation; assert=a; out=h1'), ('attempt', None)
G = ('failure', 'cmd=x; class=implementation; assert=b; out=h2')


def line(moment, verdict='reviews/one-adversary.json', independence='fresh session, same model family'):
    return '**Adversary**: %s · %s · claude-opus-5-5 session sess7 · %s\n' % (moment, verdict, independence)


def report(*lines):
    return '# %s report\n\nWork done.\n\n' % ONE + ''.join(lines) + '\n**Remains**: none\n'


def task(status, text, events, **extra):
    return dict({'status': status, 'report': text, 'events': events}, **extra)


# (case id, tasks, None when no finding is expected, else the one task id every finding names)
CASES = [
    ('pos01-complete-with-review', {ONE: task('Complete', report(line('lock', 'reviews/lock.json'), line('complete')), [('review', 'lock')])}, None),
    ('pos02-new-signature-needs-none', {ONE: task('Complete', report(line('complete')), [F, A, G, A])}, None),
    ('pos03-open-task-needs-no-complete-line', {ONE: task('In progress', '', [F, A])}, None),
    ('pos04-repeat-reviewed-before-attempt', {ONE: task('Checking', report(line('repeat-failure')), [F, A, F, ('review', 'repeat-failure'), A])}, None),
    ('pos05-repeat-not-yet-attempted', {ONE: task('Checking', '', [F, A, F])}, None),
    ('pos06-two-tasks-one-signature-each', {ONE: task('In progress', '', [F, A]), TWO: task('In progress', '', [F, A])}, None),
    ('pos07-waived-complete', {ONE: task('Complete', report(line('complete', LIVE, 'waived')), [])}, None),
    ('pos08-completed-before-adoption', {ONE: task('Complete', report(), [], before_adoption=True)}, None),
    ('neg01-complete-without-review', {ONE: task('Complete', report(), [])}, ONE),
    ('neg02-complete-with-lock-only', {ONE: task('Complete', report(line('lock', 'reviews/lock.json')), [('review', 'lock')])}, ONE),
    ('neg03-repeat-attempted-without-review', {ONE: task('In progress', '', [F, A, F, A])}, ONE),
    ('neg04-review-after-the-attempt', {ONE: task('In progress', report(line('repeat-failure')), [F, A, F, A, ('review', 'repeat-failure')])}, ONE),
    ('neg05-unknown-moment', {ONE: task('In progress', report(line('final')), [])}, ONE),
    ('neg06-verdict-path-missing', {ONE: task('Complete', report(line('complete', 'reviews/absent.json')), [])}, ONE),
    ('neg07-complete-repeat-never-reviewed', {ONE: task('Complete', report(line('complete')), [F, A, F, A])}, ONE),
    ('neg08-only-the-offending-task-is-named', {ONE: task('Complete', report(line('complete')), []), TWO: task('Complete', report(), [])}, TWO),
    ('neg09-repeat-not-adjacent', {ONE: task('In progress', '', [F, A, G, A, F, A])}, ONE),
    ('neg10-review-before-the-repeat', {ONE: task('In progress', report(line('repeat-failure')), [F, A, ('review', 'repeat-failure'), F, A])}, ONE),
    ('neg11-lock-line-verdict-missing', {ONE: task('In progress', report(line('lock', 'reviews/absent.json')), [('review', 'lock')])}, ONE),
    ('neg12-moment-is-a-superstring', {ONE: task('Complete', report(line('incomplete')), [])}, ONE),
    ('neg13-empty-independence-cell', {ONE: task('Complete', report(line('complete', independence='')), [])}, ONE),
    ('neg14-waiver-without-decision', {ONE: task('Complete', report(line('complete', 'reviews/one-adversary.json', 'waived')), [])}, ONE),
    ('neg15-waiver-unknown-decision', {ONE: task('Complete', report(line('complete', ABSENT, 'waived')), [])}, ONE),
    ('neg16-another-moment-does-not-clear-a-repeat', {ONE: task('In progress', report(line('lock', 'reviews/lock.json')), [F, A, F, ('review', 'lock'), A])}, ONE),
    ('neg17-moment-is-a-prefix-match', {ONE: task('Complete', report(line('completed')), [])}, ONE),
    ('neg18-a-non-independent-review-does-not-satisfy', {ONE: task('Complete', report(line('complete', independence='not independent: same session')), [])}, ONE),
    ('neg19-indented-line-with-a-bad-moment', {ONE: task('In progress', '  ' + line('final'), [])}, ONE),
    ('neg20-list-item-line-with-a-dead-verdict', {ONE: task('In progress', '- ' + line('lock', 'reviews/absent.json'), [])}, ONE),
    ('pos09-list-item-complete-line-counts', {ONE: task('Complete', '- ' + line('complete'), [])}, None),
]


def load_recipe():
    text = RECIPE.read_text(encoding='utf-8')
    parts = text.split('```python\n')
    assert len(parts) == 2, 'the recipe must hold exactly one fenced python block'
    namespace = {'__name__': 'tested_recipe'}
    exec(compile(parts[1].split('\n```')[0], str(RECIPE), 'exec'), namespace)
    return namespace


class AdversaryCheckpoints(unittest.TestCase):
    def test_fixture_workspaces_are_judged_by_the_shipped_recipe(self):
        findings_of = load_recipe()['adversary_findings']
        self.assertEqual(len(CASES), 29)
        for case, tasks, expected in CASES:
            with self.subTest(case=case):
                found = findings_of(tasks, set(PATHS))
                self.assertIsInstance(found, list)
                if expected is None:
                    self.assertEqual(found, [])
                    continue
                self.assertTrue(found)
                for item in found:
                    self.assertIsInstance(item, str)
                    self.assertIn(expected, item)
                    for other in set(tasks) - {expected}:
                        self.assertNotIn(other, item)

    def test_the_recipe_file_holds_one_python_block_and_nothing_else(self):
        text = RECIPE.read_text(encoding='utf-8')
        self.assertTrue(text.startswith('```python\n'))
        self.assertTrue(text.rstrip().endswith('```'))
        self.assertEqual(text.count('```'), 2)

    def test_the_cards_point_at_the_subsection_that_exists(self):
        run = (GUIDES / 'run.md').read_text(encoding='utf-8')
        self.assertEqual(run.count('<a id="adversary-checkpoints"></a>'), 1)
        self.assertEqual(len(re.findall(r'^### Adversary checkpoints$', run, re.M)), 1)
        for name in ('run-card.md', 'plan-card.md'):
            self.assertIn('run.md#adversary-checkpoints', (GUIDES / name).read_text(encoding='utf-8'))
        for kept in ('majority vote', 'frontier checker'):
            self.assertIn(kept, run)


if __name__ == '__main__':
    unittest.main()
