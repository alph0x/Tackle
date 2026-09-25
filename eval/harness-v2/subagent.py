"""The subagent-episode tool: prints a staged episode's prompt for a Claude Code subagent dispatch, and
turns the subagent's own transcript into a harness.py-shaped run.json plus an audit.json.

Usage: python3 eval/harness-v2/subagent.py prompt --episode <dir>
       python3 eval/harness-v2/subagent.py finish --episode <dir> --transcript <subagent jsonl> \
           --model <id> --started <utc> --finished <utc>
Exit 0 success, 1 refusal, 2 usage error. Standard library only.

Unlike harness.py's own ``run``, this tool starts no process: an episode staged by ``harness.py stage``
is dispatched as a Task-tool subagent of the coordinating session (D-87), and ``finish`` is handed that
subagent's own session transcript (JSONL, the same event shape ``usage.claude_code_transcript`` reads)
after the fact. ``finish`` writes exactly one session under ``sessions/01/`` because one transcript is
one session: a multi-prompt episode (``stage.json`` listing more than one ``prompts`` entry) is refused.

``run.json`` matches harness.py's own schema (schema, adapter, isolation, outcome, exit, timeout, signal,
sessions, transcript_sha256, skill_loaded, executor, roles, cost, capture_path, model_binding,
started_at, finished_at) so that ``harness.py record`` and ``judge.py --episode`` consume it unchanged.
Two fields mark this as a different execution path from a headless CLI session: ``adapter`` is
``"subagent"`` (not ``"claude-code"``), and ``executor.harness`` is ``"claude-code-subagent"``.
judge.py selects its correction-cycle parser by the ``adapter`` field and maps ``"subagent"`` to its
Claude Code parser, because ``sessions/01/stdout`` holds a Claude Code session transcript.

``audit.json`` is this tool's own contamination check, independent of anything ``run.json`` carries:
- ``outside_paths``: every tool-call path argument (Read/Write/Edit/NotebookEdit/Glob/Grep-shaped
  ``file_path``/``path``/``notebook_path``/``directory`` fields), and every absolute path in a Bash
  ``command`` string, that does not resolve under the episode directory. A ``~`` or ``$HOME``-led token
  is always counted as outside: these episodes run as subagents of the coordinating session on the
  operator's own machine (D-87's stated limit), so HOME is the real host HOME, never the episode's own
  ``home/``, and neither this tool nor the subagent's own environment can tell otherwise from the
  transcript alone. A subagent's shell and search tools start from the session's cwd, which every
  transcript line records: a relative path resolves against it (else against ``work/``), and a Glob or
  Grep without a path, or a Bash command that does not begin with ``cd``, counts that cwd itself.
  ``SYSTEM_FILES`` and ``SYSTEM_DIRS`` (``/dev/null``, system tool directories) are never outside:
  they hold nothing about the task.
- ``skill_used``: true for any ``Skill`` tool call (it always reaches the coordinator's own registered
  skill, never a path inside the episode, so it is never "the staged copy"), or for any read of a path
  named ``SKILL.md`` or carrying a ``references`` path segment that does not resolve under this
  episode's own staged install (``stage.json``'s ``skill_dir`` under ``home/``). A method arm reading
  its own staged copy is the intended interaction and does not set this; reading anything else shaped
  like a skill file does, control arm or method arm alike.
- ``verdict``: ``"clean"``, or ``"invalid"`` with ``reason`` naming which rule fired. A control episode
  with ``skill_used``, or any episode with a non-empty ``outside_paths``, is ``invalid``. The file names
  paths only, never file content.

The coordinator, not this tool, merges the audit's verdict into the judgment before ``harness.py
record``: this tool only produces the two files and prints the audit result.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import usage  # noqa: E402

NA = 'n/a'
PATH_FIELDS = ('file_path', 'path', 'notebook_path', 'directory')
SEARCH_TOOLS = ('Glob', 'Grep')
LEADING_CD = re.compile(r'^\s*\(?\s*cd\s+([^\s;&|)]+)')
# Outside every episode, but they hold nothing about the task: compared after lexical normalization, so
# a '..' cannot climb out through them.
SYSTEM_FILES = ('/dev/null', '/dev/stdin', '/dev/stdout', '/dev/stderr', '/dev/tty')
SYSTEM_DIRS = ('/bin', '/sbin', '/usr/bin', '/usr/sbin', '/usr/lib', '/usr/local/bin', '/opt/homebrew/bin',
               '/System', '/Library/Developer/CommandLineTools')
BOUNDARY = r'\s=\'"<>|;('
ABS_TOKEN = re.compile(r'(?:(?<=^)|(?<=[' + BOUNDARY + r']))(/[^\s\'"()<>|;]+)')
HOME_TOKEN = re.compile(r'(?:(?<=^)|(?<=[' + BOUNDARY + r']))((?:~|\$HOME)(?:/[^\s\'"()<>|;]*)?)')
ISO = re.compile(r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?Z$')
PREAMBLE = ('The repository for this task is {episode}/work: paths in the task are relative to it, and your '
            'changes go there. Work only inside {episode}: never read, write or run anything outside it.\n\n')
ARM_SENTENCE = '\nA copy of the skill install for this episode is staged at {skill_md}.\n'


class Refusal(Exception):
    """Exit 1: a refusal or a failed check."""


class Usage_(Exception):
    """Exit 2: a usage error."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path, what):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as problem:
        raise Refusal('unreadable %s (%s)' % (what, problem.__class__.__name__))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())


