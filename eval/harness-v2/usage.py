"""Extracts token-usage figures from Claude Code and Codex transcripts.

Token fields are always integers or the string 'n/a'; an unknown count is never
reported as 0, so a caller can distinguish "definitely zero" from "could not tell".

- Claude Code: tokens_in = input_tokens + cache_creation_input_tokens + cache_read_input_tokens.
- Codex: tokens_in = input_tokens, which already counts cached input.
- Both: tokens_out = output_tokens.
"""

import glob
import json
from pathlib import Path

_NA = 'n/a'


def claude_code_transcript(path) -> dict:
    """One Claude Code session or subagent transcript (JSONL). Rows with message.usage
    are grouped by requestId; per group keep the row with the largest output_tokens;
    sum across groups. Returns {'tokens_in', 'tokens_out', 'cache_read', 'cache_write',
    'requests', 'models', 'unkeyed', 'bad_lines', 'reason'}, where 'models' is the
    sorted list of message.model values.
    - No usage rows: every count is 'n/a', requests is 0, reason is 'no usage rows'.
    - A usage row without requestId is counted in 'unkeyed' and never raises. If any
      exists, the token counts are 'n/a' and the reason says so.
    - A line that is not JSON is counted in 'bad_lines'. If any exists, the token
      counts are 'n/a' and the reason says so.
    - Otherwise reason is None.

    A blank (whitespace-only) line is skipped and never counted as a bad line. A missing
    sub-field within a present usage object (for example no cache_creation_input_tokens)
    is treated as 0 for that row, matching how these payloads omit zero-valued fields;
    this is distinct from having no usage data at all, which is 'n/a'.
    """
    groups = {}
    unkeyed = 0
    bad_lines = 0
    models = set()
    usage_row_count = 0

    with open(path, 'r', encoding='utf-8', errors='replace') as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                bad_lines += 1
                continue
            if not isinstance(row, dict):
                continue
            message = row.get('message')
            if not isinstance(message, dict):
                continue
            row_usage = message.get('usage')
            if not isinstance(row_usage, dict):
                continue

            usage_row_count += 1
            model = message.get('model')
            if isinstance(model, str):
                models.add(model)

            request_id = row.get('requestId')
            if request_id is None:
                unkeyed += 1
                continue
            out_tokens = row_usage.get('output_tokens')
            if not isinstance(out_tokens, (int, float)):
                out_tokens = 0
            best = groups.get(request_id)
            if best is None or out_tokens > best[0]:
                groups[request_id] = (out_tokens, row_usage)

    if usage_row_count == 0:
        return {
            'tokens_in': _NA, 'tokens_out': _NA,
            'cache_read': _NA, 'cache_write': _NA,
            'requests': 0, 'models': sorted(models),
            'unkeyed': unkeyed, 'bad_lines': bad_lines,
            'reason': 'no usage rows',
        }

    reasons = []
    if unkeyed > 0:
        reasons.append('unkeyed usage rows present')
    if bad_lines > 0:
        reasons.append('unparseable lines present')
    reason = ' and '.join(reasons) if reasons else None

    if reason is not None:
        tokens_in = tokens_out = cache_read = cache_write = _NA
    else:
        tokens_in = tokens_out = cache_read = cache_write = 0
        for _, row_usage in groups.values():
            in_t = row_usage.get('input_tokens') or 0
            cache_write_t = row_usage.get('cache_creation_input_tokens') or 0
            cache_read_t = row_usage.get('cache_read_input_tokens') or 0
            out_t = row_usage.get('output_tokens') or 0
            tokens_in += in_t + cache_write_t + cache_read_t
            tokens_out += out_t
            cache_read += cache_read_t
            cache_write += cache_write_t

    return {
        'tokens_in': tokens_in, 'tokens_out': tokens_out,
        'cache_read': cache_read, 'cache_write': cache_write,
        'requests': len(groups), 'models': sorted(models),
        'unkeyed': unkeyed, 'bad_lines': bad_lines,
        'reason': reason,
    }


