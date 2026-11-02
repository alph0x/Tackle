import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[5] / 'maintaining/role_session_check.py'


class RoleChecks(unittest.TestCase):
    def run_check(self, additions=(), extra=()):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [{'type': 'session', 'cwd': tmp},
                       {'type': 'session_init', 'agent': 'executor', 'resolvedModel': 'provider/model:high'},
                       {'type': 'model_change', 'model': 'provider/model'},
                       {'type': 'thinking_level_change', 'thinkingLevel': 'high'}]
            entries.extend(additions)
            path = Path(tmp) / 'transcript'
            path.write_text(''.join(json.dumps(e) + '\n' for e in entries))
            result = subprocess.run([sys.executable, '-I', '-B', str(SCRIPT), str(path), '--model', 'provider/model', '--effort', 'high', '--agent', 'executor', '--write-root', tmp, *extra], capture_output=True, text=True)
            return result.returncode, json.loads(result.stdout)

    def test_clean(self):
        code, data = self.run_check()
        self.assertEqual(code, 0)
        self.assertEqual(data['problems'], [])

    def test_fallback_is_refused(self):
        code, data = self.run_check([{'type': 'model_change', 'model': 'provider/model', 'resolvedModelIsFallback': True}])
        self.assertEqual(code, 1)
        self.assertTrue(any(p.startswith('fallback model') for p in data['problems']))

    def test_forwarding_and_network(self):
        call = lambda name: {'type': 'message', 'message': {'content': [{'type': 'toolCall', 'name': name, 'arguments': {}}]}}
        code, data = self.run_check([call('find')], ['--forbid-forwarding'])
        self.assertEqual(code, 1)
        self.assertEqual(data['forwarded'], 1)
        code, data = self.run_check([call('web_search')])
        self.assertEqual(code, 1)
        self.assertIn('network tool: web_search', data['problems'])

    def test_model_agent_and_effort_mismatches(self):
        cases = [
            ({'type': 'model_change', 'model': 'other/model'}, 'model '),
            ({'type': 'thinking_level_change', 'thinkingLevel': 'low'}, 'effort '),
            ({'type': 'session_init', 'agent': 'reviewer', 'resolvedModel': 'other/model:low'}, 'agent '),
            ({'type': 'session_init', 'agent': 'executor', 'resolvedModel': 'other/model:high'}, 'resolved model '),
            ({'type': 'message', 'message': {'role': 'assistant', 'provider': 'other', 'model': 'model'}}, 'assistant turn on '),
        ]
        for entry, prefix in cases:
            with self.subTest(prefix=prefix):
                code, data = self.run_check([entry])
                self.assertEqual(code, 1)
                self.assertTrue(any(p.startswith(prefix) for p in data['problems']), data)

    def test_forbidden_tools_paths_and_network(self):
        def call(name, arguments):
            return {'type': 'message', 'message': {'content': [{'type': 'toolCall', 'name': name, 'arguments': arguments}]}}
        blocked_paths = ['/' + 'held' + 'out/file', 'variants/' + 'h' + '1/file',
                         '.' + 'tackle/' + 'secrets', '.' + 'codex/' + 'auth.json']
        for path in blocked_paths:
            code, data = self.run_check([call('read', {'path': path})])
            self.assertEqual(code, 1)
            self.assertTrue(any(p.startswith('forbidden path in ') for p in data['problems']))
        code, data = self.run_check([call('grep', {'path': '!/' + 'held' + 'out'})])
        self.assertEqual(code, 0, data)
        for name, args, prefix in [
                ('graft_query', {}, 'graft tool call'),
                ('task', {}, 'forbidden tool: '),
                ('eval', {}, 'forbidden tool: '),
                ('bash', {'command': 'graft query'}, 'graft command'),
                ('bash', {'command': 'git -C dir fetch origin'}, 'network command'),
                ('bash', {'command': 'curl example.invalid'}, 'network command'),
                ('read', {'path': 'https://example.invalid/'}, 'network read in ')]:
            with self.subTest(name=name, args=args):
                code, data = self.run_check([call(name, args)])
                self.assertEqual(code, 1)
                self.assertTrue(any(p.startswith(prefix) for p in data['problems']), data)

    def test_write_targets_and_forwarding(self):
        def call(name, arguments):
            return {'type': 'message', 'message': {'content': [{'type': 'toolCall', 'name': name, 'arguments': arguments}]}}
        clean = [call('write', {'path': 'inside.txt'}), call('write', {'path': 'agent://coordinator'}),
                 call('edit', {'input': '[inside.txt#ABCD]\nMV renamed.txt\n'})]
        code, data = self.run_check(clean)
        self.assertEqual(code, 0, data)
        for name, args, prefix in [
                ('write', {'path': '../escape'}, 'write outside the write roots'),
                ('write', {'path': 'local://example'}, 'write to an internal URL'),
                ('edit', {'input': 'invalid'}, 'edit without a parsable target path'),
                ('edit', {'input': '[inside.txt#ABCD]\nMV ../escape\n'}, 'edit outside the write roots')]:
            code, data = self.run_check([call(name, args)])
            self.assertEqual(code, 1)
            self.assertTrue(any(p.startswith(prefix) for p in data['problems']), data)
        code, data = self.run_check([call('find', {'path': '.'})])
        self.assertEqual(code, 0, data)
        self.assertEqual(data['forwarded'], 1)

    def test_malformed_transcript_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'transcript'
            for text in ('not json\n', '{}\n'):
                path.write_text(text)
                result = subprocess.run([sys.executable, '-I', '-B', str(SCRIPT), str(path),
                                         '--model', 'provider/model', '--effort', 'high', '--agent', 'executor'],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn('error', json.loads(result.stdout))

    def test_relative_target_without_cwd_is_refused(self):
        entries = [{'type': 'session'}, {'type': 'session_init', 'agent': 'executor', 'resolvedModel': 'provider/model:high'},
                   {'type': 'model_change', 'model': 'provider/model'},
                   {'type': 'thinking_level_change', 'thinkingLevel': 'high'},
                   {'type': 'message', 'message': {'content': [{'type': 'toolCall', 'name': 'write',
                                                                 'arguments': {'path': 'relative'}}]}}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'transcript'
            path.write_text(''.join(json.dumps(entry) + '\n' for entry in entries))
            result = subprocess.run([sys.executable, '-I', '-B', str(SCRIPT), str(path),
                                     '--model', 'provider/model', '--effort', 'high', '--agent', 'executor',
                                     '--write-root', directory], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertTrue(any(p.startswith('write with a relative path and no session cwd')
                                for p in json.loads(result.stdout)['problems']))

    def test_source_payload_is_not_a_path_access(self):
        path = '/' + 'held' + 'out/example'
        def call(name, arguments):
            return {'type': 'message', 'message': {'content': [{'type': 'toolCall', 'name': name, 'arguments': arguments}]}}
        code, data = self.run_check([
            call('write', {'path': 'checker.py', 'content': 'pattern = ' + repr(path)}),
            call('edit', {'input': '[checker.py#ABCD]\nPUT >1:\n+pattern = ' + repr(path) + '\n'})])
        self.assertEqual(code, 0, data)
        for name, arguments in (
                ('write', {'path': path, 'content': 'text'}),
                ('edit', {'input': '[' + path + '#ABCD]\nPUT >1:\n+text\n'}),
                ('bash', {'command': 'cat ' + path}),
                ('read', {'path': path})):
            code, data = self.run_check([call(name, arguments)])
            self.assertEqual(code, 1, data)
            self.assertTrue(any(problem.startswith('forbidden path in ') for problem in data['problems']), data)

    def test_shell_executable_spelling_and_boundaries(self):
        def call(command):
            return {'type': 'message', 'message': {'content': [{'type': 'toolCall', 'name': 'bash',
                                                                 'arguments': {'command': command}}]}}
        blocked = [
            ('/usr/bin/curl example.invalid', 'network command'),
            ('"curl" example.invalid', 'network command'),
            ('env MODE=quiet "/usr/bin/wget" example.invalid', 'network command'),
            ('MODE=quiet /usr/bin/ssh example.invalid', 'network command'),
            ('printf ok; "/usr/bin/nc" example.invalid', 'network command'),
            ('/usr/local/bin/graft query', 'graft command'),
            ('"graft" query', 'graft command'),
            ('env MODE=quiet "/some path/graft" query', 'graft command'),
        ]
        blocked += [('git -C "dir with spaces" ' + verb + ' origin', 'network command')
                    for verb in ('push', 'fetch', 'pull', 'clone')]
        for command, prefix in blocked:
            with self.subTest(command=command):
                code, data = self.run_check([call(command)])
                self.assertEqual(code, 1, data)
                self.assertTrue(any(problem.startswith(prefix) for problem in data['problems']), data)
        for command in ('printf "%s\\n" "curl graft git fetch"', 'git -C "dir with spaces" status',
                        'env MODE=quiet "/bin/echo" "curl"', 'printf ok | "/bin/cat"'):
            with self.subTest(command=command):
                code, data = self.run_check([call(command)])
                self.assertEqual(code, 0, data)

    def test_redirects_and_quoted_shell_data(self):
        def call(command):
            return {'type': 'message', 'message': {'content': [{'type': 'toolCall', 'name': 'bash',
                                                                 'arguments': {'command': command}}]}}
        blocked = [
            ('> output.log curl example.invalid', 'network command'),
            ('> output.log graft query', 'graft command'),
            ('2> "output log" "/usr/bin/curl" example.invalid', 'network command'),
            ('1>output.log "/usr/local/bin/graft" query', 'graft command'),
            ('env MODE=quiet 2>output.log "curl" example.invalid', 'network command'),
            ('printf ok; >output.log "graft" query', 'graft command'),
            ('2>&1 git -C "dir with spaces" fetch origin', 'network command'),
        ]
        for command, prefix in blocked:
            with self.subTest(command=command):
                code, data = self.run_check([call(command)])
                self.assertEqual(code, 1, data)
                self.assertTrue(any(problem.startswith(prefix) for problem in data['problems']), data)
        valid = [
            'printf "%s\\n" ";" "curl"',
            'printf "%s\\n" "" "graft"',
            'printf "%s\\n" ";" "" "/usr/bin/curl"',
            '2>output.log printf "%s" "graft"',
            """python3 -c 'commands=["/usr/bin/curl example.invalid", "graft query", "git fetch"]; print(commands)'""",
        ]
        for command in valid:
            with self.subTest(command=command):
                code, data = self.run_check([call(command)])
                self.assertEqual(code, 0, data)

    def test_shell_line_continuations(self):
        def call(command):
            return {'type': 'message', 'message': {'content': [{'type': 'toolCall', 'name': 'bash',
                                                                 'arguments': {'command': command}}]}}
        continuation = '\\' + '\n'
        blocked = [
            ('cu' + continuation + 'rl example.invalid', 'network command'),
            ('"cu' + continuation + 'rl" example.invalid', 'network command'),
            ('/usr/bin/cu' + continuation + '"rl" example.invalid', 'network command'),
            ('env MODE=quiet >output.log command -- ex' + continuation + 'ec "gra' + continuation + 'ft" query', 'graft command'),
            ('git -C "dir' + continuation + ' with spaces" fet' + continuation + 'ch origin', 'network command'),
            ('# comment ' + continuation + 'curl example.invalid', 'network command'),
            ('# comment ' + continuation + 'graft query', 'graft command'),
            ('printf ok # comment ' + continuation + 'git fetch origin', 'network command'),
            ('# " comment ' + continuation + '"/usr/bin/curl" example.invalid', 'network command'),
            ("# ' comment " + continuation + 'env MODE=quiet >output.log command -- exec "gra' + continuation + 'ft" query', 'graft command'),
            ('printf ok;# comment ' + continuation + 'curl example.invalid', 'network command'),
            ('printf word#data ' + continuation + '; curl example.invalid', 'network command'),
            ('printf \\#data ' + continuation + '; graft query', 'graft command'),
        ]
        for command, prefix in blocked:
            with self.subTest(command=command):
                code, data = self.run_check([call(command)])
                self.assertEqual(code, 1, data)
                self.assertTrue(any(problem.startswith(prefix) for problem in data['problems']), data)
        valid = [
            'python3 ' + continuation + ' -I -B -c "print(1)"',
            'printf "%s\\n" ' + continuation + ' ";" "" "curl"',
            'printf "%s" "cu' + continuation + 'rl"',
            "'cu" + continuation + "rl' example.invalid",
            "python3 -c 'value = \"cu" + continuation + "rl\"; print(value)'",
            '2>output.log git -C "dir with spaces" ' + continuation + ' status',
            "# ' comment\nprintf " + continuation + '"%s" "safe"',
            '# " comment\nprintf ' + continuation + '"%s" "safe"',
            'printf "%s" "# curl" word#data \\#escaped',
            'printf "%s" "quoted#' + continuation + 'data"',
            '# curl graft git fetch ' + continuation,
        ]
        for command in valid:
            with self.subTest(command=command):
                code, data = self.run_check([call(command)])
                self.assertEqual(code, 0, data)
        code, data = self.run_check([call('python3 "unterminated')])
        self.assertEqual(code, 1, data)
        self.assertTrue(any(problem.startswith('network command') for problem in data['problems']), data)