def dump(value):
    return json.dumps(value, indent=1, ensure_ascii=False) + '\n'


def parse_utc(value, flag):
    match = ISO.match(value or '')
    if not match:
        raise Usage_('%s must be UTC like 2026-09-25T00:00:00Z' % flag)
    y, mo, d, h, mi, s = (int(part) for part in match.groups()[:6])
    micro = int((match.group(7) or '0').ljust(6, '0')[:6])
    return datetime.datetime(y, mo, d, h, mi, s, micro, tzinfo=datetime.timezone.utc)


def iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def read_stage(episode):
    staged = load(episode / 'stage.json', 'stage.json')
    prompts = staged.get('prompts')
    if not isinstance(prompts, list) or len(prompts) != 1:
        raise Refusal('a subagent episode needs exactly one staged prompt; stage.json lists %r' % (prompts,))
    return staged


def events_of(data):
    """Parse a transcript's bytes into a list of JSON object rows; a blank or unparseable line is skipped."""
    found = []
    for line in data.decode('utf-8', 'replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            found.append(row)
    return found


def tool_uses(events):
    """Every tool_use block with the cwd its line records, deduplicated by id (a streamed transcript can
    repeat one as it fills in); order is the id's first appearance, content is its last (most complete)
    appearance."""
    order, latest, cwds = [], {}, {}
    for event in events:
        if event.get('type') != 'assistant':
            continue
        message = event.get('message')
        if not isinstance(message, dict):
            continue
        for block in message.get('content') or []:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                key = block.get('id') if block.get('id') is not None else id(block)
                if key not in latest:
                    order.append(key)
                    cwds[key] = event.get('cwd')
                latest[key] = block
    return [(latest[key], cwds[key]) for key in order]


def last_role(events):
    relevant = [event.get('type') for event in events if event.get('type') in ('user', 'assistant')]
    return relevant[-1] if relevant else None


def skill_loaded_of(blocks, done):
    """The run.json convention (adapters.ClaudeCode.skill_use): a Skill call naming tackle, or any
    tool-call input whose JSON text mentions the staged skill path, however it was reached."""
    def marks(block):
        text = json.dumps(block.get('input') or {})
        return (block.get('name') == 'Skill' and 'tackle' in text) or 'skills/tackle/' in text
    loaded = any(marks(block) for block in blocks)
    return True if loaded else (False if done else NA)


def is_skill_like(raw):
    parts = Path(raw).parts
    return bool(parts) and (parts[-1] == 'SKILL.md' or 'references' in parts)


def is_system(raw):
    normal = os.path.normpath(raw)
    return normal in SYSTEM_FILES or any(normal == top or normal.startswith(top + '/') for top in SYSTEM_DIRS)


def safe_resolve(path):
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError):
        return path


