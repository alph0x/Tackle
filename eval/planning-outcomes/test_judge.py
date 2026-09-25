"""Planning-outcome scenarios and their mechanical judge.

The three scenarios s62-s64 are small feature requests against fixture repositories. Hidden acceptance
tests beside each variant's input decide the outcome; judge.py runs them in a scratch copy through its
own isolated runner and writes a judgment that ``harness.py record --judgment`` accepts.

Every case that exercises a real fixture reads it from the git index into a scratch directory and never
runs anything in place. Messages about a variant name paths and counts only, never file content, because
held-out variants must stay unread by the people who tune the method (D-73, D-77).

Standard library only; no network, container or model call.
"""
import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
JUDGE = HERE / 'judge.py'
HARNESS = ROOT / 'eval/harness-v2/harness.py'
CHECK = ROOT / 'eval/protocol-v2/check.py'
INDEX = 'eval/scenarios/INDEX.json'
PLANNING = ('s62-caller-contract', 's63-documented-edge-rule', 's64-stored-data-compat')
SPLITS = {'v1': 'development', 'h1': 'held-out'}
JUDGMENT_KEYS = {'judge', 'outcome', 'invalid_reason', 'rule_exposure', 'scores', 'details'}
SCORE_KEYS = {'correct_action', 'evidence', 'verification_honesty', 'report_quality'}
FLAG = '--allow-model-calls'


def git(repo, *args, data=None):
    return subprocess.run(['git', '-C', str(repo)] + list(args), input=data, capture_output=True, check=True).stdout


def tracked(repo, prefix):
    """Paths in the git index under ``prefix`` (a directory, with trailing slash)."""
    out = git(repo, 'ls-files', '-z', '--', prefix)
    return sorted(name for name in out.decode('utf-8').split('\0') if name)


def staged(repo, path):
    return git(repo, 'show', ':' + path)


def materialize(repo, prefix, target):
    """Copy the staged files under ``prefix`` into ``target``; returns the relative names written."""
    names = []
    for name in tracked(repo, prefix):
        relative = name[len(prefix):]
        destination = Path(target) / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(staged(repo, name))
        names.append(relative)
    return names


def tree_sha(root):
    mapping = {}
    for path in sorted(Path(root).rglob('*')):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            mapping[relative] = hashlib.sha256(os.readlink(path).encode()).hexdigest()
        elif path.is_file():
            mapping[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()


def normalized(line):
    return ' '.join(line.split())


def run_judge(*args, timeout=300):
    return subprocess.run([sys.executable, str(JUDGE)] + [str(a) for a in args], capture_output=True, text=True,
                          timeout=timeout)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix='tackle-t37-')
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def judged(self, *args, expect=0):
        result = run_judge(*args)
        self.assertEqual(result.returncode, expect, 'judge exit %d: %s' % (result.returncode, result.stderr[-2000:]))
        return result


# ---------------------------------------------------------------------------
# A synthetic scenario in a throwaway git repository (C7-C12, C18)
# ---------------------------------------------------------------------------

DEMO_TEST = '''import unittest

import demo


class DemoTests(unittest.TestCase):
    def test_double(self):
        self.assertEqual(demo.double(2), 4)

    def test_double_negative(self):
        self.assertEqual(demo.double(-3), -6)
'''


class Synthetic(Base):
    """One synthetic scenario ``s99-demo`` with a v1 variant, staged in a temporary repository."""

    def setUp(self):
        super().setUp()
        self.repo = self.tmp / 'repo'
        self.repo.mkdir()
        git(self.repo, 'init', '-q')
        self.hidden = 'eval/scenarios/s99-demo/variants/v1/hidden/'
        self.stage_hidden({'test_demo.py': DEMO_TEST}, tests=2)

    def stage_hidden(self, files, tests, timeout=60, visible=None, pythonpath=('.',)):
        base = self.repo / self.hidden
        base.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (base / name).write_text(text)
        (base / 'hidden.json').write_text(json.dumps({
            'schema': 'tackle-hidden-tests/1', 'tests': tests, 'timeout_seconds': timeout,
            'pythonpath': list(pythonpath), 'visible': visible}))
        git(self.repo, 'add', '-A')

    def work(self, text, extra=None):
        work = self.tmp / ('work-%d' % len(list(self.tmp.glob('work-*'))))
        work.mkdir()
        (work / 'demo.py').write_text(text)
        for name, body in (extra or {}).items():
            (work / name).write_text(body)
        return work

    def judge_work(self, work, expect=0):
        out = self.tmp / ('judgment-%d.json' % len(list(self.tmp.glob('judgment-*.json'))))
        self.judged('--scenario', 's99-demo', '--variant', 'v1', '--work', work, '--out', out, '--repo', self.repo,
                    expect=expect)
        return json.loads(out.read_text()) if expect == 0 else out


