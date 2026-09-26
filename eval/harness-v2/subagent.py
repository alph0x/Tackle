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
  Grep without a path, or a Bash command that neither begins with ``cd`` nor names an absolute path
  inside the episode, counts that cwd itself.
  ``SYSTEM_FILES`` and ``SYSTEM_DIRS`` (``/dev/null``, system tool directories) are never outside:
  they hold nothing about the task. A call to any tool outside ``LOCAL_TOOLS`` (an MCP server such as a
  code graph of the host repository, web access, a nested agent) reaches past the episode without naming
  a path, and is listed as ``tool:<name>``.
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
# The tools whose reach the audit can see from their arguments. Any other tool (an MCP server, web access,
# a nested agent) reaches past the episode without naming a path, so it is outside by definition.
LOCAL_TOOLS = ('Read', 'Write', 'Edit', 'MultiEdit', 'NotebookEdit', 'Glob', 'Grep', 'Bash', 'BashOutput',
               'KillShell', 'Skill', 'ToolSearch', 'TodoWrite', 'TaskCreate', 'TaskGet', 'TaskList', 'TaskUpdate',
               'SubagentHandback')  # the harness's channel for the subagent's final report
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
ARM_SENTENCE = ('\nUse the Tackle method for this task: its skill is staged at {skill_md}; read that file first '
                'and follow it.\n')
ROUTED_ARM = 'method:routed'
# session 1's fixed closing block, method:routed only: the planner writes a paper plan instead of
# implementing, and never touches work/ or the skill's own PLAN scaffolding.
PLANNER_CLOSING = (
    '\nWrite a **paper plan** for whoever implements this task to {episode}/brief.md, including a '
    '`**Tier**:` line and, if you want one capped escalation available, an `**Escalation**: declared` '
    'line, in the vocabulary `references/task.tmpl.md` uses. Do not implement the task yourself, do not '
    'create or edit any file under {episode}/work, and do not run the skill\'s own PLAN scaffolding (no '
    '`docs/plans/` workspace) — write the plan as prose to `brief.md` only. Do not dispatch any subagent, '
    'reviewer or Task-tool call yourself; if the skill\'s procedure calls for one, describe that step in '
    'your plan instead of doing it. When finished, your final report must be exactly the single word '
    'DONE, with no summary.\n')
# session >= 2's fixed prompt, method:routed only: identical text regardless of session number.
EXECUTOR_PROMPT = (
    'Read the file {episode}/brief.md and carry out the task it describes, with your changes going in '
    '{episode}/work. If you hit a capability failure the brief\'s `Escalation` line lets you retry once '
    'at a higher tier, your final report must be exactly the single word ESCALATE instead of DONE; '
    'otherwise it must be exactly the single word DONE, with no summary.\n')
# A session >= 2 stays inside its brief: these paths are legal for session 1 (which legitimately reads its
# own staged prompt) but not for the executor, who must rely only on the planner's brief.
DENY_PREFIXES = ('prompts/', 'sessions/', 'dispatch.txt', 'stage.json')
TIER_VALUES = ('fast', 'standard', 'frontier')
TIER_LINE = re.compile(r'^\*\*Tier\*\*:[ \t]*(.*)$', re.M)
ESCALATION_LINE = re.compile(r'^\*\*Escalation\*\*:[ \t]*(.*)$', re.M)
ROLES = ('planner', 'executor')


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
    return load(episode / 'stage.json', 'stage.json')


def single_prompt(staged):
    """The one staged prompt name, or a refusal: session 1 (or its omission) is the only caller, on any
    arm — a session >= 2 never reads stage.json['prompts'] at all."""
    prompts = staged.get('prompts')
    if not isinstance(prompts, list) or len(prompts) != 1:
        raise Refusal('a subagent episode needs exactly one staged prompt; stage.json lists %r' % (prompts,))
    return prompts[0]


def read_tier_fields(text):
    """(tier, escalation) mechanically read from a brief's `**Tier**:`/`**Escalation**:` lines. Output is
    restricted to the closed tier vocabulary: a missing, malformed, or trailing-prose value (a valid word
    followed by more text) prints tier=n/a, never echoing planner-authored prose."""
    tier_match = TIER_LINE.search(text or '')
    tier_value = tier_match.group(1).strip() if tier_match else None
    tier = tier_value if tier_value in TIER_VALUES else NA
    escalation_match = ESCALATION_LINE.search(text or '')
    declared = escalation_match is not None and escalation_match.group(1).strip() == 'declared'
    return tier, ('declared' if declared else 'absent')