def audit_of(uses, episode_dir, staged):
    """outside_paths and skill_used, independent of run.json's own skill_loaded: see the module docstring.
    The episode boundary is realpath'd (not just made absolute) so a symlinked temp root, such as macOS's
    /tmp -> /private/tmp, does not make an in-episode path look like it escaped, or vice versa. A relative
    path resolves against the cwd its transcript line records, else against work/."""
    episode_real = safe_resolve(episode_dir)
    work_dir = safe_resolve(episode_dir / 'work')
    staged_root = safe_resolve(episode_dir / 'home' / staged['skill_dir']) if staged.get('skill_dir') else None
    outside, skill_used = [], False
    for block, cwd in uses:
        name = block.get('name')
        input_ = block.get('input') if isinstance(block.get('input'), dict) else {}
        base_dir = Path(cwd) if isinstance(cwd, str) and os.path.isabs(cwd) else work_dir
        if name == 'Skill':
            skill_used = True
        candidates = [input_[field] for field in PATH_FIELDS if isinstance(input_.get(field), str) and input_[field]]
        if name in SEARCH_TOOLS and not candidates:
            candidates.append(str(base_dir))  # a search without a path searches the cwd
        if name == 'Bash' and isinstance(input_.get('command'), str):
            command = input_['command']
            lead = LEADING_CD.match(command)
            if not lead:
                candidates.append(str(base_dir))  # the command starts in the cwd
            elif not lead.group(1).startswith(('/', '~', '$HOME')):
                candidates.append(lead.group(1).strip('\'"'))
            candidates += [m.group(1) for m in HOME_TOKEN.finditer(command)]
            candidates += [m.group(1) for m in ABS_TOKEN.finditer(command)]
        for raw in candidates:
            if raw.startswith('~') or raw.startswith('$HOME'):
                outside.append(raw)
                if is_skill_like(raw):
                    skill_used = True
                continue
            if os.path.isabs(raw) and is_system(raw):
                continue
            base = Path(raw) if os.path.isabs(raw) else base_dir / raw
            resolved = safe_resolve(base)
            if not resolved.is_relative_to(episode_real):
                outside.append(raw)
            if is_skill_like(raw) and (staged_root is None or not resolved.is_relative_to(staged_root)):
                skill_used = True
    return list(dict.fromkeys(outside)), skill_used


def files_written(work_dir, baseline):
    """Identical in effect to harness.py's own files_written: work_dir's current bytes against stage.json's
    work_files baseline, written independently here so this tool imports no product file but usage.py."""
    count = 0
    for path in sorted(Path(work_dir).rglob('*')):
        if path.is_symlink() or path.is_file():
            data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
            if baseline.get(path.relative_to(work_dir).as_posix()) != sha(data):
                count += 1
    return count


def cmd_prompt(args):
    episode = Path(args.episode).absolute()
    staged = read_stage(episode)
    prompt_name = staged['prompts'][0]
    prompt_path = episode / 'prompts' / prompt_name
    try:
        text = prompt_path.read_bytes().decode('utf-8')
    except OSError as problem:
        raise Refusal('unreadable staged prompt %s (%s)' % (prompt_name, problem.__class__.__name__))
    output = PREAMBLE.format(episode=episode) + text
    if staged.get('arm') != 'control':
        if not staged.get('skill_dir'):
            raise Refusal('a treated arm has no staged skill_dir')
        skill_md = episode / 'home' / staged['skill_dir'] / 'SKILL.md'
        output += ARM_SENTENCE.format(skill_md=skill_md)
    sys.stdout.write(output)
    return 0