def claude_code_subagents(home) -> list:
    """Every <home>/.claude/projects/*/*/subagents/agent-<id>.jsonl with its
    agent-<id>.meta.json: [{'agent_id', 'role' (meta 'description', else 'agentType',
    else 'n/a'), 'model_requested' (meta 'model' or 'n/a'), 'usage':
    claude_code_transcript(...)}], sorted by agent_id. A missing or unreadable
    meta.json gives 'n/a' fields and never raises."""
    home = Path(home)
    pattern = str(home / '.claude' / 'projects' / '*' / '*' / 'subagents' / 'agent-*.jsonl')
    results = []
    for jsonl_path_str in glob.glob(pattern):
        jsonl_path = Path(jsonl_path_str)
        filename = jsonl_path.name
        agent_id = filename[len('agent-'):-len('.jsonl')]
        meta_path = jsonl_path.with_name('agent-{}.meta.json'.format(agent_id))
        meta = {}
        try:
            with open(meta_path, 'r', encoding='utf-8') as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                meta = loaded
        except (OSError, ValueError):
            meta = {}

        role = meta.get('description')
        if role is None:
            role = meta.get('agentType')
        if role is None:
            role = _NA

        model_requested = meta.get('model')
        if model_requested is None:
            model_requested = _NA

        results.append({
            'agent_id': agent_id,
            'role': role,
            'model_requested': model_requested,
            'usage': claude_code_transcript(jsonl_path),
        })
    results.sort(key=lambda item: item['agent_id'])
    return results


def claude_code_sessions(home) -> list:
    """Every <home>/.claude/projects/*/<session>.jsonl (not under a subagents/
    directory): [{'session_id', 'usage': claude_code_transcript(...)}], sorted by
    session_id."""
    home = Path(home)
    pattern = str(home / '.claude' / 'projects' / '*' / '*.jsonl')
    results = []
    for jsonl_path_str in glob.glob(pattern):
        jsonl_path = Path(jsonl_path_str)
        session_id = jsonl_path.name[:-len('.jsonl')]
        results.append({
            'session_id': session_id,
            'usage': claude_code_transcript(jsonl_path),
        })
    results.sort(key=lambda item: item['session_id'])
    return results


def _find_last_result(objs):
    result = None
    for obj in objs:
        if isinstance(obj, dict) and obj.get('type') == 'result' and isinstance(obj.get('usage'), dict):
            result = obj
    return result


def claude_code_result(stdout: bytes) -> dict:
    """From `--output-format stream-json` or `json` output: the last object with type
    'result' and a 'usage' dict gives tokens_in and tokens_out as above, plus
    'session_id' when present. Missing values are 'n/a'. Non-JSON lines are ignored.

    The whole payload is tried as a single JSON document first (covers `json` output,
    which may be pretty-printed across many lines); if that does not parse or does not
    contain a result object, it falls back to parsing line by line (covers
    `stream-json`, where each line is its own JSON object)."""
    text = stdout.decode('utf-8', errors='replace')

    result_obj = None
    try:
        whole = json.loads(text)
    except ValueError:
        whole = None
    if whole is not None:
        result_obj = _find_last_result(whole if isinstance(whole, list) else [whole])

    if result_obj is None:
        candidates = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                candidates.append(json.loads(line))
            except ValueError:
                continue
        result_obj = _find_last_result(candidates)

    if result_obj is None:
        return {'tokens_in': _NA, 'tokens_out': _NA, 'session_id': _NA}

    result_usage = result_obj['usage']
    tokens_in = (
        (result_usage.get('input_tokens') or 0)
        + (result_usage.get('cache_creation_input_tokens') or 0)
        + (result_usage.get('cache_read_input_tokens') or 0)
    )
    tokens_out = result_usage.get('output_tokens') or 0
    session_id = result_obj.get('session_id')
    if session_id is None:
        session_id = _NA
    return {'tokens_in': tokens_in, 'tokens_out': tokens_out, 'session_id': session_id}


def codex_turns(stdout: bytes) -> dict:
    """From `codex exec --json`: sum input_tokens, cached_input_tokens (as
    'cache_read') and output_tokens over every 'turn.completed' event's 'usage'.
    'turns' counts those events; 'thread_id' comes from 'thread.started' when present.
    With no such event, the counts are 'n/a'. Non-JSON lines are ignored."""
    text = stdout.decode('utf-8', errors='replace')
    tokens_in = 0
    cache_read = 0
    tokens_out = 0
    turns = 0
    thread_id = None
    found = False

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue

        event_type = row.get('type')
        if event_type == 'turn.completed':
            row_usage = row.get('usage')
            if isinstance(row_usage, dict):
                found = True
                turns += 1
                tokens_in += row_usage.get('input_tokens') or 0
                cache_read += row_usage.get('cached_input_tokens') or 0
                tokens_out += row_usage.get('output_tokens') or 0
        elif event_type == 'thread.started':
            candidate_id = row.get('thread_id')
            if candidate_id is not None:
                thread_id = candidate_id

    thread_id = thread_id if thread_id is not None else _NA
    if not found:
        return {
            'tokens_in': _NA, 'tokens_out': _NA, 'cache_read': _NA,
            'turns': _NA, 'thread_id': thread_id,
        }
    return {
        'tokens_in': tokens_in, 'tokens_out': tokens_out, 'cache_read': cache_read,
        'turns': turns, 'thread_id': thread_id,
    }