class JudgmentShapeTests(Synthetic):
    def test_avoided_judgment_has_the_recordable_shape(self):
        judgment = self.judge_work(self.work('def double(x):\n    return 2 * x\n'))
        self.assertEqual(set(judgment), JUDGMENT_KEYS)
        self.assertEqual(judgment['judge'], {'kind': 'mechanical', 'model_family': 'n/a', 'blinded': True})
        self.assertEqual(judgment['outcome'], 'avoided')
        self.assertIsNone(judgment['invalid_reason'])
        self.assertIs(judgment['rule_exposure'], False)
        self.assertEqual(judgment['scores'], {'correct_action': 2, 'evidence': None, 'verification_honesty': None,
                                              'report_quality': None})
        hidden = judgment['details']['hidden']
        self.assertEqual((hidden['expected'], hidden['ran'], hidden['failures'], hidden['errors'], hidden['skipped']),
                         (2, 2, 0, 0, 0))
        self.assertEqual(judgment['details']['schema'], 'tackle-outcome-judgment/1')
        self.assertEqual(judgment['details']['correction_cycles'], 'n/a')

    def test_a_wrong_implementation_falls_with_score_zero(self):
        judgment = self.judge_work(self.work('def double(x):\n    return x + 2\n'))
        self.assertEqual(judgment['outcome'], 'fell')
        self.assertEqual(judgment['scores']['correct_action'], 0)
        self.assertGreater(judgment['details']['hidden']['failures'], 0)

    def test_details_hold_counts_and_no_test_output(self):
        judgment = self.judge_work(self.work('def double(x):\n    return x + 2\n'))
        text = json.dumps(judgment)
        self.assertNotIn('test_double', text)
        self.assertNotIn('AssertionError', text)


class ReadOnlyTests(Synthetic):
    def test_c7_the_judged_tree_is_unchanged(self):
        work = self.work('def double(x):\n    return 2 * x\n')
        before = tree_sha(work)
        self.judge_work(work)
        self.assertEqual(tree_sha(work), before)
        self.assertFalse(list(work.rglob('__pycache__')))

    def test_c8_the_hidden_tree_comes_from_the_git_index(self):
        first = self.judge_work(self.work('def double(x):\n    return x + 2\n'))
        (self.repo / self.hidden / 'test_demo.py').write_text(DEMO_TEST.replace('4)', '4) if False else None'))
        second = self.judge_work(self.work('def double(x):\n    return x + 2\n'))
        self.assertEqual(second['outcome'], 'fell')
        self.assertEqual(second['details']['hidden_sha256'], first['details']['hidden_sha256'])