def final_report(events):
    """The subagent's own final report text: a SubagentHandback tool call's message, if the transcript
    makes one (the harness's own channel for it, observed in the first smoke episode), else the last
    assistant text block. Returns None when neither exists."""
    handback, last_text = None, None
    for event in events:
        if event.get('type') != 'assistant':
            continue
        message = event.get('message')
        if not isinstance(message, dict):
            continue
        for block in message.get('content') or []:
            if not isinstance(block, dict):
                continue
            if block.get('type') == 'tool_use' and block.get('name') == 'SubagentHandback':
                input_ = block.get('input') if isinstance(block.get('input'), dict) else {}
                if isinstance(input_.get('message'), str):
                    handback = input_['message']
            elif block.get('type') == 'text' and isinstance(block.get('text'), str):
                last_text = block['text']
    return handback if handback is not None else last_text


def tree_digest(root):
    """Identical in effect to harness.py's own tree_digest (mapping_digest of a sorted {path: sha256}),
    written independently here so this tool imports no product file but usage.py (matches files_written's
    own precedent). A symlink refuses, exactly as harness.py's read_tree does."""
    files = {}
    for path in sorted(Path(root).rglob('*')):
        if path.is_symlink():
            raise Refusal('symlink in %s: %s' % (Path(root).name, path.relative_to(root).as_posix()))
        if path.is_file():
            files[path.relative_to(root).as_posix()] = sha(path.read_bytes())
    return sha(json.dumps(files, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


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


def denied(resolved, episode_real, deny_prefixes):
    """Whether a path that resolves inside the episode still falls under one of deny_prefixes (readiness
    F1): a session >= 2 relying only on its brief never legitimately reads prompts/, sessions/,
    dispatch.txt or stage.json, even though they resolve inside <episode>."""
    relative = resolved.relative_to(episode_real).as_posix()
    return any(relative == prefix.rstrip('/') or relative.startswith(prefix) for prefix in deny_prefixes)


def audit_of(uses, episode_dir, staged, deny_prefixes=None):
    """outside_paths and skill_used, independent of run.json's own skill_loaded: see the module docstring.
    The episode boundary is realpath'd (not just made absolute) so a symlinked temp root, such as macOS's
    /tmp -> /private/tmp, does not make an in-episode path look like it escaped, or vice versa. A relative
    path resolves against the cwd its transcript line records, else against work/. `deny_prefixes`, used
    only for a routed episode's session >= 2, folds a legal-looking-but-off-limits in-episode path into
    this same outside_paths/invalid mechanism (never used for session 1, which legitimately reads its own
    staged prompt)."""
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
        if name not in LOCAL_TOOLS:
            outside.append('tool:%s' % name)
            continue
        candidates = [input_[field] for field in PATH_FIELDS if isinstance(input_.get(field), str) and input_[field]]
        if name in SEARCH_TOOLS and not candidates:
            candidates.append(str(base_dir))  # a search without a path searches the cwd
        if name == 'Bash' and isinstance(input_.get('command'), str):
            command = input_['command']
            absolute = [m.group(1) for m in ABS_TOKEN.finditer(command)]
            lead = LEADING_CD.match(command)
            if not lead:
                if not any(safe_resolve(Path(raw)).is_relative_to(episode_real) for raw in absolute):
                    candidates.append(str(base_dir))  # the command starts in the cwd and names nothing inside
            elif not lead.group(1).startswith(('/', '~', '$HOME')):
                candidates.append(lead.group(1).strip('\'"'))
            candidates += [m.group(1) for m in HOME_TOKEN.finditer(command)]
            candidates += absolute
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
            elif deny_prefixes and denied(resolved, episode_real, deny_prefixes):
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


def total_or_na(values):
    """Sum, unless any value is unknown ('n/a'), in which case the sum is unknown too."""
    values = list(values)
    return NA if any(v == NA for v in values) else sum(values)


def cmd_prompt(args):
    episode = Path(args.episode).absolute()
    staged = read_stage(episode)
    session = args.session or 1
    routed = staged.get('arm') == ROUTED_ARM
    if session >= 2:
        if not routed:
            raise Refusal('--session >= 2 is only valid for a %s episode' % ROUTED_ARM)
        if not (episode / 'brief.md').is_file():
            raise Refusal('%s/brief.md does not exist yet: session 1 has not closed, or produced nothing'
                          % episode)
        sys.stdout.write(PREAMBLE.format(episode=episode) + EXECUTOR_PROMPT.format(episode=episode))
        return 0
    prompt_name = single_prompt(staged)
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
    if routed:
        output += PLANNER_CLOSING.format(episode=episode)
    sys.stdout.write(output)
    return 0


def cmd_finish(args):
    episode = Path(args.episode).absolute()
    staged = read_stage(episode)
    session_n = args.session
    routed = staged.get('arm') == ROUTED_ARM
    routed_write = routed and session_n is not None

    if session_n is None or session_n == 1:
        # Today's exact guard and prompt read, unchanged, on any arm.
        if (episode / 'run.json').exists() or (episode / 'sessions').exists():
            raise Refusal('the episode already ran')
        prompt_name = single_prompt(staged)
    else:
        if not routed:
            raise Refusal('--session is only valid for a %s episode' % ROUTED_ARM)
        sessions_dir = episode / 'sessions'
        existing = sorted(int(p.name) for p in sessions_dir.glob('[0-9][0-9]') if p.is_dir()) \
            if sessions_dir.is_dir() else []
        if session_n in existing:
            raise Refusal('session %d is already recorded' % session_n)
        highest = max(existing) if existing else 0
        if session_n > highest + 1:
            raise Refusal('session %d skips ahead of the highest recorded session %d' % (session_n, highest))
        prompt_name = 'brief.md'

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
    deny = DENY_PREFIXES if (routed_write and session_n >= 2) else None
    outside_paths, skill_used = audit_of(uses, episode, staged, deny_prefixes=deny)
    spent = usage.claude_code_transcript(transcript_path)
    delta_seconds = (finished - started).total_seconds()
    transcript_hash = sha(transcript)
    index = session_n if session_n is not None else 1
    session = {
        'index': index, 'prompt': prompt_name, 'exit': 0 if outcome == 'completed' else 1,
        'timeout': False, 'signal': None, 'error': None if outcome == 'completed' else 'no final assistant message',
        'started_at': iso(started), 'finished_at': iso(finished), 'wall_seconds': round(delta_seconds, 3),
        'stdout_sha256': transcript_hash, 'stderr_sha256': sha(b''), 'tokens_in': spent['tokens_in'],
        'tokens_out': spent['tokens_out'], 'tool_calls': len(blocks), 'session_id': NA, 'skill_loaded': loaded,
        'usage_source': 'transcript'}

    if routed_write:
        session.update(role=args.role or NA, tier=args.tier or NA, model=args.model,
                       work_sha256=tree_digest(episode / 'work'))
        directory = episode / 'sessions' / ('%02d' % session_n)
        write(directory / 'stdout', transcript)
        write(directory / 'stderr', b'')
        write(directory / 'meta.json', dump(session))
        print('session %d recorded; run `subagent.py close` once every session is in' % session_n)
        return 0 if outcome == 'completed' else 1

    # Today's exact single-call behaviour: writes run.json/audit.json directly, unchanged.
    reasons = []
    if staged['arm'] == 'control' and skill_used:
        reasons.append('a control episode used the skill')
    if outside_paths:
        reasons.append('%d path(s) outside the episode directory' % len(outside_paths))
    verdict = 'invalid' if reasons else 'clean'
    reason = '; '.join(reasons) if reasons else None

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


def cmd_close(args):
    """method:routed only: merge every sessions/0N/ on disk into one run.json/audit.json."""
    episode = Path(args.episode).absolute()
    staged = read_stage(episode)
    if staged.get('arm') != ROUTED_ARM:
        raise Refusal('close is only valid for a %s episode' % ROUTED_ARM)
    if (episode / 'run.json').exists():
        raise Refusal('the episode already ran')
    session_dirs = sorted((p for p in (episode / 'sessions').glob('[0-9][0-9]') if p.is_dir()),
                          key=lambda p: p.name) if (episode / 'sessions').is_dir() else []
    if not session_dirs:
        raise Refusal('no sessions/0N/ recorded yet; run finish --session 1 first')

    reasons = []
    brief_path = episode / 'brief.md'
    if not brief_path.is_file():
        reasons.append('planner produced no brief')
        escalation = 'absent'
    else:
        _, escalation = read_tier_fields(brief_path.read_text(encoding='utf-8', errors='replace'))

    metas, sessions = [], []
    outside_all, skill_used_any = [], False
    for position, directory in enumerate(session_dirs, start=1):
        meta = json.loads((directory / 'meta.json').read_text(encoding='utf-8'))
        transcript = (directory / 'stdout').read_bytes()
        metas.append(meta)
        sessions.append(meta)
        events = events_of(transcript)
        uses = tool_uses(events)
        deny = DENY_PREFIXES if position >= 2 else None
        outside, skill_used = audit_of(uses, episode, staged, deny_prefixes=deny)
        outside_all += outside
        skill_used_any = skill_used_any or skill_used
        if position == 1:
            if meta.get('work_sha256') != staged.get('work_sha256'):
                reasons.append('planner session modified the work tree')
        else:
            if outside:
                reasons.append('executor read past its brief')
            report = (final_report(events) or '').strip()
            if report == 'ESCALATE':
                if escalation != 'declared':
                    reasons.append('escalation without a declared brief')
                elif position == 2 and not any(d.name == '03' for d in session_dirs):
                    reasons.append('live escalation out of scope for 9.0.0')
    if outside_all and not any('read past its brief' in r for r in reasons):
        reasons.append('%d path(s) outside the episode directory' % len(outside_all))

    verdict = 'invalid' if reasons else 'clean'
    reason = '; '.join(dict.fromkeys(reasons)) if reasons else None
    roles = [{'role': meta.get('role', NA), 'tier': meta.get('tier', NA), 'model': meta.get('model', NA),
             'effort': NA, 'tokens_in': meta['tokens_in'], 'tokens_out': meta['tokens_out']} for meta in metas]
    cost = {
        'tokens_in': total_or_na(m['tokens_in'] for m in metas), 'tokens_out': total_or_na(m['tokens_out'] for m in metas),
        'wall_seconds': int(round(sum(m['wall_seconds'] for m in metas))),
        'tool_calls': sum(m['tool_calls'] for m in metas),
        'files_written': files_written(episode / 'work', staged['work_files'])}
    outcome = 'completed' if all(m['exit'] == 0 for m in metas) else 'error'
    transcript_hash = sha(json.dumps([m['stdout_sha256'] for m in metas], separators=(',', ':')).encode())
    started_at = min(m['started_at'] for m in metas)
    finished_at = max(m['finished_at'] for m in metas)
    result = {
        'schema': 'tackle-harness-run/1', 'adapter': 'subagent', 'isolation': NA, 'outcome': outcome,
        'exit': 0 if outcome == 'completed' else 1, 'timeout': False, 'signal': None, 'sessions': sessions,
        'transcript_sha256': transcript_hash, 'skill_loaded': sessions[0].get('skill_loaded', NA),
        'executor': {'harness': 'claude-code-subagent', 'model': metas[0].get('model', NA), 'effort': NA},
        'roles': roles, 'cost': cost,
        'capture_path': 'claude-code subagent transcripts under sessions/0N/stdout (requestId dedup)',
        'model_binding': 'unsupported', 'started_at': started_at, 'finished_at': finished_at}
    audit = {'outside_paths': list(dict.fromkeys(outside_all)), 'skill_used': skill_used_any, 'verdict': verdict,
             'reason': reason}

    write(episode / 'run.json', dump(result))
    write(episode / 'audit.json', dump(audit))
    print('close: sessions=%d outcome=%s' % (len(session_dirs), outcome))
    print('audit: verdict=%s outside_paths=%d skill_used=%s' % (verdict, len(audit['outside_paths']), skill_used_any))
    return 0


def cmd_tier(args):
    """method:routed only, mechanical and read-only: prints tier=<value> escalation=<declared|absent> from
    <episode>/brief.md, without the coordinator itself reading the brief's prose."""
    episode = Path(args.episode).absolute()
    brief_path = episode / 'brief.md'
    if brief_path.is_file():
        tier, escalation = read_tier_fields(brief_path.read_text(encoding='utf-8', errors='replace'))
    else:
        tier, escalation = NA, 'absent'
    print('tier=%s escalation=%s' % (tier, escalation))
    return 0


def parser():
    top = argparse.ArgumentParser(prog='subagent.py', description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = top.add_subparsers(dest='command')
    show = sub.add_parser('prompt')
    show.add_argument('--episode', required=True)
    show.add_argument('--session', type=int, default=None)
    finish = sub.add_parser('finish')
    finish.add_argument('--episode', required=True)
    finish.add_argument('--session', type=int, default=None)
    finish.add_argument('--role', choices=ROLES, default=None)
    finish.add_argument('--tier', choices=TIER_VALUES + (NA,), default=None)
    finish.add_argument('--transcript', required=True)
    finish.add_argument('--model', required=True)
    finish.add_argument('--started', required=True)
    finish.add_argument('--finished', required=True)
    close = sub.add_parser('close')
    close.add_argument('--episode', required=True)
    tier = sub.add_parser('tier')
    tier.add_argument('--episode', required=True)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    if not args.command:
        parser().error('a command is required: prompt, finish, close or tier')
    try:
        if args.command == 'prompt':
            return cmd_prompt(args)
        if args.command == 'finish':
            return cmd_finish(args)
        if args.command == 'close':
            return cmd_close(args)
        return cmd_tier(args)
    except Refusal as problem:
        sys.stderr.write('subagent: refused: %s\n' % problem)
        return 1
    except Usage_ as problem:
        sys.stderr.write('subagent: %s\n' % problem)
        return 2


if __name__ == '__main__':
    sys.exit(main())
