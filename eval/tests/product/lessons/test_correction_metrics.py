"""Execute the installed retro recipes on synthetic sources and valid alternatives."""
from pathlib import Path
import contextlib, json, os, subprocess, sys, tempfile, unittest
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root
TEMPLATE = current_root(ROOT) / 'references/retro.tmpl.md'

def fixture_task(number):
    return 'T-' + str(number).zfill(2)
FIXTURE_TASK_1 = fixture_task(1)
FIXTURE_TASK_14 = fixture_task(14)
FIXTURE_TASK_2 = fixture_task(2)
FIXTURE_TASK_3 = fixture_task(3)
FIXTURE_TASK_99 = fixture_task(99)

def event(task, number, claim=True, kind='correction-validation'):
    return '### Event ' + task + '-' + str(number) + '\nTask: ' + task + '\nRun ID: run/' + task + '/' + str(number) + '\nKind: ' + kind + '\nFailure ID: fault-' + str(number) + '\nObserved: Native validation failed; exit 1\nCorrection: Correct the implementation\nCheck: python3 -I check.py; exit 1\nResult: failed; exit 1\n' + ('Cycle count: ' + str(number) + '\n' if claim else '') + '\n'

def usage(task, path, count=1):
    return '| run | finish | ' + task + ' | executor | synthetic | fast | synthetic | low | n/a | failed | ' + str(count) + ' | n/a | n/a | ' + path + ' |\n'

@contextlib.contextmanager
def case(**labels):
    """Name the failing case without unittest sub-tests."""
    try:
        yield
    except AssertionError as exc:
        raise AssertionError(repr(labels) + ': ' + str(exc)) from exc