def cmd_finish(args):
    episode = Path(args.episode).absolute()
    staged = read_stage(episode)
    if (episode / 'run.json').exists() or (episode / 'sessions').exists():
        raise Refusal('the episode already ran')
    started = parse_utc(args.started, '--started')
    finished = parse_utc(args.finished, '--finished')
    if finished < started:
        raise Refusal('--finished precedes --started')
    transcript_path = Path(args.transcript)
    try:
        transcript = transcript_path.read_bytes()
    except OSError as problem:
        raise Refusal('unreadable --transcript (%s)' % problem.__class__.__name__)

    events = events_of(transcript)
    uses = tool_uses(events)
    blocks = [block for block, _ in uses]
    outcome = 'completed' if last_role(events) == 'assistant' else 'error'
    loaded = skill_loaded_of(blocks, outcome == 'completed')
    outside_paths, skill_used = audit_of(uses, episode, staged)

    reasons = []
    if staged['arm'] == 'control' and skill_used:
        reasons.append('a control episode used the skill')
    if outside_paths:
        reasons.append('%d path(s) outside the episode directory' % len(outside_paths))
    verdict = 'invalid' if reasons else 'clean'
    reason = '; '.join(reasons) if reasons else None

    spent = usage.claude_code_transcript(transcript_path)
    delta_seconds = (finished - started).total_seconds()
    transcript_hash = sha(transcript)
    session = {
        'index': 1, 'prompt': staged['prompts'][0], 'exit': 0 if outcome == 'completed' else 1,
        'timeout': False, 'signal': None, 'error': None if outcome == 'completed' else 'no final assistant message',
        'started_at': iso(started), 'finished_at': iso(finished), 'wall_seconds': round(delta_seconds, 3),
        'stdout_sha256': transcript_hash, 'stderr_sha256': sha(b''), 'tokens_in': spent['tokens_in'],
        'tokens_out': spent['tokens_out'], 'tool_calls': len(blocks), 'session_id': NA, 'skill_loaded': loaded,
        'usage_source': 'transcript'}
    result = {
        'schema': 'tackle-harness-run/1', 'adapter': 'subagent', 'isolation': NA, 'outcome': outcome,
        'exit': session['exit'], 'timeout': False, 'signal': session['signal'], 'sessions': [session],
        'transcript_sha256': transcript_hash, 'skill_loaded': loaded,
        'executor': {'harness': 'claude-code-subagent', 'model': args.model, 'effort': NA}, 'roles': [],
        'cost': {'tokens_in': spent['tokens_in'], 'tokens_out': spent['tokens_out'],
                 'wall_seconds': int(round(delta_seconds)), 'tool_calls': len(blocks),
                 'files_written': files_written(episode / 'work', staged['work_files'])},
        'capture_path': 'claude-code subagent transcript under sessions/01/stdout (requestId dedup)',
        'model_binding': 'unsupported', 'started_at': iso(started), 'finished_at': iso(finished)}
    audit = {'outside_paths': outside_paths, 'skill_used': skill_used, 'verdict': verdict, 'reason': reason}

    write(episode / 'sessions' / '01' / 'stdout', transcript)
    write(episode / 'sessions' / '01' / 'stderr', b'')
    write(episode / 'sessions' / '01' / 'meta.json', dump(session))
    write(episode / 'run.json', dump(result))
    write(episode / 'audit.json', dump(audit))
    print('finish: outcome=%s tool_calls=%d' % (outcome, len(blocks)))
    print('audit: verdict=%s outside_paths=%d skill_used=%s' % (verdict, len(outside_paths), skill_used))
    return 1 if outcome == 'error' else 0


def parser():
    top = argparse.ArgumentParser(prog='subagent.py', description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = top.add_subparsers(dest='command')
    show = sub.add_parser('prompt')
    show.add_argument('--episode', required=True)
    finish = sub.add_parser('finish')
    finish.add_argument('--episode', required=True)
    finish.add_argument('--transcript', required=True)
    finish.add_argument('--model', required=True)
    finish.add_argument('--started', required=True)
    finish.add_argument('--finished', required=True)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    if not args.command:
        parser().error('a command is required: prompt or finish')
    try:
        if args.command == 'prompt':
            return cmd_prompt(args)
        return cmd_finish(args)
    except Refusal as problem:
        sys.stderr.write('subagent: refused: %s\n' % problem)
        return 1
    except Usage_ as problem:
        sys.stderr.write('subagent: %s\n' % problem)
        return 2


if __name__ == '__main__':
    sys.exit(main())
