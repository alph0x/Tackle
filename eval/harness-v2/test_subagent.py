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


ROUTED_ARM = subagent.ROUTED_ARM
SPLIT_ARM = subagent.SPLIT_ARM


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


def handback_row(message, tool_id='tu-final', request_id='r-final', cwd=None):
    """The subagent's final report, delivered through the harness's own SubagentHandback tool."""
    return tool_row(tool_id, 'SubagentHandback', {'message': message}, request_id=request_id, cwd=cwd)


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
               finished='2026-09-25T00:01:00Z', expect=0, session=None, role=None, tier=None, notice=None,
               status='completed'):
        args = ['finish', '--episode', episode, '--transcript', transcript, '--model', model, '--started', started,
               '--finished', finished]
        if session is not None:
            args += ['--session', session]
        if role is not None:
            args += ['--role', role]
        if tier is not None:
            args += ['--tier', tier]
        args += ['--notice-status', status]
        if status == 'completed':
            count = notice if notice is not None else len(subagent.tool_uses(subagent.events_of(
                Path(transcript).read_bytes())))
            args += ['--notice-tool-calls', count]
        result = self.run_subagent(*args)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def close(self, episode, expect=0):
        result = self.run_subagent('close', '--episode', episode)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def tier(self, episode):
        result = self.run_subagent('tier', '--episode', episode)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def routed_episode(self, scenario='s90-demo', variant='v1', **kwargs):
        files = self.repo.add(scenario, variant=variant, **kwargs)
        self.repo.seal()
        episode = self.stage(scenario=scenario, variant=variant, arm=ROUTED_ARM)
        return episode, files

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

    def test_c1_the_method_sentence_asks_for_the_method(self):
        """A sentence that only names the staged path did not make the executor read it (the first smoke,
        D-97); the treated arm asks for the method, as a user who invokes it does."""
        self.repo.add('s90-demo', prompts=(('task.md', 'Do the task.\n'),))
        self.repo.seal()
        method = self.stage(arm='method', name='method')
        out = self.run_subagent('prompt', '--episode', method)
        self.assertEqual(out.returncode, 0, out.stderr)
        staged = load(method / 'stage.json')
        skill_md = str(method.joinpath('home', staged['skill_dir'], 'SKILL.md'))
        added = out.stdout[out.stdout.index('Do the task.\n') + len('Do the task.\n'):]
        self.assertIn('Use the Tackle method for this task', added)
        self.assertIn(skill_md, added)
        self.assertIn('read that file first and follow it', added)

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

    def test_c2_no_final_assistant_message_is_refused(self):
        transcript = write_transcript(self.tmp / 't3.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo hi'}), result_row('tu1')])
        self.repo.add('s90-demo')
        self.repo.seal()
        episode = self.stage(arm='control')
        result = self.finish(episode, transcript, expect=1)
        self.assertIn("the transcript does not end on the assistant's final message yet", result.stderr)
        self.assertFalse((episode / 'run.json').exists())
        self.assertFalse((episode / 'audit.json').exists())
        self.assertFalse((episode / 'sessions').exists())

    def test_tool_calls_are_deduplicated_by_id(self):
        transcript = write_transcript(self.tmp / 't4.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo partial'}, request_id='r1'),
            tool_row('tu1', 'Bash', {'command': 'echo partial and complete'}, request_id='r1'),
            tool_row('tu2', 'Bash', {'command': 'echo other'}, request_id='r2'),
            result_row('tu2'),
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

    def test_text_tool_programs_and_patterns_are_not_paths(self):
        """An awk program, a grep pattern and sed expressions hold slash-delimited regexes and ~~~ fence
        checks: code, not paths (a live planner's commands tripped the audit on exactly these)."""
        episode, _ = self.simple_method_episode(scenario='s91-audit-patterns')
        work = episode / 'work'
        commands = [
            "cd %s && awk '/^```python$/{f=1; next} f && /^```$/{f=0; exit} f' %s/brief.md" % (work, episode),
            "cd %s && grep -n -i -E 'claude|/private/|/tmp/|opus' %s/brief.md" % (work, episode),
            "cd %s && sed -e 's/a\\/b/c/' -e \"s#/usr/local#/opt#\" notes.txt" % work,
            "cd %s && awk 'BEGIN{x=1} (substr(t,1,3)==\"~~~\"){print}' notes.md" % work,
            "cd %s && grep -E \\\n  'x|/tmp/y' notes.md" % work]
        rows = []
        for i, command in enumerate(commands):
            rows += [tool_row('tu%d' % i, 'Bash', {'command': command}, request_id='r%d' % i), result_row('tu%d' % i)]
        transcript = write_transcript(self.tmp / 'a-patterns.jsonl', rows + [text_row(request_id='r-final', text='DONE')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [])
        self.assertEqual(audit['verdict'], 'clean')

    def test_text_tool_file_arguments_still_count(self):
        """Blanking a program or pattern never hides a file the tool reads: data files and -f files stay."""
        episode, _ = self.simple_method_episode(scenario='s91-audit-tool-files')
        work = episode / 'work'
        commands = ["cd %s && awk '{print}' /etc/passwd" % work, "cd %s && grep -f /etc/patterns notes.txt" % work,
                    "cd %s && sed -n '1p' /opt/other/x.txt" % work, "cd %s && cat '/etc/hosts'" % work]
        rows = []
        for i, command in enumerate(commands):
            rows += [tool_row('tu%d' % i, 'Bash', {'command': command}, request_id='r%d' % i), result_row('tu%d' % i)]
        transcript = write_transcript(self.tmp / 'a-tool-files.jsonl', rows + [text_row(request_id='r-final', text='DONE')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(sorted(audit['outside_paths']), ['/etc/hosts', '/etc/passwd', '/etc/patterns',
                                                          '/opt/other/x.txt'])
        self.assertEqual(audit['verdict'], 'invalid')

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

    def test_a_bash_command_that_names_only_paths_inside_the_episode_is_clean(self):
        """Without a leading cd, a command that names an absolute path inside the episode works on that
        path (the second smoke's find, D-97); only a command naming nothing inside counts the cwd."""
        episode, _ = self.simple_method_episode(scenario='s91-audit-bash-inside')
        transcript = write_transcript(self.tmp / 'a19.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'find %s -type f -name "*.py" | head -20' % (episode / 'work')},
                     cwd=self.repo.root), result_row('tu1'),
            text_row(request_id='r-final', text='DONE')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [])
        self.assertEqual(audit['verdict'], 'clean')

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

    def test_a_tool_that_reaches_beyond_the_episode_without_a_path_is_outside(self):
        """An MCP tool (a code graph over the host repository, a browser, a terminal), web access or a nested
        agent reaches past the episode without naming a path; only the listed local tools are auditable."""
        episode, _ = self.simple_method_episode(scenario='s91-audit-tools')
        transcript = write_transcript(self.tmp / 'a16.jsonl', [
            tool_row('tu1', 'mcp__graft__graft_find_code', {'query': 'format_currency'}), result_row('tu1'),
            tool_row('tu2', 'WebFetch', {'url': 'https://example.com/x'}, request_id='r2'), result_row('tu2'),
            tool_row('tu3', 'Agent', {'prompt': 'help'}, request_id='r3'), result_row('tu3'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], ['tool:mcp__graft__graft_find_code', 'tool:WebFetch', 'tool:Agent'])
        self.assertEqual(audit['verdict'], 'invalid')

    def test_the_final_handback_is_not_an_outside_tool(self):
        """A subagent returns its final report through the harness's SubagentHandback tool (observed in
        the first smoke episode); it reads and writes nothing."""
        episode, _ = self.simple_method_episode(scenario='s91-audit-handback')
        transcript = write_transcript(self.tmp / 'a18.jsonl', [
            tool_row('tu1', 'Read', {'file_path': str(episode / 'work' / 'a.py')}, cwd=episode / 'work'),
            result_row('tu1'),
            tool_row('tu2', 'SubagentHandback', {'message': 'DONE'}, request_id='r2', cwd=episode / 'work'),
            result_row('tu2'), text_row(request_id='r-final', text='DONE')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['outside_paths'], [])
        self.assertEqual(audit['verdict'], 'clean')

    def test_local_tools_inside_the_episode_are_clean(self):
        episode, _ = self.simple_method_episode(scenario='s91-audit-local')
        work = episode / 'work'
        transcript = write_transcript(self.tmp / 'a17.jsonl', [
            tool_row('tu1', 'ToolSearch', {'query': 'select:TodoWrite'}, cwd=work), result_row('tu1'),
            tool_row('tu2', 'TodoWrite', {'todos': []}, request_id='r2', cwd=work), result_row('tu2'),
            tool_row('tu3', 'Edit', {'file_path': str(work / 'a.py'), 'old_string': 'x', 'new_string': 'y'},
                     request_id='r3', cwd=work), result_row('tu3'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)
        audit = load(episode / 'audit.json')
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


def write_brief(episode, tier='standard', escalation=None):
    text = '**Tier**: %s\n' % tier
    if escalation is not None:
        text += '**Escalation**: %s\n' % escalation
    write(episode / 'brief.md', text)


def write_split_brief(episode, escalation=None):
    """A real method:split brief never carries a Tier line (Contract §1, Findings 3: the shipped prompt
    never invites one); an Escalation line only appears when a test specifically exercises the tool's own
    arm-agnostic escalation-declared rule against this arm, never because the real prompt offers one."""
    text = 'A plain paper plan with no Tier line.\n'
    if escalation is not None:
        text += '**Escalation**: %s\n' % escalation
    write(episode / 'brief.md', text)


class RoutedEpisodeCases(Base):
    """The subagent-episode path for a method:routed episode: session 1 (the planner) and session 2 (or
    3, the executor and its one capped, unit-tested-only escalation) recorded separately by `finish
    --session N`, merged once by `close`."""

    def session_one(self, episode, tier='standard', escalation=None, work_touched=False, no_brief=False,
                    outside=None):
        if not no_brief:
            write_brief(episode, tier=tier, escalation=escalation)
        if work_touched:
            write((episode / 'work' / 'planner-left-this.txt'), 'should not be here\n')
        events = [handback_row('DONE'), result_row('tu-final'), text_row()]
        if outside:
            events = [tool_row('tu-outside', 'Read', {'file_path': outside}), result_row('tu-outside')] + events
        transcript = write_transcript(self.tmp / 'session1.jsonl', events)
        return self.finish(episode, transcript, session=1, role='planner', tier='frontier')

    def session_two(self, episode, report='DONE', outside=None, index=2):
        events = []
        if outside:
            events = [tool_row('tu-outside-%d' % index, 'Read', {'file_path': outside}),
                      result_row('tu-outside-%d' % index)]
        events.append(handback_row(report, tool_id='tu-final-%d' % index, request_id='r-final-%d' % index))
        events.append(result_row('tu-final-%d' % index))
        events.append(text_row(request_id='r-final-%d-text' % index))
        transcript = write_transcript(self.tmp / ('session%d.jsonl' % index), events)
        return self.finish(episode, transcript, session=index, role='executor', tier='fast')

    def test_session_one_writes_only_its_session_files_and_defers_close(self):
        episode, _ = self.routed_episode()
        result = self.session_one(episode)
        self.assertIn('session 1 recorded', result.stdout)
        self.assertFalse((episode / 'run.json').exists())
        self.assertFalse((episode / 'audit.json').exists())
        meta = load(episode / 'sessions' / '01' / 'meta.json')
        self.assertEqual((meta['role'], meta['tier'], meta['index']), ('planner', 'frontier', 1))
        self.assertIn('work_sha256', meta)

    def test_session_one_that_touches_the_work_tree_is_invalid_at_close(self):
        episode, _ = self.routed_episode()
        self.session_one(episode, work_touched=True)
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertIn('planner session modified the work tree', audit['reason'])

    def test_session_one_with_no_brief_is_invalid_at_close(self):
        episode, _ = self.routed_episode()
        self.session_one(episode, no_brief=True)
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertEqual(audit['reason'], 'planner produced no brief')

    def test_two_clean_sessions_merge_into_one_run_with_two_roles(self):
        episode, _ = self.routed_episode()
        self.session_one(episode, tier='fast')
        self.session_two(episode)
        self.close(episode)
        run = load(episode / 'run.json')
        audit = load(episode / 'audit.json')
        self.assertEqual(len(run['roles']), 2)
        self.assertEqual([role['role'] for role in run['roles']], ['planner', 'executor'])
        self.assertEqual(run['roles'][0]['tier'], 'frontier')
        self.assertEqual(run['roles'][1]['tier'], 'fast')
        self.assertEqual(audit['verdict'], 'clean')
        self.assertEqual(run['outcome'], 'completed')

    def test_declared_escalation_with_a_synthetic_third_session_is_accepted(self):
        """Escalation is never dispatched live for 9.0.0; this proves only the tool's own capability, with
        a synthetic session 3 supplied by the test, never a real model call."""
        episode, _ = self.routed_episode()
        self.session_one(episode, escalation='declared')
        self.session_two(episode, report='ESCALATE')
        third = write_transcript(self.tmp / 'session3.jsonl', [
            handback_row('DONE', tool_id='tu-final-3', request_id='r-final-3'),
            result_row('tu-final-3'), text_row(request_id='r-final-3-text')])
        self.finish(episode, third, session=3, role='executor', tier='standard')
        self.close(episode)
        run = load(episode / 'run.json')
        audit = load(episode / 'audit.json')
        self.assertEqual(len(run['roles']), 3)
        self.assertEqual(audit['verdict'], 'clean')

    def test_undeclared_escalation_is_invalid(self):
        episode, _ = self.routed_episode()
        self.session_one(episode, escalation=None)
        self.session_two(episode, report='ESCALATE')
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertIn('escalation without a declared brief', audit['reason'])

    def test_a_nested_task_call_in_session_one_is_invalid(self):
        episode, _ = self.routed_episode()
        write_brief(episode)
        transcript = write_transcript(self.tmp / 's1-nested.jsonl', [
            tool_row('tu1', 'Task', {'prompt': 'help'}), result_row('tu1'), handback_row('DONE'),
            result_row('tu-final'), text_row()])
        self.finish(episode, transcript, session=1, role='planner', tier='frontier')
        self.session_two(episode)
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertIn('tool:Task', audit['outside_paths'])

    def test_a_nested_task_call_in_session_two_is_invalid(self):
        episode, _ = self.routed_episode()
        self.session_one(episode)
        transcript = write_transcript(self.tmp / 's2-nested.jsonl', [
            tool_row('tu1', 'Task', {'prompt': 'help'}), result_row('tu1'), handback_row('DONE'),
            result_row('tu-final'), text_row()])
        self.finish(episode, transcript, session=2, role='executor', tier='fast')
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertIn('tool:Task', audit['outside_paths'])

    def test_session_two_reading_the_raw_staged_prompt_is_invalid(self):
        episode, _ = self.routed_episode()
        self.session_one(episode)
        staged = load(episode / 'stage.json')
        prompt_path = str(episode / 'prompts' / staged['prompts'][0])
        self.session_two(episode, outside=prompt_path)
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertIn('executor read past its brief', audit['reason'])
        self.assertIn(prompt_path, audit['outside_paths'])

    def test_session_one_reading_its_own_staged_prompt_is_not_invalid(self):
        """The deny-prefix rule is session >= 2 only: session 1 legitimately reads prompts/."""
        episode, _ = self.routed_episode()
        staged_before = load(episode / 'stage.json')
        prompt_path = str(episode / 'prompts' / staged_before['prompts'][0])
        self.session_one(episode, outside=prompt_path)
        self.session_two(episode)
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'clean')

    def test_live_escalation_with_no_session_three_is_invalid(self):
        episode, _ = self.routed_episode()
        self.session_one(episode, escalation='declared')
        self.session_two(episode, report='ESCALATE')
        self.assertFalse((episode / 'sessions' / '03').exists())
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertIn('live escalation out of scope for 9.0.0', audit['reason'])

    def test_close_is_reused_by_a_completed_episode_with_judge_and_record(self):
        """The merged episode still satisfies judge.py --episode and harness.py record, exactly as a
        single-session one does."""
        files = self.repo.add('s92-judge', prompts=(('task.md', 'Do the task.\n'),), fixture={'out.txt': 'safe\n'})
        add_hidden(self.repo, 's92-judge', 'v1')
        self.repo.seal()
        episode = self.stage(scenario='s92-judge', arm=ROUTED_ARM)
        self.session_one(episode)
        self.session_two(episode)
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'clean')
        judgment_path = self.tmp / 'judgment-routed.json'
        judge_result = subprocess.run([sys.executable, str(JUDGE), '--episode', str(episode), '--out',
                                       str(judgment_path), '--repo', str(self.repo.root)],
                                      capture_output=True, text=True)
        self.assertEqual(judge_result.returncode, 0, judge_result.stdout + judge_result.stderr)
        cohort = self.tmp / 'cohort-routed'
        write(cohort / 'manifest.json', json.dumps(manifest(
            'cohort-routed', [{'episode_id': 'e1', 'arm': ROUTED_ARM, 'seed': 1}],
            digest_files({'SKILL.md': (self.install / 'SKILL.md').read_bytes()}), digest_files(files),
            scenario='s92-judge')))
        record_result = subprocess.run([sys.executable, str(HARNESS), 'record', '--episode', str(episode), '--cohort',
                                        str(cohort), '--episode-id', 'e1', '--judgment', str(judgment_path)],
                                       capture_output=True, text=True)
        self.assertEqual(record_result.returncode, 0, record_result.stdout + record_result.stderr)
        check = subprocess.run([sys.executable, str(CHECK), str(cohort)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        record = json.loads((cohort / 'episodes.jsonl').read_text())
        self.assertEqual(len(record['roles']), 2)


class TierExtraction(Base):
    """`subagent.py tier`: a mechanical, read-only grep of brief.md, restricted to the closed vocabulary."""

    def test_a_present_valid_tier_and_declared_escalation(self):
        episode, _ = self.routed_episode()
        write_brief(episode, tier='standard', escalation='declared')
        self.assertEqual(self.tier(episode), 'tier=standard escalation=declared')

    def test_an_absent_brief_prints_n_a_and_absent(self):
        episode, _ = self.routed_episode()
        self.assertEqual(self.tier(episode), 'tier=n/a escalation=absent')

    def test_a_malformed_tier_line_prints_n_a(self):
        episode, _ = self.routed_episode()
        write((episode / 'brief.md'), '**Tier**: someday\n')
        self.assertEqual(self.tier(episode), 'tier=n/a escalation=absent')

    def test_a_valid_value_followed_by_trailing_prose_prints_n_a(self):
        """A script's own field match, never planner-authored prose echoed back to the coordinator."""
        episode, _ = self.routed_episode()
        write((episode / 'brief.md'), '**Tier**: standard, because the task is simple\n')
        self.assertEqual(self.tier(episode), 'tier=n/a escalation=absent')

    def test_the_task_templates_bullet_fields_are_read(self):
        """A planner following the task template writes its fields as bullets: `- **Tier**: fast`. Missing
        them sent every live routed episode to the fallback tier and hid its declared escalation."""
        episode, _ = self.routed_episode()
        write((episode / 'brief.md'), '# Task\n\n- **Tier**: standard\n- **Tier reason**: default\n'
                                      '- **Escalation**: declared\n')
        self.assertEqual(self.tier(episode), 'tier=standard escalation=declared')

    def test_a_bullet_field_with_trailing_prose_still_prints_n_a(self):
        episode, _ = self.routed_episode()
        write((episode / 'brief.md'), '- **Tier**: fast, since it is cheap\n')
        self.assertEqual(self.tier(episode), 'tier=n/a escalation=absent')


class FinishReplacementGuard(Base):
    """The new per-session guard (readiness F8): no silent rerun, no out-of-order finish, and --session
    stays refused outside a method:routed episode."""

    def test_a_repeat_session_two_is_refused(self):
        episode, _ = self.routed_episode()
        self.session_one_default(episode)
        self.session_two_default(episode)
        transcript = write_transcript(self.tmp / 'repeat.jsonl', [handback_row('DONE')])
        self.finish(episode, transcript, session=2, role='executor', tier='fast', expect=1)

    def session_one_default(self, episode):
        write_brief(episode)
        transcript = write_transcript(self.tmp / 's1-default.jsonl',
                                      [handback_row('DONE'), result_row('tu-final'), text_row()])
        self.finish(episode, transcript, session=1, role='planner', tier='frontier')

    def session_two_default(self, episode):
        transcript = write_transcript(self.tmp / 's2-default.jsonl',
                                      [handback_row('DONE'), result_row('tu-final'), text_row()])
        self.finish(episode, transcript, session=2, role='executor', tier='fast')

    def test_session_two_with_no_session_one_recorded_is_refused(self):
        episode, _ = self.routed_episode()
        transcript = write_transcript(self.tmp / 's2-orphan.jsonl', [handback_row('DONE')])
        self.finish(episode, transcript, session=2, role='executor', tier='fast', expect=1)

    def test_session_on_a_control_episode_is_refused(self):
        self.repo.add('s90-demo')
        self.repo.seal()
        episode = self.stage(arm='control')
        transcript = write_transcript(self.tmp / 's2-control.jsonl', [text_row(text='All done.')])
        self.finish(episode, transcript, session=2, expect=1)


class SplitEpisodeCases(Base):
    """The subagent-episode path generalized to the fifth arm, method:split (Contract §1, §3): both
    sessions pinned to the cheapest tier, and the arm's own prompt text never offers a Tier or an
    Escalation choice, unlike method:routed's own."""

    def split_episode(self, scenario='s90-demo', variant='v1', **kwargs):
        files = self.repo.add(scenario, variant=variant, **kwargs)
        self.repo.seal()
        episode = self.stage(scenario=scenario, variant=variant, arm=SPLIT_ARM)
        return episode, files

    def planner(self, episode, escalation=None, work_touched=False, no_brief=False, index=1, tier='fast'):
        if not no_brief:
            write_split_brief(episode, escalation=escalation)
        if work_touched:
            write((episode / 'work' / 'planner-left-this.txt'), 'should not be here\n')
        transcript = write_transcript(self.tmp / ('split-s%d.jsonl' % index), [
            handback_row('DONE', tool_id='tu-final-%d' % index, request_id='r-final-%d' % index),
            result_row('tu-final-%d' % index), text_row(request_id='r-final-%d-text' % index)])
        return self.finish(episode, transcript, session=index, role='planner', tier=tier)

    def executor(self, episode, report='DONE', index=2, tier='fast'):
        transcript = write_transcript(self.tmp / ('split-s%d.jsonl' % index), [
            handback_row(report, tool_id='tu-final-%d' % index, request_id='r-final-%d' % index),
            result_row('tu-final-%d' % index), text_row(request_id='r-final-%d-text' % index)])
        return self.finish(episode, transcript, session=index, role='executor', tier=tier)

    def test_c1_session_one_writes_only_its_session_files_and_defers_close(self):
        episode, _ = self.split_episode()
        result = self.planner(episode)
        self.assertIn('session 1 recorded', result.stdout)
        self.assertFalse((episode / 'run.json').exists())
        self.assertFalse((episode / 'audit.json').exists())
        meta = load(episode / 'sessions' / '01' / 'meta.json')
        self.assertEqual((meta['role'], meta['tier'], meta['index']), ('planner', 'fast', 1))
        self.assertIn('work_sha256', meta)

    def test_c2_two_clean_sessions_merge_into_one_run_with_two_roles_both_at_fast(self):
        episode, _ = self.split_episode()
        self.planner(episode)
        self.executor(episode)
        self.close(episode)
        run = load(episode / 'run.json')
        audit = load(episode / 'audit.json')
        self.assertEqual(len(run['roles']), 2)
        self.assertEqual([r['role'] for r in run['roles']], ['planner', 'executor'])
        self.assertEqual([r['tier'] for r in run['roles']], ['fast', 'fast'])
        self.assertEqual(audit['verdict'], 'clean')
        self.assertEqual(run['outcome'], 'completed')

    def test_c3_planner_prompt_never_offers_tier_or_escalation(self):
        episode, _ = self.split_episode()
        out = self.run_subagent('prompt', '--episode', episode, '--session', '1')
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn('**Tier**:', out.stdout)
        self.assertNotIn('**Escalation**:', out.stdout)
        self.assertIn('paper plan', out.stdout)

    def test_c4_executor_prompt_never_offers_escalate(self):
        episode, _ = self.split_episode()
        write_split_brief(episode)
        out = self.run_subagent('prompt', '--episode', episode, '--session', '2')
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn('ESCALATE', out.stdout)
        self.assertIn('DONE', out.stdout)

    def test_c5_freelance_escalate_with_no_declared_brief_is_invalid(self):
        episode, _ = self.split_episode()
        self.planner(episode, escalation=None)
        self.executor(episode, report='ESCALATE')
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertIn('escalation without a declared brief', audit['reason'])

    def test_c6_escalation_past_its_one_capped_retry_is_invalid(self):
        """Findings 2: a session-3 ESCALATE (a further escalation attempt past the one capped retry the
        shipped skill allows) used to be accepted, because no prior fixture ever exercised a real session
        3. Session 2's own legitimate escalation must not itself be flagged."""
        episode, _ = self.split_episode()
        self.planner(episode, escalation='declared')
        self.executor(episode, report='ESCALATE', index=2)
        self.executor(episode, report='ESCALATE', index=3, tier='standard')
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertEqual(audit['reason'], 'escalation attempted past its one capped retry')

    def test_c17_declared_escalation_with_a_real_third_session_is_accepted(self):
        """Mirrors the tool's own pre-existing synthetic 3-session proof
        (RoutedEpisodeCases.test_declared_escalation_with_a_synthetic_third_session_is_accepted), now
        exercised for the new arm — the exact shape the live escalation mechanism episode's own merged
        record has: planner (fast), executor (fast, ESCALATE), executor (standard, DONE)."""
        episode, _ = self.split_episode()
        self.planner(episode, escalation='declared')
        self.executor(episode, report='ESCALATE', index=2, tier='fast')
        self.executor(episode, report='DONE', index=3, tier='standard')
        self.close(episode)
        run = load(episode / 'run.json')
        audit = load(episode / 'audit.json')
        self.assertEqual(len(run['roles']), 3)
        self.assertEqual([r['tier'] for r in run['roles']], ['fast', 'fast', 'standard'])
        self.assertEqual(audit['verdict'], 'clean')

    def test_c19_session_three_present_without_a_preceding_escalation_is_invalid(self):
        """readiness F8: nothing used to couple 'a session 3 was recorded' to 'session 2 actually
        escalated' — a coordinator slip that dispatched a third session after an ordinary session 2 (final
        report DONE, not ESCALATE) merged into a clean 3-role record with no invalidity signal."""
        episode, _ = self.split_episode()
        self.planner(episode)
        self.executor(episode, report='DONE', index=2)
        self.executor(episode, report='DONE', index=3, tier='standard')
        self.close(episode)
        audit = load(episode / 'audit.json')
        self.assertEqual(audit['verdict'], 'invalid')
        self.assertEqual(audit['reason'], 'session 3 present without a preceding escalation')


class MultiSessionArmRefusals(Base):
    """C7-C9: the multi-session mechanism refuses every non-multi-session arm, generalizing the existing
    control-only and routed-only fixtures to MULTI_SESSION_ARMS."""

    def test_c7_close_refuses_a_non_multi_session_arm(self):
        episode, _ = self.simple_method_episode(scenario='s93-refuse-close', arm='method:candidate')
        result = self.run_subagent('close', '--episode', episode)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_c8_finish_session_refuses_a_non_multi_session_arm(self):
        episode, _ = self.simple_method_episode(scenario='s93-refuse-finish', arm='method:candidate')
        transcript = write_transcript(self.tmp / 'refuse-finish.jsonl', [handback_row('DONE')])
        self.finish(episode, transcript, session=2, role='executor', tier='fast', expect=1)

    def test_c9_prompt_session_refuses_a_non_multi_session_arm(self):
        episode, _ = self.simple_method_episode(scenario='s93-refuse-prompt', arm='method:candidate')
        result = self.run_subagent('prompt', '--episode', episode, '--session', '2')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


class HostNoticeCases(Base):
    """finish records a session only against the host's own notice for it. A completed notice must match
    the transcript's own deduplicated tool-call count, the transcript's last tool call must already carry
    its result, and the transcript must end on the assistant's own message; otherwise nothing is written.
    A failed notice always records an error outcome, whatever the transcript's last message is. The two
    notice options are required together and validated as a pair before anything else is read."""

    def test_a_notice_claiming_more_calls_than_the_transcript_holds_is_refused(self):
        episode, _ = self.simple_method_episode(scenario='notice-undercount')
        transcript = write_transcript(self.tmp / 'undercount.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo one'}), result_row('tu1'),
            tool_row('tu2', 'Bash', {'command': 'echo two'}, request_id='r2'), result_row('tu2'),
            text_row(request_id='r-final', text='All done.')])
        result = self.finish(episode, transcript, notice=3, expect=1)
        self.assertIn('the transcript holds 2 tool calls and the completion notice 3', result.stderr)
        self.assertFalse((episode / 'run.json').exists())
        self.assertFalse((episode / 'audit.json').exists())
        self.assertFalse((episode / 'sessions').exists())

    def test_a_notice_claiming_fewer_calls_than_the_transcript_holds_is_refused(self):
        episode, _ = self.simple_method_episode(scenario='notice-overcount')
        transcript = write_transcript(self.tmp / 'overcount.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo one'}), result_row('tu1'),
            tool_row('tu2', 'Bash', {'command': 'echo two'}, request_id='r2'), result_row('tu2'),
            tool_row('tu3', 'Bash', {'command': 'echo three'}, request_id='r3'), result_row('tu3'),
            text_row(request_id='r-final', text='All done.')])
        result = self.finish(episode, transcript, notice=2, expect=1)
        self.assertIn('the transcript holds 3 tool calls and the completion notice 2', result.stderr)
        self.assertFalse((episode / 'run.json').exists())
        self.assertFalse((episode / 'audit.json').exists())
        self.assertFalse((episode / 'sessions').exists())

    def test_a_matching_notice_records_as_completed(self):
        episode, _ = self.simple_method_episode(scenario='notice-match')
        transcript = write_transcript(self.tmp / 'match.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo one'}), result_row('tu1'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript)  # default: a completed notice carrying the transcript's own count
        run = load(episode / 'run.json')
        self.assertEqual(run['outcome'], 'completed')
        self.assertIsNone(run['sessions'][0]['error'])

    def test_a_transcript_ending_on_a_tool_result_is_refused(self):
        episode, _ = self.simple_method_episode(scenario='notice-midsession')
        transcript = write_transcript(self.tmp / 'midsession.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo hi'}), result_row('tu1')])
        result = self.finish(episode, transcript, expect=1)
        self.assertIn("the transcript does not end on the assistant's final message yet", result.stderr)
        self.assertFalse((episode / 'run.json').exists())
        self.assertFalse((episode / 'audit.json').exists())
        self.assertFalse((episode / 'sessions').exists())

    def test_missing_notice_status_is_a_usage_error(self):
        episode, _ = self.simple_method_episode(scenario='notice-missing-status')
        transcript = write_transcript(self.tmp / 'missing-status.jsonl', [text_row(text='All done.')])
        result = self.run_subagent('finish', '--episode', episode, '--transcript', transcript, '--model',
                                   'claude-haiku-4-5', '--started', '2026-09-25T00:00:00Z', '--finished',
                                   '2026-09-25T00:01:00Z')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('--notice-status', result.stderr)
        self.assertFalse((episode / 'run.json').exists())

    def test_completed_notice_without_a_count_is_a_usage_error(self):
        episode, _ = self.simple_method_episode(scenario='notice-completed-no-count')
        transcript = write_transcript(self.tmp / 'completed-no-count.jsonl', [text_row(text='All done.')])
        result = self.run_subagent('finish', '--episode', episode, '--transcript', transcript, '--model',
                                   'claude-haiku-4-5', '--started', '2026-09-25T00:00:00Z', '--finished',
                                   '2026-09-25T00:01:00Z', '--notice-status', 'completed')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('subagent: --notice-tool-calls is required with --notice-status completed', result.stderr)
        self.assertFalse((episode / 'run.json').exists())

    def test_failed_notice_with_a_count_is_a_usage_error(self):
        episode, _ = self.simple_method_episode(scenario='notice-failed-with-count')
        transcript = write_transcript(self.tmp / 'failed-with-count.jsonl', [text_row(text='All done.')])
        result = self.run_subagent('finish', '--episode', episode, '--transcript', transcript, '--model',
                                   'claude-haiku-4-5', '--started', '2026-09-25T00:00:00Z', '--finished',
                                   '2026-09-25T00:01:00Z', '--notice-status', 'failed', '--notice-tool-calls', '2')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('subagent: --notice-tool-calls is never given with --notice-status failed', result.stderr)
        self.assertFalse((episode / 'run.json').exists())

    def test_a_negative_notice_count_is_a_usage_error(self):
        episode, _ = self.simple_method_episode(scenario='notice-negative')
        transcript = write_transcript(self.tmp / 'negative.jsonl', [text_row(text='All done.')])
        result = self.finish(episode, transcript, notice=-1, expect=2)
        self.assertIn('subagent: --notice-tool-calls must be 0 or more', result.stderr)
        self.assertFalse((episode / 'run.json').exists())

    def test_a_session_finish_refuses_on_a_count_mismatch(self):
        episode, _ = self.routed_episode(scenario='notice-multisession')
        (episode / 'sessions' / '01').mkdir(parents=True)
        transcript = write_transcript(self.tmp / 'session2.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo hi'}), result_row('tu1'),
            handback_row('DONE'), result_row('tu-final'), text_row()])
        result = self.finish(episode, transcript, session=2, role='executor', tier='fast', notice=5, expect=1)
        self.assertIn('the transcript holds 2 tool calls and the completion notice 5', result.stderr)
        self.assertFalse((episode / 'sessions' / '02').exists())

    def test_a_duplicated_tool_id_counts_once_toward_the_notice(self):
        episode, _ = self.simple_method_episode(scenario='notice-duplicate')
        transcript = write_transcript(self.tmp / 'duplicate.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo partial'}, request_id='r1'),
            tool_row('tu1', 'Bash', {'command': 'echo partial and complete'}, request_id='r1'),
            result_row('tu1'),
            tool_row('tu2', 'Bash', {'command': 'echo other'}, request_id='r2'), result_row('tu2'),
            text_row(request_id='r-final', text='All done.')])
        self.finish(episode, transcript, notice=2, expect=0)
        run = load(episode / 'run.json')
        self.assertEqual(run['outcome'], 'completed')
        self.assertEqual(run['cost']['tool_calls'], 2)

    def test_an_unanswered_last_tool_call_is_refused(self):
        episode, _ = self.simple_method_episode(scenario='notice-unanswered')
        transcript = write_transcript(self.tmp / 'unanswered.jsonl', [
            tool_row('tu1', 'Bash', {'command': 'echo hi'}), result_row('tu1'), handback_row('DONE')])
        result = self.finish(episode, transcript, notice=2, expect=1)
        self.assertIn("the transcript's last tool call has no result yet", result.stderr)
        self.assertFalse((episode / 'run.json').exists())
        self.assertFalse((episode / 'audit.json').exists())
        self.assertFalse((episode / 'sessions').exists())

    def test_a_failed_notice_records_an_error_outcome(self):
        episode, _ = self.simple_method_episode(scenario='notice-failed')
        transcript = write_transcript(self.tmp / 'failed.jsonl', [text_row(text='All done.')])
        result = self.finish(episode, transcript, status='failed', expect=1)
        self.assertIn('outcome=error', result.stdout)
        run = load(episode / 'run.json')
        self.assertEqual(run['outcome'], 'error')
        self.assertEqual(run['sessions'][0]['error'], 'the host reported the session failed')


if __name__ == '__main__':
    unittest.main()