class CorrectionCandidateRecipeTests(unittest.TestCase):

    def execute(self, files, metric='Attempts over budget', links=(), outside=None, absolute_source=False, fifos=(), raw_output=False):
        with tempfile.TemporaryDirectory(prefix='tackle-retro-candidate-') as temporary:
            lab = Path(temporary).resolve()
            root = lab / 'workspace'
            root.mkdir()
            binaries = lab / 'bin'
            binaries.mkdir()
            (binaries / 'python3').symlink_to(sys.executable)
            (root / 'history.md').write_text('## 2026-10-26 · session 1\n')
            if outside is not None:
                (lab / 'outside.md').write_text(outside)
            if absolute_source:
                files = {**files, 'resource-usage.md': usage(f'{FIXTURE_TASK_2}', str(lab / 'outside.md'))}
            for (name, text) in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            for (name, target) in links:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(target)
            for name in fifos:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                os.mkfifo(path)
            command = TEMPLATE.read_text().split('| ' + metric + ' | `', 1)[1].split('`', 1)[0]
            environment = dict(os.environ)
            environment['PATH'] = str(binaries) + os.pathsep + environment.get('PATH', '')
            result = subprocess.run(['sh', '-c', command], cwd=root, env=environment, capture_output=True, timeout=15)
            self.assertEqual((result.returncode, result.stderr), (0, b''))
            return result.stdout if raw_output else result.stdout.decode('utf-8')

    def candidates(self, output):
        return [json.loads(line[len('structured candidate: '):]) for line in output.splitlines() if line.startswith('structured candidate: ')]

    def test_markdown_source_and_report_reveal_41_plus_one_reviewable_events(self):
        output = self.execute({'resource-usage.md': usage(f'{FIXTURE_TASK_3}', f'verification-records/{FIXTURE_TASK_3}/events.md#{FIXTURE_TASK_3}-41', 41), f'verification-records/{FIXTURE_TASK_3}/events.md': ''.join((event(f'{FIXTURE_TASK_3}', n) for n in range(1, 42))), f'reports/{FIXTURE_TASK_14}-report.md': event(f'{FIXTURE_TASK_14}', 1, claim=False)})
        candidates = self.candidates(output)
        self.assertEqual(len(candidates), 42)
        self.assertEqual({c['cyclecount'] for c in candidates if c['task'] == f'{FIXTURE_TASK_3}'}, {str(n) for n in range(1, 42)})
        self.assertEqual(next((c for c in candidates if c['task'] == f'{FIXTURE_TASK_14}'))['cyclecount'], 'n/a')
        self.assertNotIn('none', output.splitlines())
        self.assertNotIn(f'{FIXTURE_TASK_3} 861', output)
        self.assertNotIn('over cap:', output)
        self.assertTrue(all((c['locations'] and c['observed'] and c['check'] for c in candidates)))
        self.assertIn('Attempts over budget: n/a;', output)
        no_outer = self.execute({'resource-usage.md': usage(f'{FIXTURE_TASK_3}', 'raw/events.md').strip().strip('|') + '\n', 'raw/events.md': event(f'{FIXTURE_TASK_3}', 1)})
        self.assertEqual(len(self.candidates(no_outer)), 1)
        self.assertNotIn('none', no_outer.splitlines())
        missing_anchor = self.execute({'resource-usage.md': usage(f'{FIXTURE_TASK_3}', 'raw/events.md#missing'), 'raw/events.md': event(f'{FIXTURE_TASK_3}', 1)})
        self.assertIn('unresolved cited anchor', missing_anchor)
        shared = self.execute({'resource-usage.md': usage(f'{FIXTURE_TASK_1}', 'raw/events.md') + usage(f'{FIXTURE_TASK_2}', 'raw/events.md'), 'raw/events.md': event(f'{FIXTURE_TASK_1}', 1) + event(f'{FIXTURE_TASK_2}', 1)})
        self.assertEqual(len(self.candidates(shared)), 2)
        self.assertNotIn('n/a:', shared)

    def test_legacy_only_output_and_observed_empty_alternative_stay_unchanged(self):
        archive = f'## 2026-10-25 · session 1\n{FIXTURE_TASK_2} attempt 1: first failed\n'
        history = f'## 2026-10-26 · session 2\n{FIXTURE_TASK_2} correction cycle 2 of 3: second failed\n{FIXTURE_TASK_2} correction 3 of 3: third failed\n### State snapshot\n{FIXTURE_TASK_2} attempt 9: copied summary\n'
        output = self.execute({'history-archive.md': archive, 'history.md': history})
        self.assertEqual(output.splitlines(), [f'history-archive.md:2: {FIXTURE_TASK_2} attempt 1: first failed', f'history.md:2: {FIXTURE_TASK_2} correction cycle 2 of 3: second failed', f'history.md:3: {FIXTURE_TASK_2} correction 3 of 3: third failed', f'{FIXTURE_TASK_2} 3'])
        self.assertEqual(self.execute({}).splitlines(), ['none'])
        literal = f'{FIXTURE_TASK_2} attempt 1: first\u2028second\r\n'
        raw = self.execute({'history.md': '## 2026-10-26 · session 1\r\n' + literal}, raw_output=True)
        self.assertEqual(raw, ('history.md:2: ' + literal + f'{FIXTURE_TASK_2} 1\n').encode('utf-8'))

    def test_duplicate_conflicting_initial_and_fenced_records_remain_distinct(self):
        complete = event(f'{FIXTURE_TASK_1}', 1).replace('Check: python3 -I check.py; exit 1', '**Check:** python3 -I check.py --pattern *')
        output = self.execute({f'reports/{FIXTURE_TASK_1}-report.md': complete + complete + 'Host: harmless metadata\n' + event(f'{FIXTURE_TASK_1}', 2, kind='initial-validation') + '```text\n' + event(f'{FIXTURE_TASK_1}', 3) + '```\n'})
        candidates = self.candidates(output)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(len(candidates[0]['locations']), 2)
        self.assertEqual(candidates[0]['check'], 'python3 -I check.py --pattern *')
        conflict = self.execute({f'reports/{FIXTURE_TASK_1}-report.md': complete + complete.replace('Observed: Native validation failed', 'Observed: Different failure')})
        self.assertIn('conflicting event identity', conflict)
        facts = self.candidates(conflict)
        self.assertEqual(len(facts), 2)
        self.assertEqual({fact['observed'] for fact in facts}, {'Native validation failed; exit 1', 'Different failure; exit 1'})
        self.assertEqual({fact['fact_completeness'] for fact in facts}, {'conflicting'})
        self.assertTrue(all(fact['conflict_reason'] == 'event-identity' for fact in facts))
        location = f'reports/{FIXTURE_TASK_1}-report.md:'
        step = complete.count('\n')
        self.assertEqual({fact['observed']: fact['locations'] for fact in facts}, {
            'Native validation failed; exit 1': [location+'1'],
            'Different failure; exit 1': [location+str(step+1)]})
        self.assertIn('Attempts over budget: n/a;', conflict)
        changed = complete.replace('Observed: Native validation failed', 'Observed: Different failure')
        repeated = self.execute({f'reports/{FIXTURE_TASK_1}-report.md': complete+changed+changed+complete})
        repeated_facts = self.candidates(repeated)
        self.assertEqual(len(repeated_facts), 2)
        self.assertEqual({fact['observed']: fact['locations'] for fact in repeated_facts}, {
            'Native validation failed; exit 1': [location+'1', location+str(3*step+1)],
            'Different failure; exit 1': [location+str(step+1), location+str(2*step+1)]})
        self.assertIn('Attempts over budget: n/a;', repeated)
        self.assertNotIn('none', conflict.splitlines())
        related = self.execute({f'reports/{FIXTURE_TASK_1}-report.md': complete + complete.replace(f'Event {FIXTURE_TASK_1}-1', 'Event another-id')})
        self.assertEqual(len(self.candidates(related)), 2)
        self.assertIn('related run/failure', related)
        listed = self.execute({f'reports/{FIXTURE_TASK_1}-report.md': event(f'{FIXTURE_TASK_1}', 1).replace('Kind: correction-validation', '- **Kind:** Correction-validation')})
        self.assertEqual(len(self.candidates(listed)), 1)
        commented = self.execute({f'reports/{FIXTURE_TASK_1}-report.md': event(f'{FIXTURE_TASK_1}', 1).replace('Cycle count: 1', 'Cycle count: 1 <!-- annotation -->')})
        self.assertEqual(self.candidates(commented)[0]['cyclecount'], '1')
        literal_check = '`echo "<!-- literal -->" *`'
        quoted = self.execute({f'reports/{FIXTURE_TASK_1}-report.md': event(f'{FIXTURE_TASK_1}', 1).replace('python3 -I check.py; exit 1', literal_check)})
        self.assertEqual(self.candidates(quoted)[0]['check'], literal_check)
        for (first, last) in (('correction-validation', 'initial-validation'), ('initial-validation', 'correction-validation')):
            contradictory = self.execute({f'reports/{FIXTURE_TASK_1}-report.md': '### Event E1\nKind: ' + first + '\nCycle count: 4\nKind: ' + last + '\n'})
            facts = self.candidates(contradictory)
            self.assertEqual(len(facts), 1)
            self.assertEqual(set(facts[0]['conflicting_fields']['kind']), {'correction-validation', 'initial-validation'})
            self.assertEqual(facts[0]['cyclecount'], '4')
            self.assertIn('Attempts over budget: n/a;', contradictory)
            self.assertNotIn('none', contradictory.splitlines())

    def test_unsafe_missing_and_incomplete_sources_never_become_bare_none(self):
        for (source, links) in (('../outside.md', ()), ('verification-records/events.md', (('verification-records/events.md', '../../outside.md'),)), ('missing.md', ())):
            with case(source=source):
                output = self.execute({'resource-usage.md': usage(f'{FIXTURE_TASK_2}', source)}, links=links, outside=event(f'{FIXTURE_TASK_99}', 1))
                self.assertIn('n/a:', output)
                self.assertNotIn('none', output.splitlines())
                self.assertEqual(self.candidates(output), [])
        malformed = event(f'{FIXTURE_TASK_2}', 1).replace('Observed: Native validation failed; exit 1\n', '')
        output = self.execute({f'reports/{FIXTURE_TASK_2}-report.md': malformed})
        self.assertIn('incomplete', output)
        self.assertEqual(len(self.candidates(output)), 1)
        self.assertEqual(self.candidates(output)[0]['fact_completeness'], 'partial')
        partial = self.execute({f'reports/{FIXTURE_TASK_2}-report.md': '### Event E1\nKind: correction-validation\nCycle count: 4\n'})
        facts = self.candidates(partial)
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]['cyclecount'], '4')
        self.assertEqual(facts[0]['kind'], 'correction-validation')
        self.assertEqual(facts[0]['fact_completeness'], 'partial')
        for unknown in ('n/a', '-', '', '²'):
            unmeasured = self.execute({'resource-usage.md': usage(f'{FIXTURE_TASK_2}', 'raw/events.md', unknown), 'raw/events.md': event(f'{FIXTURE_TASK_2}', 1)})
            self.assertIn('n/a:', unmeasured)
            self.assertNotIn('none', unmeasured.splitlines())
        non_ascii = self.execute({f'reports/{FIXTURE_TASK_2}-report.md': event(f'{FIXTURE_TASK_2}', 1).replace('Cycle count: 1', 'Cycle count: ²')})
        self.assertIn('unsupported Cycle count', non_ascii)
        valid = self.execute({'resource-usage.md': usage(f'{FIXTURE_TASK_2}', 'raw/events.md'), 'raw/events.md': event(f'{FIXTURE_TASK_2}', 1)})
        self.assertEqual(len(self.candidates(valid)), 1)
        self.assertNotIn('n/a:', valid)
        mixed = self.execute({'resource-usage.md': usage(f'{FIXTURE_TASK_2}', '`raw/events.md` E-missing'), 'raw/events.md': event(f'{FIXTURE_TASK_2}', 1)})
        self.assertIn('stable event reference is unresolved: E-missing', mixed)
        no_result = self.execute({f'reports/{FIXTURE_TASK_2}-report.md': event(f'{FIXTURE_TASK_2}', 1).replace('Result: failed; exit 1\n', '')})
        facts = self.candidates(no_result)
        self.assertEqual(facts[0]['fact_completeness'], 'partial')
        self.assertIn('result', facts[0]['missing_fields'])
        absolute = self.execute({}, outside=event(f'{FIXTURE_TASK_99}', 1), absolute_source=True)
        self.assertIn('n/a:', absolute)
        self.assertEqual(self.candidates(absolute), [])
        fifo = self.execute({'resource-usage.md': usage(f'{FIXTURE_TASK_2}', 'raw/events.md')}, fifos=('raw/events.md',))
        self.assertIn('not a regular file', fifo)
        self.assertEqual(self.candidates(fifo), [])

    def test_empty_blockers_are_excluded_without_hiding_real_state_events(self):
        history = f'## 2026-10-26 · session 1\nBlocked on: nothing\n- Blocked on: nothing.\n- **Blocked on:** nothing\nBlocked on: owner answer\n{FIXTURE_TASK_2} Blocked\n### State snapshot\nBlocked on: copied snapshot\n'
        output = self.execute({'history.md': history}, metric='Blocked durations')
        self.assertNotIn('nothing', output)
        self.assertNotIn('copied snapshot', output)
        self.assertIn('Blocked on: owner answer', output)
        self.assertIn(f'{FIXTURE_TASK_2} Blocked', output)
if __name__ == '__main__':
    unittest.main()