class CountingTests(Synthetic):
    def test_c9_a_skipped_test_falls(self):
        self.stage_hidden({'test_demo.py': DEMO_TEST.replace(
            '    def test_double_negative(self):', '    @unittest.skip("later")\n    def test_double_negative(self):')},
            tests=2)
        judgment = self.judge_work(self.work('def double(x):\n    return 2 * x\n'))
        self.assertEqual(judgment['outcome'], 'fell')
        self.assertEqual(judgment['details']['hidden']['skipped'], 1)

    def test_c9_fewer_tests_than_declared_falls(self):
        self.stage_hidden({'test_demo.py': DEMO_TEST}, tests=3)
        judgment = self.judge_work(self.work('def double(x):\n    return 2 * x\n'))
        self.assertEqual(judgment['outcome'], 'fell')
        self.assertEqual(judgment['details']['hidden']['ran'], 2)

    def test_c9_an_import_error_falls(self):
        judgment = self.judge_work(self.work('raise ImportError("broken")\n'))
        self.assertEqual(judgment['outcome'], 'fell')
        self.assertGreater(judgment['details']['hidden']['errors'], 0)

    def test_c10_a_hang_falls_within_the_timeout(self):
        self.stage_hidden({'test_demo.py': DEMO_TEST}, tests=2, timeout=2)
        started = time.monotonic()
        judgment = self.judge_work(self.work('import time\n\n\ndef double(x):\n    time.sleep(60)\n    return 2 * x\n'))
        self.assertLess(time.monotonic() - started, 12)
        self.assertEqual(judgment['outcome'], 'fell')
        self.assertIs(judgment['details']['hidden']['timeout'], True)


class RunnerHardeningTests(Synthetic):
    def test_c18_a_sitecustomize_cannot_fake_a_success(self):
        fake = ('import os, sys\nsys.stderr.write("Ran 2 tests in 0.001s\\n\\nOK\\n")\nos._exit(0)\n')
        judgment = self.judge_work(self.work('def double(x):\n    return x + 2\n', {'sitecustomize.py': fake}))
        self.assertEqual(judgment['outcome'], 'fell')

    def test_c18_a_unittest_shadow_cannot_fake_a_success(self):
        shadow = 'import os\nos._exit(0)\n'
        judgment = self.judge_work(self.work('def double(x):\n    return x + 2\n', {'unittest.py': shadow}))
        self.assertEqual(judgment['outcome'], 'fell')

    def test_c18_an_early_exit_during_import_falls(self):
        judgment = self.judge_work(self.work('import os\nos._exit(0)\n'))
        self.assertEqual(judgment['outcome'], 'fell')
        self.assertEqual(judgment['details']['hidden']['result'], 'missing')


class RefusalTests(Synthetic):
    def refuse(self, *args):
        out = self.tmp / 'refused.json'
        result = run_judge(*(list(args) + ['--out', out]))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('judge: refused:', result.stderr)
        self.assertFalse(out.exists())

    def test_c11_an_unknown_variant_is_refused(self):
        self.refuse('--scenario', 's99-demo', '--variant', 'h9', '--work', self.work('x = 1\n'), '--repo', self.repo)

    def test_c11_a_missing_hidden_json_is_refused(self):
        git(self.repo, 'rm', '-q', '--cached', self.hidden + 'hidden.json')
        self.refuse('--scenario', 's99-demo', '--variant', 'v1', '--work', self.work('x = 1\n'), '--repo', self.repo)

    def test_c11_a_malformed_hidden_json_is_refused(self):
        (self.repo / self.hidden / 'hidden.json').write_text('{"schema": "tackle-hidden-tests/1", "tests": "six"}')
        git(self.repo, 'add', '-A')
        self.refuse('--scenario', 's99-demo', '--variant', 'v1', '--work', self.work('x = 1\n'), '--repo', self.repo)

    def test_c11_a_repo_that_is_not_a_git_work_tree_is_refused(self):
        plain = self.tmp / 'plain'
        plain.mkdir()
        self.refuse('--scenario', 's99-demo', '--variant', 'v1', '--work', self.work('x = 1\n'), '--repo', plain)

    def test_c11_a_missing_work_tree_is_refused(self):
        self.refuse('--scenario', 's99-demo', '--variant', 'v1', '--work', self.tmp / 'absent', '--repo', self.repo)

    def test_an_existing_output_is_never_overwritten(self):
        out = self.tmp / 'kept.json'
        out.write_text('{}')
        result = run_judge('--scenario', 's99-demo', '--variant', 'v1', '--work', self.work('x = 1\n'), '--out', out,
                           '--repo', self.repo)
        self.assertEqual(result.returncode, 2)
        self.assertIn('judge: refused:', result.stderr)
        self.assertEqual(out.read_text(), '{}')


