"""Host adapters for the protocol v2 harness: argv construction and output parsing. Nothing here starts a process.

``build(prompt, session, model, effort, home, work, broker=None) -> (argv, env)``: argv starts with a bare
command name resolved through the participant's PATH; env holds only the adapter's own variables (the broker
base URL and the per-episode dummy token), which the harness adds to its allowlist. A real adapter never
receives a credential: ``broker`` carries only the broker URL and the dummy token.
``parse(stdout) -> {tokens_in, tokens_out, tool_calls, session_id, skill_loaded}``, with ``'n/a'`` wherever the
output does not state a value (unknown is never 0).

The real adapters' flags come from `codex exec --help` (codex-cli 0.155.1) and `claude --help` (Claude Code
2.1.150), probed at T-05 preflight; their real output formats and triggering stay unobserved until an
authorized smoke episode (T-08 preflight).
"""
import json
import uuid
from pathlib import Path

import usage

NA = 'n/a'
# The single-entry container flags, restated (D-56), plus the episode network and a non-root user.
CONTAINER_FLAGS = ('--rm', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp')
CONTAINER_WORK, CONTAINER_HOME, CONTAINER_BIN = '/episode/work', '/episode/home', '/episode/bin'
CONTAINER_PATH = CONTAINER_BIN + ':/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'


def count(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else NA


def events(stdout):
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            yield event


class Fake:
    """The scripted ``fake-agent`` (fake_agent.py); local isolation or a fake docker only."""
    name, real, skill_dir = 'fake', False, '.fake/skills'
    capture_path = 'fake-agent result events on stdout'

    def build(self, prompt, session, model, effort, home, work, broker=None):
        return ['fake-agent', '--session', str(session), '--model', model, '--effort', effort, '--skills',
                self.skill_dir, prompt], {}

    def parse(self, stdout):
        found = list(events(stdout))
        result = next((e for e in reversed(found) if e.get('type') == 'result'), None)
        spent = (result or {}).get('usage') or {}
        loaded = any(e.get('type') == 'skill' for e in found)
        return {'tokens_in': count(spent.get('input_tokens')), 'tokens_out': count(spent.get('output_tokens')),
                'tool_calls': sum(e.get('type') == 'tool' for e in found) if result else NA,
                'session_id': (result or {}).get('session_id') or NA,
                'skill_loaded': True if loaded else (False if result else NA)}


class Codex:
    """`codex exec --json`; the broker is a provider override whose key variable holds the dummy token."""
    name, real, skill_dir = 'codex', True, '.agents/skills'
    upstream = 'https://api.openai.com'
    token_header, token_prefix = 'authorization', 'Bearer '
    credential_header, credential_prefix = 'authorization', 'Bearer '
    token_variable = 'BROKER_TOKEN'
    capture_path = 'codex exec --json turn.completed usage'
    EFFORTS = {'low': 'low', 'medium': 'medium', 'high': 'high', 'max': 'xhigh'}
    TOOL_ITEMS = ('command_execution', 'file_change', 'mcp_tool_call', 'web_search')

    def build(self, prompt, session, model, effort, home, work, broker=None):
        argv = ['codex', 'exec', '--json', '--skip-git-repo-check', '--ignore-user-config', '--ephemeral',
                '--sandbox', 'workspace-write', '-C', str(work)]
        if model != NA:
            argv += ['-m', model]
        if effort != NA:
            argv += ['-c', 'model_reasoning_effort="%s"' % self.EFFORTS.get(effort, effort)]
        env = {}
        if broker:
            argv += ['-c', 'model_provider="broker"', '-c', 'model_providers.broker.name="broker"',
                     '-c', 'model_providers.broker.base_url="%s/v1"' % broker['url'],
                     '-c', 'model_providers.broker.env_key="%s"' % self.token_variable,
                     '-c', 'model_providers.broker.wire_api="responses"']
            env[self.token_variable] = broker['token']
        return argv + [prompt], env

    def parse(self, stdout):
        found = list(events(stdout))
        turns = usage.codex_turns(stdout)
        completed = any(e.get('type') == 'turn.completed' for e in found)
        loaded = any('skills/tackle/SKILL.md' in line for line in stdout.decode('utf-8', 'replace').splitlines())
        tools = sum(1 for e in found if e.get('type') == 'item.completed'
                    and (e.get('item') or {}).get('type') in self.TOOL_ITEMS)
        return {'tokens_in': turns['tokens_in'], 'tokens_out': turns['tokens_out'],
                'tool_calls': tools if completed else NA, 'session_id': turns.get('thread_id') or NA,
                'skill_loaded': True if loaded else (False if completed else NA)}


class ClaudeCode:
    """`claude -p --output-format stream-json`; the broker is a gateway base URL with a dummy bearer token."""
    name, real, skill_dir = 'claude-code', True, '.claude/skills'
    upstream = 'https://api.anthropic.com'
    token_header, token_prefix = 'authorization', 'Bearer '
    credential_header, credential_prefix = 'x-api-key', ''
    capture_path = 'claude-code session transcripts under the episode HOME (requestId dedup), else result events'

    def build(self, prompt, session, model, effort, home, work, broker=None):
        argv = ['claude', '-p', prompt, '--output-format', 'stream-json', '--verbose', '--session-id',
                str(uuid.uuid4()), '--permission-mode', 'bypassPermissions']
        if model != NA:
            argv += ['--model', model]
        if effort != NA:
            argv += ['--effort', effort]
        env = {'ANTHROPIC_BASE_URL': broker['url'], 'ANTHROPIC_AUTH_TOKEN': broker['token']} if broker else {}
        return argv, env

    @staticmethod
    def skill_use(block):
        text = json.dumps(block.get('input') or {})
        return (block.get('name') == 'Skill' and 'tackle' in text) or 'skills/tackle/' in text

    def parse(self, stdout):
        found = list(events(stdout))
        result = usage.claude_code_result(stdout)
        done = any(e.get('type') == 'result' for e in found)
        tools, loaded = 0, False
        for event in found:
            if event.get('type') != 'assistant':
                continue
            for block in (event.get('message') or {}).get('content') or []:
                if isinstance(block, dict) and block.get('type') == 'tool_use':
                    tools += 1
                    loaded = loaded or self.skill_use(block)
        session = result.get('session_id')
        if session in (None, NA):
            session = next((e['session_id'] for e in found if e.get('session_id')), NA)
        return {'tokens_in': result['tokens_in'], 'tokens_out': result['tokens_out'],
                'tool_calls': tools if done else NA, 'session_id': session,
                'skill_loaded': True if loaded else (False if done else NA)}


ADAPTERS = {'fake': Fake(), 'codex': Codex(), 'claude-code': ClaudeCode()}


def container_argv(inner, env, episode, image, network, name=None, user=None):
    """`docker run` with the restated isolation flags, one network, and only the episode's work, home and bin."""
    argv = ['docker', 'run'] + list(CONTAINER_FLAGS) + ['--network', network]
    if name:
        argv += ['--name', name]
    if user:
        argv += ['--user', user]
    for sub, target, mode in (('work', CONTAINER_WORK, ''), ('home', CONTAINER_HOME, ''), ('bin', CONTAINER_BIN, ',readonly')):
        argv += ['--mount', 'type=bind,src=%s,dst=%s%s' % (Path(episode, sub).resolve(), target, mode)]
    argv += ['--workdir', CONTAINER_WORK]
    for key in sorted(env):
        argv += ['-e', '%s=%s' % (key, env[key])]
    return argv + [image] + list(inner)
