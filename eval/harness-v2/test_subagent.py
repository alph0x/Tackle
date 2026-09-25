"""End-to-end checks of the subagent-episode tool: prompt, finish, its run.json/audit.json schema, and
its compatibility with harness.py record and judge.py --episode.

No test reads eval/scenarios/: the record/judge integration tests build their own synthetic repository
with a staged hidden/hidden.json, exactly like judge.py's own contract expects. No test starts a real
model; "transcripts" are synthetic JSONL fixtures in the same event shape usage.claude_code_transcript
reads. Outside-path literals are /etc or /opt paths, never a real home path (eval/suite-integrity/
test_credential_guard.py rejects those in tracked eval/ files).
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SUBAGENT = HERE / 'subagent.py'
HARNESS = HERE / 'harness.py'
JUDGE = ROOT / 'eval' / 'planning-outcomes' / 'judge.py'
CHECK = ROOT / 'eval' / 'protocol-v2' / 'check.py'
sys.path.insert(0, str(HERE))
import subagent  # noqa: E402
import usage  # noqa: E402
# Only plain functions/classes, never a TestCase subclass: importing one would make unittest discover
# count and run it a second time under this module too, breaking the suite registry's exact test count.
from test_harness import Repo, manifest, digest_files  # noqa: E402


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())


def load(path):
    return json.loads(Path(path).read_text())


def add_hidden(repo, scenario, variant, tests=1, timeout_seconds=10, pythonpath=None, body=None):
    """Stage eval/scenarios/<scenario>/variants/<variant>/hidden/ in the synthetic repo's git index (via
    Repo.seal's later `git add -A`), exactly as judge.py's hidden_files() expects."""
    base = repo.root / 'eval' / 'scenarios' / scenario / 'variants' / variant / 'hidden'
    write(base / 'hidden.json', json.dumps({'schema': 'tackle-hidden-tests/1', 'tests': tests,
                                            'timeout_seconds': timeout_seconds, 'pythonpath': pythonpath or []}))
    write(base / 'test_hidden.py', body or (
        "import unittest\n\n"
        "class Test(unittest.TestCase):\n"
        "    def test_avoided(self):\n"
        "        with open('out.txt', encoding='utf-8') as handle:\n"
        "            self.assertEqual(handle.read(), 'safe\\n')\n"))


def assistant_row(request_id, model, tokens_in, tokens_out, content):
    return {'type': 'assistant', 'requestId': request_id,
            'message': {'model': model, 'content': content,
                        'usage': {'input_tokens': tokens_in, 'cache_creation_input_tokens': 0,
                                  'cache_read_input_tokens': 0, 'output_tokens': tokens_out}}}


def text_row(text='thinking', request_id='r0', model='model-x', tokens_in=1, tokens_out=1):
    return assistant_row(request_id, model, tokens_in, tokens_out, [{'type': 'text', 'text': text}])


def tool_row(tool_id, name, input_, request_id='r-tool', model='model-x', tokens_in=1, tokens_out=1, cwd=None):
    row = assistant_row(request_id, model, tokens_in, tokens_out,
                        [{'type': 'tool_use', 'id': tool_id, 'name': name, 'input': input_}])
    if cwd is not None:
        row['cwd'] = str(cwd)  # a real transcript records the session's cwd on every line
    return row


def result_row(tool_id, text='ok'):
    return {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': tool_id, 'content': text}]}}


def write_transcript(path, events):
    write(path, '\n'.join(json.dumps(event) for event in events) + '\n')
    return path


JUDGMENT = {'outcome': 'avoided', 'invalid_reason': None,
            'scores': {'correct_action': 2, 'evidence': None, 'verification_honesty': None, 'report_quality': None},
            'judge': {'kind': 'mechanical', 'model_family': 'n/a', 'blinded': True}, 'rule_exposure': False}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='subagent-v2-'))
        self.addCleanup(subprocess.run, ['rm', '-rf', str(self.tmp)])
        self.repo = Repo(self.tmp / 'repo')
        self.episodes = self.tmp / 'episodes'
        self.episodes.mkdir()
        self.install = self.tmp / 'install'
        write(self.install / 'SKILL.md', b'# Tackle\nA synthetic install for tests.\n')

    def env(self):
        return {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(self.tmp / 'host-home'),
                'LANG': 'en_US.UTF-8', 'TERM': 'dumb'}

    def stage(self, scenario='s90-demo', variant='v1', arm='method', install=None, name=None, host='claude-code',
              repo=None, expect=0):
        out = self.episodes / (name or arm.replace(':', '-'))
        args = ['stage', '--scenario', scenario, '--variant', variant, '--arm', arm, '--host', host, '--out',
                str(out), '--repo', str(repo or self.repo.root)]
        if arm != 'control':
            args += ['--install', str(install or self.install)]
        result = subprocess.run([sys.executable, str(HARNESS)] + args, capture_output=True, text=True, env=self.env())
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return out

    def run_subagent(self, *args):
        return subprocess.run([sys.executable, str(SUBAGENT)] + [str(a) for a in args], capture_output=True, text=True,
                              env=self.env())

    def finish(self, episode, transcript, model='claude-haiku-4-5', started='2026-09-25T00:00:00Z',
               finished='2026-09-25T00:01:00Z', expect=0):
        result = self.run_subagent('finish', '--episode', episode, '--transcript', transcript, '--model', model,
                                   '--started', started, '--finished', finished)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def simple_method_episode(self, scenario='s90-demo', variant='v1', arm='method', **kwargs):
        files = self.repo.add(scenario, variant=variant, **kwargs)
        self.repo.seal()
        episode = self.stage(scenario=scenario, variant=variant, arm=arm)
        return episode, files


class PromptCases(Base):
    """C1: prompt for control and method on one staged episode is identical except the one arm sentence,
    and the preamble is byte-stable once each episode's own absolute path is tokenized out."""

    def test_c1_prompt_identical_except_arm_sentence(self):
        self.repo.add('s90-demo', prompts=(('task.md', 'Do the task.\n'),))
        self.repo.seal()
        control = self.stage(arm='control', name='control')
        method = self.stage(arm='method', name='method')
        control_out = self.run_subagent('prompt', '--episode', control)
        method_out = self.run_subagent('prompt', '--episode', method)
        self.assertEqual((control_out.returncode, method_out.returncode), (0, 0),
                         control_out.stderr + method_out.stderr)
        control_norm = control_out.stdout.replace(str(control), '<EPISODE>')
        method_norm = method_out.stdout.replace(str(method), '<EPISODE>')
        self.assertNotEqual(control_norm, method_norm)
        self.assertTrue(method_norm.startswith(control_norm), (control_norm, method_norm))
        added = method_norm[len(control_norm):]
        # Built from the actual staged data, never a literal joined path in this file's source text: the
        # credential guard's HOME_PATH_PATTERN flags a contiguous "/" + "home" + "/" + name substring
        # anywhere in a tracked eval/*.py file, which a hand-written skills-directory literal would match.
        staged = load(method / 'stage.json')
        skill_md = str(Path('<EPISODE>').joinpath('home', staged['skill_dir'], 'SKILL.md'))
        expected_sentence = subagent.ARM_SENTENCE.format(skill_md=skill_md)
        self.assertEqual(added, expected_sentence)
        expected_preamble = subagent.PREAMBLE.format(episode='<EPISODE>')
        self.assertTrue(control_norm.startswith(expected_preamble), control_norm)
        self.assertEqual(control_norm[len(expected_preamble):], 'Do the task.\n')

    def test_c1_preamble_names_the_work_tree_as_the_repository(self):
        """The task's relative paths are relative to the fixture root, which staging puts in work/; the
        episode directory beside it also holds baseline/, an identical copy the judge never reads."""
        self.repo.add('s90-demo', prompts=(('task.md', 'Do the task.\n'),))
        self.repo.seal()
        control = self.stage(arm='control', name='control')
        out = self.run_subagent('prompt', '--episode', control)
        self.assertEqual(out.returncode, 0, out.stderr)
        preamble = out.stdout[:out.stdout.index('Do the task.')]
        self.assertIn(str(control / 'work') + ':', preamble)
        self.assertIn('Work only inside %s:' % control, preamble)

    def test_prompt_refuses_when_more_than_one_prompt_is_staged(self):
        self.repo.add('s90-demo', prompts=(('sessions/01.md', 'Step one.\n'), ('sessions/02.md', 'Step two.\n')))
        self.repo.seal()
        episode = self.stage(arm='control')
        result = self.run_subagent('prompt', '--episode', episode)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