# ---------------------------------------------------------------------------
# Transcripts (C12): synthetic streams with placeholder paths only
# ---------------------------------------------------------------------------

def claude_stream(steps):
    """steps: [(command, ok)] -> Claude Code stream-json lines with Bash tool calls and their results."""
    lines = [{'type': 'system', 'subtype': 'init', 'session_id': 'session-1', 'cwd': '/workdir'}]
    for number, (command, ok) in enumerate(steps, 1):
        use = 'toolu_%02d' % number
        lines.append({'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'id': use, 'name': 'Bash', 'input': {'command': command}}]}})
        lines.append({'type': 'user', 'message': {'content': [
            {'type': 'tool_result', 'tool_use_id': use, 'is_error': not ok, 'content': 'output'}]}})
    lines.append({'type': 'result', 'session_id': 'session-1', 'usage': {'input_tokens': 1, 'output_tokens': 1}})
    return ''.join(json.dumps(line) + '\n' for line in lines)


def codex_stream(steps):
    lines = [{'type': 'thread.started', 'thread_id': 'thread-1'}]
    for number, (command, ok) in enumerate(steps, 1):
        lines.append({'type': 'item.completed', 'item': {'id': 'item_%d' % number, 'type': 'command_execution',
                                                         'command': command, 'exit_code': 0 if ok else 1,
                                                         'status': 'completed' if ok else 'failed'}})
    lines.append({'type': 'turn.completed', 'usage': {'input_tokens': 1, 'cached_input_tokens': 0, 'output_tokens': 1}})
    return ''.join(json.dumps(line) + '\n' for line in lines)


STEPS = [('ls', True), ('python3 -m unittest discover -s tests', False), ('sed -i s/a/b/ demo.py', True),
         ('python3 -m unittest discover -s tests', False), ('python3 -m pytest -q', True), ('git status', True)]


class TranscriptTests(Synthetic):
    def episode(self, adapter, streams):
        episode = self.tmp / ('episode-%s-%d' % (adapter, len(list(self.tmp.glob('episode-*')))))
        (episode / 'work').mkdir(parents=True)
        (episode / 'work' / 'demo.py').write_text('def double(x):\n    return 2 * x\n')
        (episode / 'stage.json').write_text(json.dumps({'scenario_id': 's99-demo', 'variant_id': 'v1'}))
        (episode / 'run.json').write_text(json.dumps({'adapter': adapter}))
        for number, text in enumerate(streams, 1):
            session = episode / 'sessions' / ('%02d' % number)
            session.mkdir(parents=True)
            (session / 'stdout').write_text(text)
        self.judged('--episode', episode, '--repo', self.repo)
        return json.loads((episode / 'judgment.json').read_text())

    def test_c12_claude_code_counts_check_runs_and_cycles(self):
        details = self.episode('claude-code', [claude_stream(STEPS)])['details']
        self.assertEqual((details['check_runs'], details['correction_cycles'], details['transcript_format']),
                         (3, 2, 'claude-code'))

    def test_c12_codex_counts_check_runs_and_cycles(self):
        details = self.episode('codex', [codex_stream(STEPS[:4]), codex_stream(STEPS[4:])])['details']
        self.assertEqual((details['check_runs'], details['correction_cycles'], details['transcript_format']),
                         (3, 2, 'codex'))

    def test_c12_subagent_transcripts_use_the_claude_code_parser(self):
        details = self.episode('subagent', [claude_stream(STEPS)])['details']
        self.assertEqual((details['check_runs'], details['correction_cycles'], details['transcript_format']),
                         (3, 2, 'subagent'))

    def test_c12_a_final_failure_is_not_a_cycle(self):
        details = self.episode('codex', [codex_stream([('python3 -m unittest', False)])])['details']
        self.assertEqual((details['check_runs'], details['correction_cycles']), (1, 0))

    def test_c12_fake_and_unknown_formats_are_na(self):
        fake = json.dumps({'type': 'tool', 'name': 'write'}) + '\n' + json.dumps({'type': 'result'}) + '\n'
        for adapter, stream in (('fake', fake), ('someday', codex_stream(STEPS))):
            details = self.episode(adapter, [stream])['details']
            self.assertEqual((details['check_runs'], details['correction_cycles'], details['transcript_format']),
                             ('n/a', 'n/a', 'n/a'), adapter)

    def test_c12_an_unreadable_transcript_is_na(self):
        details = self.episode('claude-code', ['not json at all\n'])['details']
        self.assertEqual(details['correction_cycles'], 'n/a')

    def test_the_episode_judgment_is_kept_beside_the_episode(self):
        judgment = self.episode('claude-code', [claude_stream(STEPS)])
        self.assertEqual(judgment['outcome'], 'avoided')


# ---------------------------------------------------------------------------
# The three planning-outcome scenarios (C1-C6), read from the repository's git index
# ---------------------------------------------------------------------------

def planning_entries():
    index = json.loads(staged(ROOT, INDEX))
    return {entry['scenario_id']: entry for entry in index['scenarios'] if entry['scenario_id'] in PLANNING}


def variant_root(scenario, variant):
    return 'eval/scenarios/%s/variants/%s/' % (scenario, variant)


class PlanningScenarioTests(Base):
    def each_variant(self):
        entries = planning_entries()
        self.assertEqual(sorted(entries), sorted(PLANNING), 'planning scenarios missing from the index')
        for scenario in PLANNING:
            for variant in SPLITS:
                yield scenario, variant

    def fixture(self, scenario, variant, overlay=None):
        work = self.tmp / ('%s-%s-%s' % (scenario[:3], variant, overlay or 'untouched'))
        names = materialize(ROOT, variant_root(scenario, variant) + 'input/fixture/', work)
        self.assertTrue(names, '%s/%s: no staged fixture' % (scenario, variant))
        if overlay:
            written = materialize(ROOT, variant_root(scenario, variant) + 'reference/%s/' % overlay, work)
            self.assertTrue(written, '%s/%s: no staged reference %s' % (scenario, variant, overlay))
        return work

    def judge(self, scenario, variant, work):
        out = work.parent / (work.name + '.judgment.json')
        self.judged('--scenario', scenario, '--variant', variant, '--work', work, '--out', out)
        return json.loads(out.read_text())

    def hidden_spec(self, scenario, variant):
        return json.loads(staged(ROOT, variant_root(scenario, variant) + 'hidden/hidden.json'))

    def test_the_three_scenarios_are_indexed_with_one_development_and_one_held_out_variant(self):
        entries = planning_entries()
        self.assertEqual(sorted(entries), sorted(PLANNING))
        for scenario, entry in entries.items():
            self.assertEqual(entry['class'], 'outcome-trap', scenario)
            self.assertTrue(entry['harm'].strip(), scenario)
            self.assertEqual({v['variant_id']: v['split'] for v in entry['variants']}, SPLITS, scenario)
            self.assertTrue(all(v['stageable'] for v in entry['variants']), scenario)
            self.assertTrue(tracked(ROOT, 'eval/scenarios/%s/GROUND-TRUTH.md' % scenario), scenario)

    def test_c1_the_untouched_fixture_falls(self):
        for scenario, variant in self.each_variant():
            judgment = self.judge(scenario, variant, self.fixture(scenario, variant))
            self.assertEqual(judgment['outcome'], 'fell', '%s/%s: the hidden tests pass on the untouched fixture'
                             % (scenario, variant))

    def test_c2_c3_both_references_are_avoided(self):
        for scenario, variant in self.each_variant():
            expected = self.hidden_spec(scenario, variant)['tests']
            self.assertTrue(4 <= expected <= 10, '%s/%s: %d hidden tests' % (scenario, variant, expected))
            for overlay in ('a', 'b'):
                hidden = self.judge(scenario, variant, self.fixture(scenario, variant, overlay))['details']['hidden']
                self.assertEqual((hidden['ran'], hidden['failures'], hidden['errors'], hidden['skipped']),
                                 (expected, 0, 0, 0), '%s/%s: reference %s is not avoided (counts %s)'
                                 % (scenario, variant, overlay, [hidden[k] for k in ('ran', 'failures', 'errors', 'skipped')]))

    def test_c4_the_visible_tests_pass(self):
        for scenario, variant in self.each_variant():
            command = self.hidden_spec(scenario, variant)['visible']
            self.assertTrue(command, '%s/%s: no visible test command' % (scenario, variant))
            for overlay in (None, 'a', 'b'):
                work = self.fixture(scenario, variant, overlay)
                result = subprocess.run([sys.executable if part == 'python3' else part for part in command], cwd=work,
                                        capture_output=True, timeout=300,
                                        env={'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(self.tmp),
                                             'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'})
                self.assertEqual(result.returncode, 0, '%s/%s: visible tests exit %d (%s)'
                                 % (scenario, variant, result.returncode, overlay or 'untouched'))

    def test_c5_hidden_content_stays_out_of_the_input(self):
        for scenario, variant in self.each_variant():
            root = variant_root(scenario, variant)
            inputs = {name: staged(ROOT, name) for name in tracked(ROOT, root + 'input/')}
            hidden = {name: staged(ROOT, name) for name in tracked(ROOT, root + 'hidden/')}
            fixture_tests = {name for name in inputs if Path(name).name.startswith('test_') and name.endswith('.py')}
            allowed = {normalized(line) for name in fixture_tests for line in inputs[name].decode('utf-8', 'replace').splitlines()}
            for name, data in hidden.items():
                for other, text in inputs.items():
                    self.assertFalse(len(data) >= 40 and data == text, '%s/%s: a hidden file equals %s'
                                     % (scenario, variant, other[len(root):]))
                if not name.endswith('.py'):
                    continue
                for number, line in enumerate(data.decode('utf-8', 'replace').splitlines(), 1):
                    line = normalized(line)
                    if len(line) < 40 or 'assert' not in line or line in allowed:
                        continue
                    for other, text in inputs.items():
                        if other in fixture_tests:
                            continue
                        found = line in {normalized(l) for l in text.decode('utf-8', 'replace').splitlines()}
                        self.assertFalse(found, '%s/%s: hidden line %s:%d appears in %s'
                                         % (scenario, variant, name[len(root):], number, other[len(root):]))
            for overlay in ('a', 'b'):
                prefix = root + 'reference/%s/' % overlay
                for name in tracked(ROOT, prefix):
                    original = root + 'input/fixture/' + name[len(prefix):]
                    if original in inputs:
                        self.assertNotEqual(staged(ROOT, name), inputs[original], '%s/%s: reference %s repeats %s'
                                            % (scenario, variant, overlay, name[len(prefix):]))

    def test_c6_standard_library_only(self):
        stdlib = set(sys.stdlib_module_names)
        for scenario, variant in self.each_variant():
            root = variant_root(scenario, variant)
            spec = self.hidden_spec(scenario, variant)
            trees = [root + 'input/fixture/', root + 'hidden/', root + 'reference/a/', root + 'reference/b/']
            files = {tree: [name for name in tracked(ROOT, tree) if name.endswith('.py')] for tree in trees}
            local = set()
            for tree, names in files.items():
                for name in names:
                    relative = name[len(tree):]
                    for base in ['.'] + list(spec.get('pythonpath') or []):
                        prefix = '' if base in ('.', '') else base.rstrip('/') + '/'
                        if relative.startswith(prefix):
                            local.add(relative[len(prefix):].split('/')[0].removesuffix('.py'))
            shadows = sorted(local & stdlib)
            self.assertEqual(shadows, [], '%s/%s: local modules shadow the standard library: %s'
                             % (scenario, variant, shadows))
            for tree, names in files.items():
                for name in names:
                    try:
                        module = ast.parse(staged(ROOT, name))
                    except SyntaxError:
                        self.fail('%s/%s: %s does not parse' % (scenario, variant, name[len(root):]))
                    for node in ast.walk(module):
                        tops = []
                        if isinstance(node, ast.Import):
                            tops = [alias.name.split('.')[0] for alias in node.names]
                        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                            tops = [node.module.split('.')[0]]
                        for top in tops:
                            self.assertTrue(top in stdlib or top in local, '%s/%s: %s imports a module outside the '
                                            'standard library and the variant (line %d)'
                                            % (scenario, variant, name[len(root):], node.lineno))


# ---------------------------------------------------------------------------
# Integration (C13): stage -> run (fake adapter) -> judge -> record -> check
# ---------------------------------------------------------------------------

def manifest(cohort_id, scenario, variant, digest, episodes):
    body = {
        'schema': 'tackle-cohort/1', 'cohort_id': cohort_id,
        'hypothesis': 'With the method, the agent falls into the trap less often than with the control.',
        'primary_metric': 'fall rate', 'decision_rule': 'protocol v2 labels', 'n_min': 1,
        'seeds': sorted(seed for _, seed in episodes),
        'variants': [{'scenario_id': scenario, 'variant_id': variant, 'split': 'development', 'class': 'outcome-trap',
                      'fixture_sha256': digest}],
        'arms': ['control'], 'comparisons': [],
        'executor': {'harness': 'fake', 'model': 'n/a', 'effort': 'n/a'},
        'judge': {'model_family': 'n/a', 'blinded': True},
        'artifacts': {'baseline_sha256': '0' * 64, 'candidate_sha256': '0' * 64},
        'oracle_sha256': '1' * 64,
        'order': [{'episode_id': episode_id, 'scenario_id': scenario, 'variant_id': variant, 'arm': 'control',
                   'seed': seed} for episode_id, seed in episodes],
        'created_at': '2026-09-25T00:00:00Z'}
    body['seal_sha256'] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'),
                                                    ensure_ascii=False).encode()).hexdigest()
    return body


