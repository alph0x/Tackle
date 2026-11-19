import copy
import hashlib
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

    def test_protected_path_reads_and_inert_printed_filter(self):
        def call(command):
            return {'type': 'message', 'message': {'content': [
                {'type': 'toolCall', 'name': 'bash', 'arguments': {'command': command}}]}}

        protected = '/' + 'held' + 'out/'
        code, data = self.run_check([call("printf '%s' '" + protected + "'")])
        self.assertEqual(code, 0, data)
        for command in (
                "printf '%s\\n' '" + protected + "'",
                "printf '%s' '$HOME `literal` " + protected + "'",
                "printf '%s' '" + protected + "*'",
                "printf '%s' " + protected + "\\*"):
            with self.subTest(command=command):
                code, data = self.run_check([call(command)])
                self.assertEqual(code, 0, data)
        for name, arguments, expected in (
                ('glob', {'pattern': protected + '**'}, 1),
                ('find', {'pattern': protected + '**'}, 1),
                ('glob', {'unknown': protected + '**'}, 1),
                ('grep', {'pattern': protected + '.*', 'path': '/safe'}, 0),
                ('grep', {'pattern': 'safe', 'path': protected}, 1),
                ('grep', {'pattern': 'safe', 'path': '/safe;!' + protected}, 0)):
            with self.subTest(name=name, arguments=arguments):
                entry = {'type': 'message', 'message': {'content': [
                    {'type': 'toolCall', 'name': name, 'arguments': arguments}]}}
                code, data = self.run_check([entry])
                self.assertEqual(code, expected, data)
                if expected:
                    self.assertTrue(any(problem.startswith('forbidden path in ')
                                        for problem in data['problems']), data)
        for command in (
                'cat ' + protected + 'file',
                "printf -v 'a[$(cat " + protected + "file >&2)0]' '%s' safe",
                "printf '%n' 'a[$(cat " + protected + "file >&2)0]'",
                "printf '%s' " + protected + '*',
                "printf '%s' " + protected + '?',
                "printf '%s' " + protected + '[ab]',
                'printf "%s" "$(cat ' + protected + 'file)"',
                'printf "%s" safe < ' + protected + 'file',
                'printf "%s" safe; cat ' + protected + 'file'):
            with self.subTest(command=command):
                code, data = self.run_check([call(command)])
                self.assertEqual(code, 1, data)
                self.assertTrue(any(problem.startswith('forbidden path in ')
                                    for problem in data['problems']), data)

    def test_process_control_requires_sealed_ownership(self):
        def call(url):
            return {'type': 'message', 'message': {'content': [
                {'type': 'toolCall', 'name': 'write', 'arguments': {'path': url}}]}}

        receipt = {
            'schema': 'legacy-process-ownership-fixture/1',
            'creator_pid': 100,
            'child_pid': 101,
            'child_ppid': 100,
            'control_pid': 201,
            'control_ppid': 200,
            'supervisor_pid': 200,
            'provenance': 'synthetic fixture',
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'receipt.json'

            def check(url, proof=None, digest=None, include_proof=True):
                extra = ['--write-root', '/']
                if include_proof:
                    raw = json.dumps(proof).encode()
                    path.write_bytes(raw)
                    extra.extend(['--legacy-ownership-receipt', str(path),
                                  '--legacy-ownership-sha256',
                                  digest if digest is not None else hashlib.sha256(raw).hexdigest()])
                return self.run_check([call(url)], extra)

            code, data = check('proc://101/kill', include_proof=False)
            self.assertEqual(code, 1, data)
            code, data = check('proc://101/kill', receipt)
            self.assertEqual(code, 0, data)
            for url in ('proc://102/kill', 'proc://0/kill', 'proc://-1/kill',
                        'proc://true/kill', 'proc://101/other'):
                with self.subTest(url=url):
                    code, data = check(url, receipt)
                    self.assertEqual(code, 1, data)
            code, data = check('proc://101/kill', receipt, digest='0' * 64)
            self.assertNotEqual(code, 0, data)

            mutations = [
                ('child_ppid', 999),
                ('control_ppid', 999),
                ('control_pid', 101),
                ('supervisor_pid', 100),
                ('provenance', ''),
                ('child_pid', True),
                ('creator_pid', False),
                ('control_pid', 0),
                ('child_ppid', -1),
            ]
            for field, value in mutations:
                with self.subTest(field=field, value=value):
                    changed = copy.deepcopy(receipt)
                    changed[field] = value
                    code, data = check('proc://101/kill', changed)
                    self.assertNotEqual(code, 0, data)
            missing = copy.deepcopy(receipt)
            del missing['provenance']
            code, data = check('proc://101/kill', missing)
            self.assertNotEqual(code, 0, data)


THREAD, PARENT, TURN, ROOT = 'child', 'parent', 'turn', 'root-turn'
AGENT, CWD = '/root/reviewer', '/work'


def native_fixture(tier='priority'):
    settings = {
        'model': 'gpt-6.1-sol', 'reasoning_effort': 'high', 'service_tier': tier,
        'cwd': CWD,
        'collaboration_mode': {'settings': {'model': 'gpt-6.1-sol', 'reasoning_effort': 'high'}},
    }
    attribution = {
        'turn_id': TURN, 'root_turn_id': ROOT, 'parent_turn_id': ROOT,
        'initiating_agent_path': '/root',
    }
    final_text = 'Review mentions a tool and a forbidden operation without invoking either.'
    message = {
        'type': 'message', 'id': 'final', 'role': 'assistant', 'phase': 'final_answer',
        'status': 'completed', 'content': [{'type': 'output_text', 'text': final_text}],
        'internal_chat_message_metadata_passthrough': {'turn_id': TURN},
    }

    def initial(role, text):
        return {
            'type': 'message', 'role': role,
            'content': [{'type': 'input_text', 'text': text}],
            'internal_chat_message_metadata_passthrough': {'turn_id': TURN},
        }

    records = [
        ('session_meta', {
            'id': THREAD, 'parent_thread_id': PARENT, 'cwd': CWD, 'agent_path': AGENT,
            'thread_source': 'subagent',
            'source': {'subagent': {'thread_spawn': {
                'parent_thread_id': PARENT, 'agent_path': AGENT, 'depth': 1}}},
        }),
        ('event_msg', {'type': 'task_started', 'turn_id': TURN, 'root_turn_id': ROOT,
                       'turn_attribution': attribution}),
        ('turn_context', {
            'turn_id': TURN, 'root_turn_id': ROOT, 'cwd': CWD,
            'model': 'gpt-6.1-sol', 'effort': 'high',
            'collaboration_mode': {'settings': {'model': 'gpt-6.1-sol', 'reasoning_effort': 'high'}},
        }),
        ('event_msg', {'type': 'thread_settings_applied', 'thread_id': THREAD,
                       'thread_settings': settings}),
        ('response_item', initial('developer', 'Follow the review instructions.')),
        ('response_item', initial('user', 'Review the change.')),
        ('world_state', {
            'full': True,
            'state': {'model': {'model': 'gpt-6.1-sol'},
                      'collaboration_mode': {'model': 'gpt-6.1-sol'}},
        }),
        ('response_item', {
            'type': 'agent_message', 'author': '/root', 'recipient': AGENT,
            'content': [{'type': 'input_text', 'text': 'Review.'}],
            'internal_chat_message_metadata_passthrough': {'turn_id': TURN},
        }),
        ('event_msg', {
            'type': 'item_completed', 'thread_id': THREAD, 'turn_id': TURN,
            'item': {'type': 'AgentMessage', 'id': 'final', 'phase': 'final_answer',
                     'content': [{'type': 'Text', 'text': final_text}]},
        }),
        ('response_item', message),
        ('event_msg', {'type': 'task_complete', 'turn_id': TURN, 'root_turn_id': ROOT,
                       'last_agent_message': final_text}),
    ]
    return [{'ordinal': index, 'timestamp': '2026-01-01T00:00:00Z',
             'type': kind, 'payload': payload}
            for index, (kind, payload) in enumerate(records)]


def deferred_namespace_fixture():
    return [
        {
            'type': 'response_item', 'timestamp': '2026-01-01T00:00:00Z',
            'payload': {
                'id': 'deferred-namespace-fixture',
                'type': 'message', 'role': 'developer',
                'content': [{
                    'type': 'input_text',
                    'text': '<tools>\nAdded deferred tool namespaces:\n- mcp__fixture_tools\n</tools>',
                }],
                'internal_chat_message_metadata_passthrough': {
                    'turn_id': TURN, 'create_time': 1,
                    'content_item_kinds': ['tools.deferred_namespaces'],
                    'content_item_metadata': [
                        {'provenance': {'type': 'tool', 'namespace': 'tool_search'}},
                    ],
                },
            },
        },
        {
            'type': 'world_state', 'timestamp': '2026-01-01T00:00:00Z',
            'payload': {'full': False, 'state': {'tools': {'mcp__fixture_tools': ''}}},
        },
    ]


class NativeControls(unittest.TestCase):
    """Verify the pinned, complete, tool-free direct-child review decision."""

    def record(self, entries, kind, payload_type=None, role=None):
        matches = [entry for entry in entries
                   if entry['type'] == kind
                   and (payload_type is None or entry['payload'].get('type') == payload_type)
                   and (role is None or entry['payload'].get('role') == role)]
        self.assertEqual(len(matches), 1, (kind, payload_type, role, matches))
        return matches[0]

    def check(self, entries, expected, tier='priority', digest=None, raw_suffix=b'', agent=AGENT):
        for index, entry in enumerate(entries):
            entry['ordinal'] = index
        raw = b''.join((json.dumps(entry) + '\n').encode() for entry in entries) + raw_suffix
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'rollout.jsonl'
            path.write_bytes(raw)
            command = [
                sys.executable, '-I', '-B', str(SCRIPT), str(path), '--native',
                '--model', 'gpt-6.1-sol', '--effort', 'high', '--agent', agent,
                '--thread', THREAD, '--parent', PARENT, '--cwd', CWD, '--tier', tier,
                '--sha256', digest if digest is not None else hashlib.sha256(raw).hexdigest(),
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, (result.stdout, result.stderr))
            return json.loads(result.stdout)

    def test_tool_free_quoted_text_and_supported_tiers(self):
        import runpy
        literal_print = runpy.run_path(
            str(SCRIPT)
        )['legacy_literal_print']
        for command in (
                "printf '%s' 'literal $text * `text`'",
                r"printf '%s\n' 'hello'",
                "printf '%%n' 'a[$(printf marker)0]'",
                "printf '%10.3s' hello"):
            with self.subTest(literal_print=command):
                self.assertTrue(literal_print(command))
        for command in (
                "printf '%n' 'a[$(printf marker)0]'",
                "printf '%1$n' target",
                "printf '%*s' 2 hello",
                "printf '%.*s' 2 hello",
                "printf '%s' \"$value\"",
                "printf '%s' *.txt",
                "printf -v target '%s' hello"):
            with self.subTest(nonliteral_or_unsafe_print=command):
                self.assertFalse(literal_print(command))
        for tier in ('default', 'priority'):
            with self.subTest(tier=tier):
                self.assertEqual(self.check(native_fixture(tier), 0, tier=tier)['problems'], [])
                entries = native_fixture(tier)
                dispatch = self.record(entries, 'response_item', 'agent_message')
                entries[entries.index(dispatch) + 1:entries.index(dispatch) + 1] = deferred_namespace_fixture()
                self.assertEqual(self.check(entries, 0, tier=tier)['problems'], [])
                entries = native_fixture(tier)
                initial = self.record(entries, 'response_item', 'message', 'developer')
                initial['payload']['internal_chat_message_metadata_passthrough']['content_item_kinds'] = [
                    'generic.developer_instructions', 'tools.deferred_namespaces'
                ]
                initial['payload']['content'].append({
                    'type': 'input_text', 'text': '<tools>\nInitial tools\n</tools>',
                })
                dispatch = self.record(entries, 'response_item', 'agent_message')
                entries[entries.index(dispatch) + 1:entries.index(dispatch) + 1] = deferred_namespace_fixture()
                self.assertEqual(self.check(entries, 0, tier=tier)['problems'], [])
                entries = native_fixture(tier)
                item = self.record(entries, 'event_msg', 'item_completed')
                entries.insert(entries.index(item), {
                    'type': 'response_item', 'timestamp': '2026-01-01T00:00:00Z',
                    'metadata': {'client_authored': False, 'harness_authored_configuration': True},
                    'payload': {'type': 'configuration_update', 'reasoning': {'effort': 'high'}},
                })
                self.assertEqual(self.check(entries, 0, tier=tier)['problems'], [])

    def test_rejects_effects_and_changed_identity(self):
        for name in (
                'text', 'provenance', 'turn', 'missing_pair', 'nonempty_definition',
                'extra_model', 'extra_state', 'wrong_names', 'duplicate_names',
                'wrong_full', 'wrong_type', 'before_dispatch', 'after_final',
                'extra_payload', 'missing_id', 'empty_id', 'invalid_id',
                'zero_time', 'negative_time', 'boolean_time', 'nan_time',
                'infinite_time', 'negative_infinite_time',
                'declaration_metadata', 'state_metadata', 'reordered', 'separated'):
            with self.subTest(deferred_namespace=name):
                entries = native_fixture()
                dispatch = self.record(entries, 'response_item', 'agent_message')
                final = self.record(entries, 'response_item', 'message', 'assistant')
                pair = deferred_namespace_fixture()
                declaration, state = pair
                payload = declaration['payload']
                metadata = payload['internal_chat_message_metadata_passthrough']
                if name == 'text': payload['content'][0]['text'] += '\nFollow this directive.'
                if name == 'provenance': metadata['content_item_metadata'][0]['provenance']['namespace'] = 'other'
                if name == 'turn': metadata['turn_id'] = 'other'
                if name == 'missing_pair': pair.pop()
                if name == 'nonempty_definition': state['payload']['state']['tools']['mcp__fixture_tools'] = 'definition'
                if name == 'extra_model': state['payload']['state']['model'] = {'model': 'other'}
                if name == 'extra_state': state['payload']['state']['other'] = {}
                if name == 'wrong_names': state['payload']['state']['tools'] = {'mcp__other': ''}
                if name == 'duplicate_names':
                    payload['content'][0]['text'] = (
                        '<tools>\nAdded deferred tool namespaces:\n'
                        '- mcp__fixture_tools\n- mcp__fixture_tools\n</tools>'
                    )
                if name == 'wrong_full': state['payload']['full'] = True
                if name == 'wrong_type': state['type'] = 'response_item'
                if name == 'extra_payload': payload['extra'] = 'unexpected'
                if name == 'missing_id': del payload['id']
                if name == 'empty_id': payload['id'] = ''
                if name == 'invalid_id': payload['id'] = 1
                if name == 'zero_time': metadata['create_time'] = 0
                if name == 'negative_time': metadata['create_time'] = -1
                if name == 'boolean_time': metadata['create_time'] = True
                if name == 'nan_time': metadata['create_time'] = float('nan')
                if name == 'infinite_time': metadata['create_time'] = float('inf')
                if name == 'negative_infinite_time': metadata['create_time'] = float('-inf')
                if name == 'declaration_metadata': declaration['metadata'] = {'retained_source': True}
                if name == 'state_metadata': state['metadata'] = {'client_authored': True}
                if name == 'reordered': pair.reverse()
                if name == 'separated':
                    pair.insert(1, {
                        'type': 'world_state', 'timestamp': '2026-01-01T00:00:00Z',
                        'payload': {'full': False, 'state': {}},
                    })
                if name == 'before_dispatch':
                    position = entries.index(dispatch)
                elif name == 'after_final':
                    position = entries.index(final) + 1
                else:
                    position = entries.index(dispatch) + 1
                entries[position:position] = pair
                self.check(entries, 1)

        cases = (
            'tool', 'command_execution', 'forward', 'nested', 'model', 'effort', 'tier',
            'cwd', 'thread', 'parent', 'terminal', 'unknown_payload', 'unknown_setting',
            'unknown_event', 'missing_settings', 'second_turn', 'after_terminal',
            'bad_final', 'world_model', 'world_collaboration_model', 'context_model',
            'context_effort', 'item_final',
        )
        for name in cases:
            with self.subTest(name=name):
                entries = native_fixture()
                meta = self.record(entries, 'session_meta')['payload']
                started = self.record(entries, 'event_msg', 'task_started')
                context = self.record(entries, 'turn_context')['payload']
                settings = self.record(entries, 'event_msg', 'thread_settings_applied')
                dispatch = self.record(entries, 'response_item', 'agent_message')
                item = self.record(entries, 'event_msg', 'item_completed')
                final = self.record(entries, 'response_item', 'message', 'assistant')
                world = self.record(entries, 'world_state')['payload']
                terminal = self.record(entries, 'event_msg', 'task_complete')
                if name == 'tool':
                    entries.insert(entries.index(dispatch), {
                        'type': 'response_item', 'timestamp': '2026-01-01T00:00:00Z',
                        'payload': {'type': 'custom_tool_call', 'name': 'functions.exec', 'input': 'safe'},
                    })
                if name == 'command_execution': item['payload']['item']['type'] = 'CommandExecution'
                if name == 'forward': dispatch['payload']['author'] = '/root/other'
                if name == 'nested': meta['source']['subagent']['thread_spawn']['depth'] = 2
                if name == 'model': context['model'] = 'other'
                if name == 'effort': settings['payload']['thread_settings']['reasoning_effort'] = 'low'
                if name == 'tier': settings['payload']['thread_settings']['service_tier'] = 'other'
                if name == 'cwd': meta['cwd'] = '/elsewhere'
                if name == 'thread': settings['payload']['thread_id'] = 'other'
                if name == 'parent': meta['parent_thread_id'] = 'other'
                if name == 'terminal': terminal['payload']['turn_id'] = 'other'
                if name == 'unknown_payload': final['payload']['tool_call'] = {'name': 'tool'}
                if name == 'unknown_setting': settings['payload']['thread_settings']['new_effect'] = 'unknown'
                if name == 'unknown_event':
                    entries.insert(entries.index(dispatch), {
                        'type': 'event_msg', 'timestamp': '2026-01-01T00:00:00Z',
                        'payload': {'type': 'new_effect'},
                    })
                if name == 'missing_settings': entries.remove(settings)
                if name == 'second_turn': entries.insert(entries.index(context) if context in entries else 2, copy.deepcopy(started))
                if name == 'after_terminal': entries.append(copy.deepcopy(item))
                if name == 'bad_final': terminal['payload']['last_agent_message'] = 'other'
                if name == 'world_model': world['state']['model']['model'] = 'other'
                if name == 'world_collaboration_model': world['state']['collaboration_mode']['model'] = 'other'
                if name == 'context_model': context['collaboration_mode']['settings']['model'] = 'other'
                if name == 'context_effort': context['collaboration_mode']['settings']['reasoning_effort'] = 'low'
                if name == 'item_final': item['payload']['item']['content'][0]['text'] = 'other'
                self.check(entries, 1)

        entries = native_fixture()
        meta = self.record(entries, 'session_meta')['payload']
        meta['agent_path'] = '/root/other'
        meta['source']['subagent']['thread_spawn']['agent_path'] = '/root/other'
        self.record(entries, 'response_item', 'agent_message')['payload']['recipient'] = '/root/other'
        self.check(entries, 1)
        self.assertEqual(self.check(entries, 0, agent='/root/other')['problems'], [])

        for name, expected in (
                ('effort', 1), ('missing_provenance', 1), ('false_provenance', 2),
                ('unknown_metadata', 2), ('unknown_payload', 1), ('unknown_reasoning', 1),
                ('before_dispatch', 1), ('after_final', 1), ('after_terminal', 1)):
            with self.subTest(configuration_update=name):
                entries = native_fixture()
                dispatch = self.record(entries, 'response_item', 'agent_message')
                item = self.record(entries, 'event_msg', 'item_completed')
                final = self.record(entries, 'response_item', 'message', 'assistant')
                terminal = self.record(entries, 'event_msg', 'task_complete')
                update = {
                    'type': 'response_item', 'timestamp': '2026-01-01T00:00:00Z',
                    'metadata': {'client_authored': False, 'harness_authored_configuration': True},
                    'payload': {'type': 'configuration_update', 'reasoning': {'effort': 'high'}},
                }
                if name == 'effort': update['payload']['reasoning']['effort'] = 'low'
                if name == 'missing_provenance': update['metadata'] = {}
                if name == 'false_provenance': update['metadata']['harness_authored_configuration'] = False
                if name == 'unknown_metadata': update['metadata']['extra'] = True
                if name == 'unknown_payload': update['payload']['extra'] = True
                if name == 'unknown_reasoning': update['payload']['reasoning']['extra'] = True
                if name == 'before_dispatch':
                    entries.insert(entries.index(dispatch), update)
                elif name == 'after_final':
                    entries.insert(entries.index(final) + 1, update)
                elif name == 'after_terminal':
                    entries.insert(entries.index(terminal) + 1, update)
                else:
                    entries.insert(entries.index(item), update)
                self.check(entries, expected)

    def test_raw_integrity_and_truncation(self):
        self.check(native_fixture(), 2, digest='0' * 64)
        entries = native_fixture()
        entries.remove(self.record(entries, 'event_msg', 'task_complete'))
        self.check(entries, 1)
        self.check(native_fixture(), 2, raw_suffix=b'{')
