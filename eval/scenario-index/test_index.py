"""The scenario index classifies every scenario and seals its held-out variants before any cohort uses them.

``check_index.py`` is driven by subprocess over git repositories built here in temporary directories, the
way CI runs it on this repository. Nothing is written inside this repository.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / 'eval/scenario-index/check_index.py'
GAPS = ('invocation-help-aliases', 'sizing', 'correction-budget-stop', 'resume-across-sessions',
        'communication-policy', 'coordinated-independence')
GIT_ENV = {'GIT_AUTHOR_NAME': 'fixture', 'GIT_AUTHOR_EMAIL': 'fixture@invalid', 'GIT_COMMITTER_NAME': 'fixture',
           'GIT_COMMITTER_EMAIL': 'fixture@invalid', 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}
VECTOR = '1bda081eba31926b2292c94f4827339be927655103610bd8f1c7623091ab02aa'


def digest(files):
    """C06 over a {relative path: bytes} mapping."""
    mapping = {path: hashlib.sha256(data).hexdigest() for path, data in files.items()}
    return hashlib.sha256(json.dumps(mapping, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


class Repo:
    """Eight outcome traps with two held-out variants each, one procedure, one tripwire, one retired scenario."""

    def __init__(self, case, traps=8):
        self.temporary = tempfile.TemporaryDirectory(prefix='tackle-index-')
        case.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'repo'
        self.root.mkdir()
        self.git('init', '-q')
        self.files = {}
        self.rules = []
        self.entries = []
        for n in range(1, traps + 1):
            self.trap('s%d-trap' % n, covers=[GAPS[n - 1]] if n <= len(GAPS) else [])
        self.plain('s20-proc', 'procedure')
        self.plain('s21-wire', 'tripwire')
        self.plain('s22-gone', 'retired', stageable=False)
        self.write_all()
        self.commit('index')

    def rule(self, scenario, fragment):
        self.rules.append(dict(rule_id='R-RUN-%02d' % (len(self.rules) + 1), statement='Rule for %s: %s.' % (scenario, fragment),
                               home_fragment=fragment, evidence=dict(status='untested', scenarios=[scenario])))

    def legacy(self, scenario, prompt='Fix the report.\n', world=None):
        base = 'eval/scenarios/%s' % scenario
        self.files[base + '/GROUND-TRUTH.md'] = 'answer sheet of %s\n' % scenario
        self.files[base + '/README.md'] = 'about %s\n' % scenario
        self.files[base + '/task.md'] = prompt
        for name, text in (world or {'notes.md': 'a world for %s\n' % scenario}).items():
            self.files[base + '/fixture/' + name] = text
        return self.variant(base, 'v0', 'development')

    def new(self, scenario, variant, split, prompt='Tidy the notes.\n', world=None):
        base = 'eval/scenarios/%s/variants/%s' % (scenario, variant)
        self.files[base + '/GROUND-TRUTH.md'] = 'answer sheet of %s/%s\n' % (scenario, variant)
        self.files[base + '/input/task.md'] = prompt
        for name, text in (world or {'notes.md': 'another world %s\n' % variant}).items():
            self.files[base + '/input/fixture/' + name] = text
        return self.variant(base + '/input', variant, split)

    def variant(self, path, variant, split):
        return dict(variant_id=variant, split=split, path=path, prompts=['task.md'], fixture='fixture', stageable=True,
                    fixture_sha256=None, control_exposure=dict(install=False, fragments=[]))

    def trap(self, scenario, covers=()):
        self.rule(scenario, 'never flip %s early' % scenario)
        variants = [self.legacy(scenario), self.new(scenario, 'h1', 'held-out'), self.new(scenario, 'h2', 'held-out')]
        self.entries.append(dict(scenario_id=scenario, **{'class': 'outcome-trap'}, harm='the wrong action loses data',
                                 covers=list(covers), authored=dict(actors=['fixture'], blind=True), variants=variants))

    def plain(self, scenario, kind, stageable=True):
        if kind != 'retired':
            self.rule(scenario, 'keep %s tidy' % scenario)
        if stageable:
            variants = [self.legacy(scenario)]
        else:
            self.files['eval/scenarios/%s/GROUND-TRUTH.md' % scenario] = 'answer sheet\n'
            variants = [dict(variant_id='v0', split='development', path='eval/scenarios/%s' % scenario, prompts=[],
                             fixture=None, stageable=False, fixture_sha256=None,
                             control_exposure=dict(install=False, fragments=[]))]
        self.entries.append(dict(scenario_id=scenario, **{'class': kind}, harm='', covers=[],
                                 authored=dict(actors=['fixture'], blind=True), variants=variants))

    def entry(self, scenario):
        return next(e for e in self.entries if e['scenario_id'] == scenario)

    def input_files(self, variant):
        prefix = variant['path'] + '/'
        chosen = {}
        for path, text in self.files.items():
            if not path.startswith(prefix):
                continue
            relative = path[len(prefix):]
            if relative in variant['prompts'] or (variant['fixture'] and relative.startswith(variant['fixture'] + '/')):
                chosen[relative] = text.encode()
        return chosen

    def seal(self):
        for entry in self.entries:
            for variant in entry['variants']:
                variant['fixture_sha256'] = digest(self.input_files(variant)) if variant['stageable'] else None

    def write_all(self, seal=True):
        if seal:
            self.seal()
        self.files['eval/rules/ledger.json'] = json.dumps(dict(schema='tackle-rule-ledger/1', rules=self.rules, non_normative=[]))
        self.files['eval/scenarios/INDEX.json'] = json.dumps(dict(schema='tackle-scenario-index/1', scenarios=self.entries), indent=1)
        for path, text in self.files.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root)] + list(args), capture_output=True, text=True,
                              env=dict(os.environ, **GIT_ENV), check=True)

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-q', '--allow-empty', '-m', message)

    def cohort(self, lines):
        """A cohort manifest listing s1-trap/h1 with the given episode lines (scenario, variant)."""
        h1 = next(v for v in self.entry('s1-trap')['variants'] if v['variant_id'] == 'h1')
        manifest = dict(cohort_id='c1', variants=[dict(scenario_id='s1-trap', variant_id='h1', split='held-out',
                                                       **{'class': 'outcome-trap'}, fixture_sha256=h1['fixture_sha256'])])
        base = self.root / 'eval/cohorts/c1'
        base.mkdir(parents=True, exist_ok=True)
        (base / 'manifest.json').write_text(json.dumps(manifest))
        with open(base / 'episodes.jsonl', 'a') as handle:
            for scenario, variant in lines:
                handle.write(json.dumps(dict(scenario_id=scenario, variant_id=variant, episode_id='e')) + '\n')

    def tree(self):
        return {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(self.root.rglob('*')) if p.is_file() and '.git' not in p.relative_to(self.root).parts}


def check(root, stage=True):
    """Stage the working tree the way an author would (git add -A), then run the checker on the index."""
    if stage:
        subprocess.run(['git', '-C', str(root), 'add', '-A'], capture_output=True, env=dict(os.environ, **GIT_ENV), check=True)
    child = subprocess.run([sys.executable, str(CHECKER), '--repo', str(root)], capture_output=True, text=True, timeout=120)
    return child.returncode, child.stdout, child.stderr


SUMMARY = 'scenarios=11 outcome_traps=8 held_out=16 stageable=26 exposed=0 gaps=6/6'


class IndexTests(unittest.TestCase):
    def assertValid(self, repo, expected=SUMMARY):
        code, out, err = check(repo.root)
        self.assertEqual((code, err), (0, ''), out)
        self.assertEqual(out.splitlines(), [expected])

    def assertRejected(self, repo, *fragments, stage=True):
        code, out, err = check(repo.root, stage)
        self.assertEqual(code, 1, out + err)
        self.assertNotIn('Traceback', err)
        errors = [line for line in out.splitlines() if line.startswith('error: ')]
        self.assertTrue(errors, out)
        for fragment in fragments:
            self.assertTrue(any(fragment in line for line in errors), (fragment, errors))

    def test_valid_index_passes(self):
        self.assertValid(Repo(self))

    def test_scenario_without_entry_fails(self):
        repo = Repo(self)
        repo.files['eval/scenarios/s30-new/GROUND-TRUTH.md'] = 'answer\n'
        repo.write_all()
        self.assertRejected(repo, 's30-new: completeness:')

    def test_entry_without_directory_fails(self):
        repo = Repo(self)
        repo.entries.append(dict(repo.entry('s20-proc'), scenario_id='s31-ghost'))
        repo.write_all(seal=False)
        self.assertRejected(repo, 's31-ghost: completeness:')

    def test_unknown_class_and_bad_variant_ids_fail(self):
        repo = Repo(self)
        repo.entry('s20-proc')['class'] = 'smoke'
        repo.entry('s21-wire')['variants'][0]['variant_id'] = 'h9'
        repo.write_all()
        self.assertRejected(repo, 's20-proc: vocabulary:', 's21-wire/h9: vocabulary:')

    def test_outcome_trap_without_harm_fails(self):
        repo = Repo(self)
        repo.entry('s3-trap')['harm'] = ''
        repo.write_all()
        self.assertRejected(repo, 's3-trap: harm:')

    def test_digest_drift_fails(self):
        repo = Repo(self)
        path = 'eval/scenarios/s2-trap/variants/h2/input/fixture/notes.md'
        (repo.root / path).write_text(repo.files[path] + 'x')
        self.assertRejected(repo, 's2-trap/h2: digest:')

    def test_extra_file_in_a_new_input_root_fails(self):
        repo = Repo(self)
        (repo.root / 'eval/scenarios/s2-trap/variants/h1/input/extra.md').write_text('stray\n')
        self.assertRejected(repo, 's2-trap/h1: digest:')

    def test_legacy_input_ignores_the_scenario_readme(self):
        repo = Repo(self)
        (repo.root / 'eval/scenarios/s1-trap/README.md').write_text('rewritten readme\n')
        self.assertValid(repo)

    def test_own_answer_sheet_in_the_input_fails(self):
        for where in ('eval/scenarios/s4-trap/fixture/copy.md', 'eval/scenarios/s4-trap/variants/h1/input/fixture/sheet.md'):
            with self.subTest(where=where):
                repo = Repo(self)
                source = 'eval/scenarios/s4-trap/GROUND-TRUTH.md' if '/variants/' not in where else \
                    'eval/scenarios/s4-trap/variants/h1/GROUND-TRUTH.md'
                repo.files[where] = repo.files[source]
                repo.write_all()
                self.assertRejected(repo, 'answer-sheet:')

    def test_nested_world_answer_sheet_is_fixture_content(self):
        repo = Repo(self)
        repo.files['eval/scenarios/s5-trap/fixture/suite/t1/GROUND-TRUTH.md'] = 'an answer sheet inside the world\n'
        repo.write_all()
        self.assertValid(repo)

    def test_file_hidden_by_the_world_gitignore_fails_until_force_added(self):
        repo = Repo(self)
        repo.files['eval/scenarios/s5-trap/fixture/.gitignore'] = 'notes/\n'
        repo.files['eval/scenarios/s5-trap/fixture/notes/state.md'] = 'the plan state the trap needs\n'
        repo.write_all()
        self.assertRejected(repo, 's5-trap/v0: untracked:')
        repo.git('add', '-f', 'eval/scenarios/s5-trap/fixture/notes/state.md')
        self.assertValid(repo)

    def test_runtime_caches_in_a_fixture_are_ignored(self):
        repo = Repo(self)
        (repo.root / '.gitignore').write_text('__pycache__/\n*.pyc\n')
        cache = repo.root / 'eval/scenarios/s6-trap/fixture/__pycache__'
        cache.mkdir(parents=True)
        (cache / 'tool.cpython-310.pyc').write_bytes(b'cache')
        self.assertValid(repo)

    def test_staged_bytes_are_checked_not_the_working_tree(self):
        repo = Repo(self)
        path = 'eval/scenarios/s2-trap/variants/h1/input/fixture/notes.md'
        good = (repo.root / path).read_text()
        (repo.root / path).write_text(good + 'drift\n')
        repo.git('add', path)
        (repo.root / path).write_text(good)
        self.assertRejected(repo, 's2-trap/h1: digest:', stage=False)

    def test_symlink_in_an_input_fails(self):
        repo = Repo(self)
        link = repo.root / 'eval/scenarios/s6-trap/variants/h1/input/fixture/link.md'
        link.symlink_to(repo.root / 'eval/scenarios/s6-trap/GROUND-TRUTH.md')
        self.assertRejected(repo, 's6-trap/h1: symlink:')

    def test_unrecorded_exposure_fails(self):
        repo = Repo(self)
        repo.files['eval/scenarios/s7-trap/fixture/guide.md'] = 'Remember: NEVER   flip s7-trap early.\n'
        repo.write_all()
        self.assertRejected(repo, 's7-trap/v0: exposure:')

    def test_recorded_exposure_needs_a_clean_development_variant(self):
        repo = Repo(self)
        repo.files['eval/scenarios/s7-trap/fixture/guide.md'] = 'never flip s7-trap early\n'
        v0 = repo.entry('s7-trap')['variants'][0]
        v0['control_exposure'] = dict(install=False, fragments=['never flip s7-trap early'])
        repo.write_all()
        self.assertRejected(repo, 's7-trap: exposure:')
        repo.entry('s7-trap')['variants'].append(repo.new('s7-trap', 'v1', 'development'))
        repo.write_all()
        self.assertValid(repo, SUMMARY.replace('stageable=26', 'stageable=27').replace('exposed=0', 'exposed=1'))

    def test_outcome_trap_without_held_out_needs_no_runnable_variant(self):
        repo = Repo(self)
        repo.files['eval/scenarios/s23-extra/GROUND-TRUTH.md'] = 'answer sheet\n'
        repo.entries.append(dict(scenario_id='s23-extra', **{'class': 'outcome-trap'}, harm='the wrong action loses data',
                                 covers=[], authored=dict(actors=['fixture'], blind=True),
                                 variants=[dict(variant_id='v0', split='development', path='eval/scenarios/s23-extra',
                                                prompts=[], fixture=None, stageable=False, fixture_sha256=None,
                                                control_exposure=dict(install=False, fragments=[]))]))
        repo.write_all()
        self.assertValid(repo, SUMMARY.replace('scenarios=11 outcome_traps=8', 'scenarios=12 outcome_traps=9'))

    def test_shipped_install_is_exposure(self):
        repo = Repo(self)
        repo.files['eval/scenarios/s21-wire/fixture/SKILL.md'] = '---\nname: Tackle\n---\nbody\n'
        repo.write_all()
        self.assertRejected(repo, 's21-wire/v0: exposure:')
        repo.entry('s21-wire')['variants'][0]['control_exposure'] = dict(install=True, fragments=[])
        repo.write_all()
        self.assertValid(repo, SUMMARY.replace('exposed=0', 'exposed=1'))

    def test_exposed_held_out_variant_fails(self):
        repo = Repo(self)
        repo.files['eval/scenarios/s8-trap/variants/h2/input/fixture/guide.md'] = 'never flip s8-trap early\n'
        variant = repo.entry('s8-trap')['variants'][2]
        variant['control_exposure'] = dict(install=False, fragments=['never flip s8-trap early'])
        repo.write_all()
        self.assertRejected(repo, 's8-trap/h2: exposure:')

    def test_exposed_new_development_variant_fails(self):
        repo = Repo(self)
        variant = repo.new('s3-trap', 'v1', 'development', world={'guide.md': 'never flip s3-trap early\n'})
        variant['control_exposure'] = dict(install=False, fragments=['never flip s3-trap early'])
        repo.entry('s3-trap')['variants'].append(variant)
        repo.write_all()
        self.assertRejected(repo, 's3-trap/v1: exposure:')

    def test_leading_prompt_fails(self):
        repo = Repo(self)
        repo.files['eval/scenarios/s1-trap/variants/h1/input/task.md'] = 'Should you never flip s1-trap early?\n'
        repo.write_all()
        self.assertRejected(repo, 's1-trap/h1: prompt:')

    def test_held_out_count_is_bounded(self):
        for traps, fragment in ((7, 'count:'), (11, 'count:')):
            with self.subTest(traps=traps):
                self.assertRejected(Repo(self, traps=traps), fragment)

    def test_missing_gap_fails(self):
        repo = Repo(self)
        repo.entry('s6-trap')['covers'] = []
        repo.write_all()
        self.assertRejected(repo, 'coverage:')

    def test_seal_order_single_commit(self):
        repo = Repo(self)
        repo.cohort([('s1-trap', 'h1')])
        repo.commit('cohort with the seal commit')
        self.assertValid(repo)
        early = Repo(self)
        early.git('checkout', '-q', '--orphan', 'other')
        early.git('rm', '-rq', '--cached', '.')
        early.cohort([('s1-trap', 'h1')])
        early.git('add', 'eval/cohorts')
        early.git('commit', '-q', '-m', 'episode first')
        early.commit('index after the episode')
        self.assertRejected(early, 's1-trap/h1: seal:')

    def test_seal_order_over_several_commits(self):
        repo = Repo(self)
        repo.git('checkout', '-q', '--orphan', 'other')
        repo.git('rm', '-rq', '--cached', '.')
        repo.cohort([('s2-trap', 'h1')])
        repo.git('add', 'eval/cohorts')
        repo.git('commit', '-q', '-m', 'an unrelated episode before the index')
        repo.commit('the index')
        repo.cohort([('s1-trap', 'h1')])
        repo.commit('the sealed episode')
        self.assertValid(repo)
        early = Repo(self)
        early.git('checkout', '-q', '--orphan', 'other')
        early.git('rm', '-rq', '--cached', '.')
        early.cohort([('s1-trap', 'h1')])
        early.git('add', 'eval/cohorts')
        early.git('commit', '-q', '-m', 'the violating episode')
        early.commit('the index')
        early.cohort([('s2-trap', 'h1')])
        early.commit('a later valid episode')
        self.assertRejected(early, 's1-trap/h1: seal:')

    def test_seal_in_the_same_commit_as_the_first_record_fails(self):
        repo = Repo(self)
        repo.git('checkout', '-q', '--orphan', 'other')
        repo.cohort([('s1-trap', 'h1')])
        repo.commit('index and episode together')
        self.assertRejected(repo, 's1-trap/h1: seal:')

    def test_cohort_digest_must_match_the_index(self):
        repo = Repo(self)
        repo.cohort([])
        manifest = repo.root / 'eval/cohorts/c1/manifest.json'
        data = json.loads(manifest.read_text())
        data['variants'][0]['fixture_sha256'] = '0' * 64
        manifest.write_text(json.dumps(data))
        repo.commit('cohort with a stale digest')
        self.assertRejected(repo, 's1-trap/h1: seal:')

    def test_reordered_index_gives_the_same_result(self):
        repo = Repo(self)
        first = check(repo.root)
        self.assertEqual(first[0], 0, first)
        repo.entries.reverse()
        for entry in repo.entries:
            entry['variants'].reverse()
        repo.write_all()
        self.assertEqual(check(repo.root), first)

    def test_digest_tool_matches_the_contract_vector(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'b').mkdir()
            (Path(tmp) / 'a.txt').write_text('a\n')
            (Path(tmp) / 'b' / 'c.txt').write_text('c\n')
            child = subprocess.run([sys.executable, str(CHECKER), '--digest', tmp], capture_output=True, text=True)
            self.assertEqual((child.returncode, child.stdout.strip()), (0, VECTOR))

    def test_checker_never_writes(self):
        repo = Repo(self)
        before = repo.tree()
        self.assertEqual(check(repo.root)[0], 0)
        self.assertEqual(repo.tree(), before)

    def test_usage_errors_exit_2(self):
        repo = Repo(self)
        with tempfile.TemporaryDirectory() as plain:
            for argv in ([], ['--repo'], ['--repo', plain], ['--repo', str(repo.root), 'extra'], ['--digest']):
                with self.subTest(argv=argv):
                    child = subprocess.run([sys.executable, str(CHECKER)] + argv, capture_output=True, text=True)
                    self.assertEqual(child.returncode, 2, child.stdout + child.stderr)
                    self.assertIn('usage: check_index.py', child.stderr)


class RepositoryTests(unittest.TestCase):
    def test_repository_index_is_current(self):
        code, out, err = check(ROOT, stage=False)  # read the index as it is; never stage the real repository
        self.assertEqual((code, err), (0, ''), out)
        self.assertRegex(out, r'^scenarios=\d+ outcome_traps=\d+ held_out=\d+ stageable=\d+ exposed=\d+ gaps=6/6\n$')


if __name__ == '__main__':
    unittest.main()