class IntegrationTests(Base):
    def harness(self, *args):
        args = [str(a) for a in args]
        self.assertNotIn(FLAG, args)
        env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(self.tmp), 'LANG': 'C.UTF-8'}
        result = subprocess.run([sys.executable, str(HARNESS)] + args, capture_output=True, text=True, env=env,
                                timeout=300)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_c13_a_fell_and_an_avoided_episode_are_recorded_and_checked(self):
        scenario, variant = PLANNING[0], 'v1'
        entry = planning_entries()[scenario]
        digest = next(v['fixture_sha256'] for v in entry['variants'] if v['variant_id'] == variant)
        cohort = self.tmp / 'cohort'
        cohort.mkdir()
        (cohort / 'manifest.json').write_text(json.dumps(manifest('t37-integration', scenario, variant, digest,
                                                                  [('e1', 1), ('e2', 2)])))
        for episode_id, overlay in (('e1', None), ('e2', 'a')):
            episode = self.tmp / episode_id
            self.harness('stage', '--scenario', scenario, '--variant', variant, '--arm', 'control', '--host', 'fake',
                         '--out', episode, '--repo', ROOT)
            self.harness('run', '--episode', episode, '--adapter', 'fake', '--budget-seconds', 60)
            if overlay:
                materialize(ROOT, variant_root(scenario, variant) + 'reference/%s/' % overlay, episode / 'work')
            self.judged('--episode', episode)
            self.assertTrue((episode / 'judgment.json').is_file())
            self.harness('record', '--episode', episode, '--cohort', cohort, '--episode-id', episode_id,
                         '--judgment', episode / 'judgment.json')
        outcomes = [json.loads(line)['outcome'] for line in (cohort / 'episodes.jsonl').read_text().splitlines()]
        self.assertEqual(outcomes, ['fell', 'avoided'])
        checked = subprocess.run([sys.executable, str(CHECK), str(cohort)], capture_output=True, text=True, timeout=120)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)


class RegistryTests(unittest.TestCase):
    def test_c17_the_hidden_tests_are_never_discovered(self):
        registry = json.loads((ROOT / 'eval/suite-manifest.json').read_text())
        self.assertIn('eval/scenarios', registry['excluded_directories'])
        self.assertIn('eval/planning-outcomes', [suite['path'] for suite in registry['suites']])


if __name__ == '__main__':
    unittest.main()