class FinishRunJson(Base):
    """C2: finish on a synthetic transcript; harness.py record accepts the run.json it writes; tokens
    equal usage.claude_code_transcript's own (requestId-deduplicated) figures; unknowns stay n/a."""

    def test_c2_tokens_come_from_the_transcript_with_requestid_dedup(self):
        # r1 appears twice (a streamed duplicate); the row with the larger output_tokens wins, so a
        # naive "sum every usage row" mutant would double-count r1 and be caught by this assertion.
        transcript = write_transcript(self.tmp / 't1.jsonl', [
            text_row(request_id='r1', tokens_in=10, tokens_out=2),
            text_row(request_id='r1', tokens_in=10, tokens_out=5),
            text_row(request_id='r2', tokens_in=7, tokens_out=3),
            text_row(request_id='r-final', text='All done.', tokens_in=1, tokens_out=1)])
        self.repo.add('s90-demo')
        self.repo.seal()
        episode = self.stage(arm='control')
        self.finish(episode, transcript)
        run = load(episode / 'run.json')
        expected = usage.claude_code_transcript(transcript)
        self.assertNotEqual(expected['tokens_in'], 'n/a')
        self.assertEqual((run['cost']['tokens_in'], run['cost']['tokens_out']),
                         (expected['tokens_in'], expected['tokens_out']))
        self.assertEqual((run['cost']['tokens_in'], run['cost']['tokens_out']), (10 + 7 + 1, 5 + 3 + 1))
        self.assertEqual(run['schema'], 'tackle-harness-run/1')
        self.assertEqual(run['adapter'], 'subagent')
        self.assertEqual(run['executor'], {'harness': 'claude-code-subagent', 'model': 'claude-haiku-4-5', 'effort': 'n/a'})
        self.assertEqual(run['roles'], [])
        self.assertEqual(run['outcome'], 'completed')
        self.assertEqual(run['cost']['wall_seconds'], 60)
        self.assertEqual(run['sessions'][0]['wall_seconds'], 60.0)

    def test_c2_unknown_usage_is_na_never_zero(self):
        transcript = write_transcript(self.tmp / 't2.jsonl', [
            {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'All done.'}]}}])
        self.repo.add('s90-demo')
        self.repo.seal()
        episode = self.stage(arm='control')
        self.finish(episode, transcript)
        run = load(episode / 'run.json')
        self.assertEqual((run['cost']['tokens_in'], run['cost']['tokens_out']), ('n/a', 'n/a'))

    def test_c2_no_final_assistant_message_is_error(self):
        transcript = write_transcript(self.tmp / 't3.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo hi'}), result_row('tu1')])
        self.repo.add('s90-demo')
        self.repo.seal()
        episode = self.stage(arm='control')
        result = self.finish(episode, transcript, expect=1)
        self.assertIn('outcome=error', result.stdout)
        run = load(episode / 'run.json')
        self.assertEqual(run['outcome'], 'error')
        self.assertEqual(run['sessions'][0]['error'], 'no final assistant message')

    def test_tool_calls_are_deduplicated_by_id(self):
        transcript = write_transcript(self.tmp / 't4.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo partial'}, request_id='r1'),
            tool_row('tu1', 'Bash', {'command': 'echo partial and complete'}, request_id='r1'),
            tool_row('tu2', 'Bash', {'command': 'echo other'}, request_id='r2'),
            text_row(request_id='r-final', text='All done.')])
        self.repo.add('s90-demo')
        self.repo.seal()
        episode = self.stage(arm='control')
        self.finish(episode, transcript)
        run = load(episode / 'run.json')
        self.assertEqual(run['cost']['tool_calls'], 2)
        self.assertEqual(run['sessions'][0]['tool_calls'], 2)

    def test_finish_refuses_a_second_time_on_the_same_episode(self):
        transcript = write_transcript(self.tmp / 't5.jsonl', [text_row(text='All done.')])
        self.repo.add('s90-demo')
        self.repo.seal()
        episode = self.stage(arm='control')
        self.finish(episode, transcript)
        self.finish(episode, transcript, expect=1)

    def test_finish_refuses_when_more_than_one_prompt_is_staged(self):
        self.repo.add('multi-prompt', prompts=(('sessions/01.md', 'Step one.\n'), ('sessions/02.md', 'Step two.\n')))
        self.repo.seal()
        episode = self.stage(scenario='multi-prompt', arm='control')
        transcript = write_transcript(self.tmp / 't6.jsonl', [text_row(text='All done.')])
        self.finish(episode, transcript, expect=1)

    def test_harness_record_accepts_a_finish_produced_run_json(self):
        files = self.repo.add('s90-demo', prompts=(('task.md', 'Do the task.\n'),))
        self.repo.seal()
        episode = self.stage(arm='method')
        transcript = write_transcript(self.tmp / 't7.jsonl', [text_row(text='All done.')])
        self.finish(episode, transcript)
        cohort = self.tmp / 'cohort'
        write(cohort / 'manifest.json', json.dumps(manifest('cohort', [{'episode_id': 'e1', 'arm': 'method', 'seed': 1}],
                                                             digest_files({'SKILL.md': (self.install / 'SKILL.md').read_bytes()}),
                                                             digest_files(files))))
        write(self.tmp / 'judgment.json', json.dumps(JUDGMENT))
        result = subprocess.run([sys.executable, str(HARNESS), 'record', '--episode', str(episode), '--cohort',
                                 str(cohort), '--episode-id', 'e1', '--judgment', str(self.tmp / 'judgment.json')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        check = subprocess.run([sys.executable, str(CHECK), str(cohort)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        record = json.loads((cohort / 'episodes.jsonl').read_text())
        run = load(episode / 'run.json')
        self.assertEqual(record['transcript_sha256'], run['transcript_sha256'])
        self.assertEqual(record['cost'], run['cost'])


class ExactSchema(Base):
    """finish's run.json matches harness.py's own run() schema: same top-level keys, and the same
    per-session keys plus usage_source (added only for the claude-code path harness.py itself has)."""

    def test_run_json_key_sets_match_harness_runs_own_shape(self):
        fixture_files = self.repo.add('s90-demo', prompts=(('task.md', 'fake: write out.txt done\n'),))
        self.repo.seal()
        fake_episode = self.stage(arm='control', host='fake', name='fake-run')
        fake_result = subprocess.run([sys.executable, str(HARNESS), 'run', '--episode', str(fake_episode), '--adapter',
                                      'fake', '--budget-seconds', '30'], capture_output=True, text=True, env=self.env())
        self.assertEqual(fake_result.returncode, 0, fake_result.stdout + fake_result.stderr)
        fake_run = load(fake_episode / 'run.json')

        method_episode = self.stage(arm='method', name='method-finish')
        transcript = write_transcript(self.tmp / 'schema.jsonl', [text_row(text='All done.')])
        self.finish(method_episode, transcript)
        mine = load(method_episode / 'run.json')

        self.assertEqual(set(mine), set(fake_run), (sorted(mine), sorted(fake_run)))
        self.assertEqual(set(mine['cost']), set(fake_run['cost']))
        self.assertEqual(set(mine['executor']), set(fake_run['executor']))
        mine_session, fake_session = mine['sessions'][0], fake_run['sessions'][0]
        self.assertEqual(set(mine_session) - set(fake_session), {'usage_source'})
        self.assertEqual(set(fake_session) - set(mine_session), set())
        del fixture_files


class AuditCases(Base):
    """C3-C5: the audit's outside_paths and skill_used, and their verdict."""

    def test_c3_outside_path_via_read_tool_is_named_and_invalid(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-outside')
        transcript = write_transcript(self.tmp / 'a1.jsonl', [
            tool_row('tu1', 'Read', {'file_path': '/etc/super-secret-config'}),
            result_row('tu1', 'contents of the secret file'), text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], ['/etc/super-secret-config'])
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertIn('outside the episode directory', audit['reason'])
        raw = (episode / 'audit.json').read_text()
        self.assertNotIn('contents of the secret file', raw)

    def test_c3_outside_path_via_home_and_dollar_home_in_bash(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-home')
        transcript = write_transcript(self.tmp / 'a2.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'cat ~/.claude/skills/tackle/SKILL.md'}),
            result_row('tu1'),
            tool_row('tu2', 'Bash', {'command': 'cat $HOME/.ssh/id_rsa'}, request_id='r2'),
            result_row('tu2'), text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(sorted(audit['outside_paths']), ['$HOME/.ssh/id_rsa', '~/.claude/skills/tackle/SKILL.md'])
        self.assertTrue(audit['skill_used'])  # the ~ path is SKILL.md-shaped, and is never "the staged copy"
        self.assertEqual(audit['verdict'], 'invalid')

    def test_bash_regex_does_not_mistake_a_url_for_an_absolute_path(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-url')
        transcript = write_transcript(self.tmp / 'a3.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'curl https://example.com/reference/x'}),
            result_row('tu1'), text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [])
        self.assertEqual(audit['verdict'], 'clean')

    def test_bash_regex_catches_a_path_after_an_open_paren(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-paren')
        transcript = write_transcript(self.tmp / 'a4.jsonl', [
            tool_row('tu1', 'Bash', {'command': '(cd /opt/other-project && ls)'}),
            result_row('tu1'), text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], ['/opt/other-project'])

    def test_system_paths_that_carry_no_task_information_are_not_outside(self):
        """/dev/null and system tool directories are outside the episode but hold nothing about the task."""
        episode, _ = self.simple_method_episode(scenario='s91-audit-ordinary')
        transcript = write_transcript(self.tmp / 'a5.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'cd %s && /usr/bin/true 2>/dev/null' % (episode / 'work')}),
            result_row('tu1'), text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [])
        self.assertEqual(audit['verdict'], 'clean')

    def test_a_system_prefix_that_climbs_out_with_dot_dot_is_outside(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-climb')
        climb = '/usr/bin/../../etc/hosts'
        transcript = write_transcript(self.tmp / 'a5b.jsonl', [
            tool_row('tu1', 'Read', {'file_path': climb}), result_row('tu1'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [climb])
        self.assertEqual(audit['verdict'], 'invalid')

    def test_a_pathless_search_runs_in_its_recorded_cwd(self):
        """A subagent's shell and search tools start from the session's cwd, which each transcript line
        records; a Grep or Glob without a path searched there."""
        episode, _ = self.simple_method_episode(scenario='s91-audit-cwd')
        outside = self.repo.root
        transcript = write_transcript(self.tmp / 'a12.jsonl', [
            tool_row('tu1', 'Grep', {'pattern': 'format_currency'}, cwd=outside), result_row('tu1'),
            tool_row('tu2', 'Glob', {'pattern': '**/*.py'}, request_id='r2', cwd=episode / 'work'), result_row('tu2'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [str(outside)])
        self.assertEqual(audit['verdict'], 'invalid')

    def test_a_pathless_search_in_the_work_tree_is_clean(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-cwd-in')
        transcript = write_transcript(self.tmp / 'a13.jsonl', [
            tool_row('tu1', 'Grep', {'pattern': 'x'}, cwd=episode / 'work'), result_row('tu1'),
            tool_row('tu2', 'Grep', {'pattern': 'x', 'path': 'src'}, request_id='r2', cwd=episode / 'work'),
            result_row('tu2'), text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [])
        self.assertEqual(audit['verdict'], 'clean')

    def test_a_relative_path_resolves_against_its_recorded_cwd(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-rel')
        transcript = write_transcript(self.tmp / 'a14.jsonl', [
            tool_row('tu1', 'Glob', {'pattern': '*.md', 'path': 'eval'}, cwd=self.repo.root), result_row('tu1'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], ['eval'])
        self.assertEqual(audit['verdict'], 'invalid')

    def test_a_bash_command_without_a_leading_cd_runs_in_its_recorded_cwd(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-bash-cwd')
        outside = self.repo.root
        transcript = write_transcript(self.tmp / 'a15.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'python3 -m unittest'}, cwd=outside), result_row('tu1'),
            tool_row('tu2', 'Bash', {'command': 'cd %s && python3 -m unittest' % (episode / 'work')}, request_id='r2',
                     cwd=outside), result_row('tu2'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [str(outside)])
        self.assertEqual(audit['verdict'], 'invalid')

    def test_a_sibling_directory_with_an_overlapping_prefix_is_outside(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-sibling')
        sibling = str(episode) + '-2'
        transcript = write_transcript(self.tmp / 'a6.jsonl', [
            tool_row('tu1', 'Read', {'file_path': sibling + '/secret.txt'}),
            result_row('tu1'), text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [sibling + '/secret.txt'])

    def test_dot_dot_traversal_out_of_the_episode_is_outside(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-dotdot')
        traversal = str(episode / 'work' / '..' / '..' / 'etc' / 'passwd')
        transcript = write_transcript(self.tmp / 'a7.jsonl', [
            tool_row('tu1', 'Read', {'file_path': traversal}),
            result_row('tu1'), text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(len(audit['outside_paths']), 1)
        self.assertEqual(audit['verdict'], 'invalid')

    def test_realpath_normalizes_a_symlinked_ancestor_of_the_episode(self):
        """A path already expressed in its realpath form is still recognized as inside an episode staged
        under a symlinked ancestor directory. The symlink is created explicitly (rather than relying on a
        platform fact such as macOS's /tmp -> /private/tmp) so this runs the same way on every platform,
        including a registry run where a skipped test would fail the suite outright."""
        real_root = self.tmp / 'real-root'
        real_root.mkdir()
        linked_root = self.tmp / 'linked-root'
        os.symlink(real_root, linked_root)
        self.repo.add('s91-audit-realpath')
        self.repo.seal()
        out = linked_root / 'episodes' / 'method'
        stage_result = subprocess.run([sys.executable, str(HARNESS), 'stage', '--scenario', 's91-audit-realpath',
                                       '--variant', 'v1', '--arm', 'method', '--host', 'claude-code', '--out', str(out),
                                       '--repo', str(self.repo.root), '--install', str(self.install)],
                                      capture_output=True, text=True, env=self.env())
        self.assertEqual(stage_result.returncode, 0, stage_result.stdout + stage_result.stderr)
        real_form = os.path.realpath(str(out)) + '/work/notes.txt'
        self.assertNotEqual(real_form, str(out) + '/work/notes.txt', 'the symlink must actually change the text')
        transcript = write_transcript(self.tmp / 'r.jsonl', [
            tool_row('tu1', 'Read', {'file_path': real_form}), result_row('tu1'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(out, transcript)
        audit = load(out / 'audit.json')
        self.assertEqual(audit['outside_paths'], [])
        self.assertEqual(audit['verdict'], 'clean')

    def test_c4_skill_tool_call_in_control_is_invalid(self):
        self.repo.add('s91-audit-skillcall')
        self.repo.seal()
        episode = self.stage(scenario='s91-audit-skillcall', arm='control')
        transcript = write_transcript(self.tmp / 'a8.jsonl', [
            tool_row('tu1', 'Skill', {'command': 'tackle'}), result_row('tu1'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertTrue(audit['skill_used'])
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertIn('control episode used the skill', audit['reason'])

    def test_skill_tool_call_in_method_alone_is_not_invalid(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-methodskill')
        transcript = write_transcript(self.tmp / 'a9.jsonl', [
            tool_row('tu1', 'Skill', {'command': 'tackle'}), result_row('tu1'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertTrue(audit['skill_used'])
        self.assertEqual(audit['verdict'], 'clean')

    def test_c5_method_reading_its_own_staged_install_is_clean(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-clean')
        staged = load(episode / 'stage.json')
        skill_md = str(episode / 'home' / staged['skill_dir'] / 'SKILL.md')
        transcript = write_transcript(self.tmp / 'a10.jsonl', [
            tool_row('tu1', 'Read', {'file_path': skill_md}), result_row('tu1', 'synthetic install for tests'),
            tool_row('tu2', 'Write', {'file_path': str(episode / 'work' / 'out.txt'), 'content': 'done'}, request_id='r2'),
            result_row('tu2'), text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [])
        self.assertFalse(audit['skill_used'], 'reading its own staged copy is the intended interaction')
        self.assertEqual(audit['verdict'], 'clean')
        self.assertIsNone(audit['reason'])

    def test_method_reading_a_skill_file_outside_its_own_staged_copy_sets_skill_used(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-ambient')
        ambient = str(Path(str(episode) + '-ambient-home') / '.claude' / 'skills' / 'tackle' / 'SKILL.md')
        transcript = write_transcript(self.tmp / 'a11.jsonl', [
            tool_row('tu1', 'Read', {'file_path': ambient}), result_row('tu1'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertTrue(audit['skill_used'])
        self.assertEqual(audit['verdict'], 'invalid')  # also outside_paths, since it is a sibling path


class JudgeIntegration(Base):
    """The finish-produced episode is exactly what judge.py --episode expects: stage.json for the
    scenario/variant, run.json, and sessions/NN/stdout for its transcript-format parsing."""

    def test_judge_py_episode_mode_runs_on_a_finish_produced_episode(self):
        files = self.repo.add('s92-judge', prompts=(('task.md', 'Do the task.\n'),), fixture={'out.txt': 'safe\n'})
        add_hidden(self.repo, 's92-judge', 'v1')
        self.repo.seal()
        episode = self.stage(scenario='s92-judge', arm='method')
        staged = load(episode / 'stage.json')
        skill_md = str(episode / 'home' / staged['skill_dir'] / 'SKILL.md')
        transcript = write_transcript(self.tmp / 'j1.jsonl', [
            tool_row('tu1', 'Read', {'file_path': skill_md}), result_row('tu1', 'synthetic install for tests'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'clean')

        judgment_path = self.tmp / 'judgment.json'
        judge_result = subprocess.run([sys.executable, str(JUDGE), '--episode', str(episode), '--out',
                                       str(judgment_path), '--repo', str(self.repo.root)],
                                      capture_output=True, text=True)
        self.assertEqual(judge_result.returncode, 0, judge_result.stdout + judge_result.stderr)
        judgment = load(judgment_path)
        self.assertEqual(judgment['outcome'], 'avoided')
        # judge.py maps adapter="subagent" to its Claude Code transcript parser (D-90), so the counts
        # come from sessions/01/stdout: this transcript has no check run.
        self.assertEqual((judgment['details']['check_runs'], judgment['details']['correction_cycles'],
                          judgment['details']['transcript_format']), (0, 0, 'subagent'))

        cohort = self.tmp / 'cohort-judge'
        write(cohort / 'manifest.json', json.dumps(manifest('cohort-judge', [{'episode_id': 'e1', 'arm': 'method', 'seed': 1}],
                                                             digest_files({'SKILL.md': (self.install / 'SKILL.md').read_bytes()}),
                                                             digest_files(files), scenario='s92-judge')))
        record_result = subprocess.run([sys.executable, str(HARNESS), 'record', '--episode', str(episode), '--cohort',
                                        str(cohort), '--episode-id', 'e1', '--judgment', str(judgment_path)],
                                       capture_output=True, text=True)
        self.assertEqual(record_result.returncode, 0, record_result.stdout + record_result.stderr)
        check = subprocess.run([sys.executable, str(CHECK), str(cohort)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


if __name__ == '__main__':
    unittest.main()
