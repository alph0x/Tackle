"""Field-report tool: one deterministic command that reports, per local Tackle workspace and for a
repository revision range, what real work cost and where the effort went.

Usage:
    python3 maintaining/field_report.py --plans <dir> --repo <dir> --since <rev> [--until <rev>]
        [--workspace <slug> ...] --json <file> --markdown <file>

Every value names the record it came from; what the records cannot support is reported as the string
"n/a", never invented or defaulted to zero. This tool only reads `--plans` and `--repo`; it never
writes into either (only the `--json`/`--markdown` output files, which may point anywhere, including
inside `--plans`). Standard library only, no network access, no model-backed subprocess.

Exit 0: the report was written. Exit 2: a usage error (including `--repo` not a git work tree, an
unresolvable `--since`/`--until`, or a requested `--workspace` that does not exist); nothing is
written in that case.

Design notes (see eval/field-report/README.md for the full rationale, grounded in
references/guides/migrate.md's schema-keyed detection table and references/terminology.md's legacy
state map):
  - Only a workspace's root-level files are read (never a subdirectory), which is what keeps a
    `legacy-*/` snapshot or a task's own `verification-records/<task>/` out of scope by construction,
    not by an exclusion list.
  - The historical file names (`board.md`, `log.md`, `usage.md`, `usage.telemetry.jsonl`) are read
    exactly like their current replacements, per references/guides/usage-observability.md's legacy
    compatibility rule.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

SCHEMA = 'tackle-field-report/1'

# ---------------------------------------------------------------------------------------------
# Markdown/board parsing primitives, grounded in migrate.md's schema-keyed detection table (the same
# table `references/recipes/migrate/schema.md`'s `schema_of`/`parse_board` helpers implement).
# Reimplemented here rather than imported, so this stand-alone tool carries no runtime dependency on
# that recipe module's own naming and layout.
# ---------------------------------------------------------------------------------------------

_FENCE_RE = re.compile(r'^\s{0,3}(`{3,}|~{3,})(.*)$')


def unfenced_lines(text):
    """Lines of `text` outside fenced code blocks."""
    fence = None
    out = []
    for line in text.splitlines():
        match = _FENCE_RE.match(line)
        if fence:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= fence[1] \
                    and not match.group(2).strip():
                fence = None
            continue
        if match:
            fence = (match.group(1)[0], len(match.group(1)))
            continue
        out.append(line)
    return out


def schema_token(text):
    """The value after a top-level 'Schema:' line, or None."""
    for line in unfenced_lines(text):
        if line.startswith('Schema:'):
            return line[len('Schema:'):].strip()
    return None


def split_row(line):
    """A pipe-table row's cells (no leading/trailing empty cell), or None if not a table row."""
    if '|' not in line:
        return None
    cells = line.split('|')
    if len(cells) < 3:
        return None
    return [cell.strip() for cell in cells[1:-1]]


def is_delimiter_row(line):
    stripped = line.strip()
    return bool(re.fullmatch(r'\|?[\s:|-]+\|?', stripped)) and '-' in stripped


def find_table(text, start=0):
    """(header_cells, [row_cells, ...]) for the first header+delimiter pipe table found outside
    fences at or after unfenced line index `start`, or None."""
    lines = unfenced_lines(text)
    for i in range(start, len(lines) - 1):
        if not lines[i].strip().startswith('|') or not is_delimiter_row(lines[i + 1]):
            continue
        header = split_row(lines[i])
        if not header:
            continue
        rows = []
        j = i + 2
        while j < len(lines):
            cells = split_row(lines[j])
            if cells is None:
                break
            rows.append(cells)
            j += 1
        return header, rows
    return None


def column_index(header, name):
    for i, cell in enumerate(header):
        if cell == name:
            return i
    return None


# ---------------------------------------------------------------------------------------------
# Bucket detection: migrate.md#schema-keyed-migration's table, read from a workspace's root files
# only (never a `legacy-*/` snapshot, never a subdirectory -- both are simply never opened).
# ---------------------------------------------------------------------------------------------

def detect_bucket(root_texts):
    """root_texts: {'plan.md' | 'board.md' | 'task-board.md': text}, root-level files only.
    Returns (bucket, source_filename_or_None)."""
    matches = {}
    plan = root_texts.get('plan.md')
    if plan is not None and plan.splitlines() and plan.splitlines()[0].strip() == 'Gate: Lite':
        matches['lite'] = 'plan.md'
    board = root_texts.get('board.md')
    if board is not None:
        token = schema_token(board)
        if token == 'tackle-workspace/3':
            matches['3'] = 'board.md'
        elif token is None:
            table = find_table(board)
            if table and 'Status' in table[0] and any(word in table[0] for word in ('Point', 'Task')):
                matches['pre-3'] = 'board.md'
    task_board = root_texts.get('task-board.md')
    if task_board is not None:
        token = schema_token(task_board)
        if token == 'tackle-workspace/4':
            matches['4'] = 'task-board.md'
        elif token == 'tackle-workspace/5':
            matches['5'] = 'task-board.md'
    if len(matches) == 1:
        bucket = next(iter(matches))
        return bucket, matches[bucket]
    return 'unknown', None


# ---------------------------------------------------------------------------------------------
# Task state counting: references/terminology.md's "States and observations" table (both the
# emoji and the legacy English words), applied to whichever board file `detect_bucket` settled on.
# ---------------------------------------------------------------------------------------------

VALID_STATES = ('Draft', 'Ready to run', 'In progress', 'Checking', 'Complete',
                'Blocked', 'Interrupted', 'Skipped', 'Unverifiable', 'Waiting on owner')

_EMOJI_STATES = (
    ('\U0001F534', 'Draft'),         # red circle
    ('\U0001F7E1', 'In progress'),   # yellow circle
    ('\U0001F7E2', 'Complete'),      # green circle
    ('⏸', 'Blocked'),           # pause
    ('⚪', 'Skipped'),           # white circle
)
_VARIATION_SELECTOR = '️'

# Ordered longest-phrase-first so e.g. "ready to run" is matched before the bare legacy "ready",
# and multi-word legacy phrases are matched before a shorter word another phrase happens to contain.
_TEXT_STATES = (
    ('waiting on owner', 'Waiting on owner'),
    ('unavailable required check', 'Unverifiable'),
    ('not started', 'Draft'),
    ('ready to run', 'Ready to run'),
    ('target validation', 'Checking'),
    ('observe-incomplete', 'Interrupted'),
    ('interrupted', 'Interrupted'),
    ('unverifiable', 'Unverifiable'),
    ('validating', 'Checking'),
    ('integrating', 'Checking'),
    ('accepting', 'Checking'),
    ('checking', 'Checking'),
    ('implementing', 'In progress'),
    ('correction', 'In progress'),
    ('preflight', 'In progress'),
    ('in progress', 'In progress'),
    ('done', 'Complete'),
    ('complete', 'Complete'),
    ('skipped', 'Skipped'),
    ('blocked', 'Blocked'),
    ('draft', 'Draft'),
    ('ready', 'Ready to run'),
)

_TASK_ID_RE = re.compile(r'[PT]-\d+')


def map_status(cell):
    """The canonical state for one Status cell, or None if it matches nothing known."""
    text = cell.replace(_VARIATION_SELECTOR, '')
    for glyph, state in _EMOJI_STATES:
        if glyph in text:
            return state
    lowered = text.lower()
    for needle, state in _TEXT_STATES:
        if needle in lowered:
            return state
    return None


def count_tasks(board_text):
    """(by_state, unmapped_raw_values) over every task row of the first board table in board_text.
    A row only counts as a task row when its first cell names a P-/T-id (this also excludes a
    decorative or unrelated pipe table, if one precedes the real board)."""
    table = find_table(board_text)
    by_state, unmapped = {}, []
    if not table:
        return by_state, unmapped
    header, rows = table
    status_col = column_index(header, 'Status')
    if status_col is None:
        return by_state, unmapped
    for row in rows:
        if not row or not _TASK_ID_RE.search(row[0]):
            continue
        if status_col >= len(row):
            unmapped.append('')
            continue
        raw = row[status_col]
        state = map_status(raw)
        if state is None:
            unmapped.append(raw)
        else:
            by_state[state] = by_state.get(state, 0) + 1
    return by_state, unmapped


# ---------------------------------------------------------------------------------------------
# v2 lifecycle ledger: attempts/rework sums over `finish` rows (resource-usage.tmpl.md,
# references/guides/usage-observability.md).
# ---------------------------------------------------------------------------------------------

_INTEGER_RE = re.compile(r'^\d+$')


def find_ledger_table(text):
    """The v2 table's (header, rows), read only after its own 'Schema: tackle-observability/2'
    declaration (a legacy 8-column table may sit above it in the same file), or None."""
    lines = unfenced_lines(text)
    marker = next((i for i, line in enumerate(lines) if line.strip() == 'Schema: tackle-observability/2'), None)
    if marker is None:
        return None
    for i in range(marker, len(lines) - 1):
        if not lines[i].strip().startswith('|') or not is_delimiter_row(lines[i + 1]):
            continue
        header = split_row(lines[i])
        if header and {'Event', 'Attempts', 'Rework'} <= set(header):
            rows = []
            j = i + 2
            while j < len(lines):
                cells = split_row(lines[j])
                if cells is None:
                    break
                rows.append(cells)
                j += 1
            return header, rows
    return None


def sum_finish_column(header, rows, column_name):
    """(value, rows_used, rows_skipped) for one column, over `finish` rows only. A non-finish row
    is neither used nor skipped: it is outside the counted population."""
    idx = column_index(header, column_name)
    event_idx = column_index(header, 'Event')
    total, used, skipped = 0, 0, 0
    for row in rows:
        if idx is None or event_idx is None or max(idx, event_idx) >= len(row):
            continue
        if row[event_idx].strip() != 'finish':
            continue
        cell = row[idx].strip()
        if _INTEGER_RE.fullmatch(cell):
            total += int(cell)
            used += 1
        else:
            skipped += 1
    return (total if used > 0 else 'n/a'), used, skipped


# ---------------------------------------------------------------------------------------------
# Reopenings: strict "- <task id> -> <State>" history lines only. Stay mechanical: report only what
# a record of this exact shape can support, rather than guess at a transition written some other way.
# ---------------------------------------------------------------------------------------------

_REOPEN_LINE_RE = re.compile(r'^-\s*([PT]-\d+)\s*→\s*(.+?)\s*$')
_EARLIER_STATES = ('Draft', 'Ready to run', 'In progress', 'Checking')
_STATES_BY_LENGTH = tuple(sorted(VALID_STATES, key=len, reverse=True))


def count_reopenings(history_text):
    """The number of "- <id> -> <State>" lines where the same id's previously recorded state (via
    an earlier matching line) was Complete and the new state is an earlier one in the main
    Draft -> ... -> Complete progression. Returns 'n/a' when no line has the exact shape at all.
    This intentionally never matches a from-state-carrying line like "- T-01 In progress ->
    Complete." or a transition narrated in prose instead of this bullet shape, however real the
    underlying event was: see eval/field-report/README.md for the resulting, deliberate undercount."""
    last_state = {}
    reopenings = 0
    matched_any = False
    for line in unfenced_lines(history_text):
        match = _REOPEN_LINE_RE.match(line)
        if not match:
            continue
        task_id, rest = match.group(1), match.group(2)
        state = next((name for name in _STATES_BY_LENGTH if rest.startswith(name)), None)
        if state is None:
            continue
        matched_any = True
        if last_state.get(task_id) == 'Complete' and state in _EARLIER_STATES:
            reopenings += 1
        last_state[task_id] = state
    return reopenings if matched_any else 'n/a'


# ---------------------------------------------------------------------------------------------
# Telemetry sidecar: sums per scope (references/guides/usage-observability.md: "Session/account
# data is never allocated, divided, or delta-inferred into a role" and "Compare only the same
# metric, unit, scope, collector semantics, and pricing basis" -- scopes are never mixed).
# Within a scope, a repeated capture of the same scope_id is de-duplicated to its latest
# captured_at before summing across distinct scope_ids: some real captures carry a
# provenance.completeness value of "session snapshot at capture", which this tool reads as a sign
# that a later capture for the same scope_id supersedes an earlier one rather than adding to it.
# ---------------------------------------------------------------------------------------------

_TOKEN_METRICS = ('input_tokens', 'output_tokens', 'cache_read_tokens', 'cache_write_tokens')


def sum_telemetry(jsonl_text):
    """{scope: {metric: sum_or_n/a, ...}, ...}, or 'n/a' if nothing usable was found."""
    latest = {}
    for line in jsonl_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if not isinstance(obj, dict):
            continue
        scope, scope_id = obj.get('scope'), obj.get('scope_id')
        if not isinstance(scope, str) or not isinstance(scope_id, str):
            continue
        captured_at = obj.get('captured_at') if isinstance(obj.get('captured_at'), str) else ''
        key = (scope, scope_id)
        existing = latest.get(key)
        if existing is None or captured_at > existing[0]:
            latest[key] = (captured_at, obj)
    values_by_scope = {}
    for (scope, _scope_id), (_captured_at, obj) in latest.items():
        metrics = obj.get('metrics') if isinstance(obj.get('metrics'), dict) else {}
        bucket = values_by_scope.setdefault(scope, {m: [] for m in _TOKEN_METRICS})
        for m in _TOKEN_METRICS:
            v = metrics.get(m)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                bucket[m].append(v)
    if not values_by_scope:
        return 'n/a'
    return {scope: {m: (sum(values) if values else 'n/a') for m, values in metrics.items()}
            for scope, metrics in sorted(values_by_scope.items())}


# ---------------------------------------------------------------------------------------------
# Per-workspace assembly: root-level files only, with the legacy name read exactly like its
# current replacement (references/guides/usage-observability.md's "Legacy compatibility").
# ---------------------------------------------------------------------------------------------

def read_root_file(workspace_dir, *names):
    """The text of the first of `names` that exists directly inside workspace_dir, and that name;
    (None, None) if none exist. Never recurses into a subdirectory."""
    for name in names:
        candidate = workspace_dir / name
        if candidate.is_file():
            try:
                return candidate.read_text(encoding='utf-8', errors='replace'), name
            except OSError:
                return None, None
    return None, None


def workspace_report(plans_arg, slug):
    workspace_dir = Path(plans_arg) / slug

    def source(filename):
        return str(PurePosixPath(plans_arg) / slug / filename) if filename else None

    root_texts = {}
    for name in ('plan.md', 'board.md', 'task-board.md'):
        text, found = read_root_file(workspace_dir, name)
        if found:
            root_texts[found] = text
    bucket, bucket_file = detect_bucket(root_texts)

    if bucket_file and bucket_file in ('board.md', 'task-board.md'):
        by_state, unmapped = count_tasks(root_texts[bucket_file])
        tasks = {'value': by_state, 'source': source(bucket_file), 'unmapped': unmapped}
    else:
        tasks = {'value': 'n/a', 'source': None, 'unmapped': []}

    ledger_text, ledger_file = read_root_file(workspace_dir, 'resource-usage.md', 'usage.md')
    ledger_table = find_ledger_table(ledger_text) if ledger_text is not None else None
    if ledger_table:
        header, rows = ledger_table
        a_value, a_used, a_skipped = sum_finish_column(header, rows, 'Attempts')
        r_value, r_used, r_skipped = sum_finish_column(header, rows, 'Rework')
        attempts = {'value': a_value, 'rows_used': a_used, 'rows_skipped': a_skipped, 'source': source(ledger_file)}
        rework = {'value': r_value, 'rows_used': r_used, 'rows_skipped': r_skipped, 'source': source(ledger_file)}
    else:
        attempts = {'value': 'n/a', 'rows_used': 0, 'rows_skipped': 0, 'source': None}
        rework = {'value': 'n/a', 'rows_used': 0, 'rows_skipped': 0, 'source': None}

    history_text, history_file = read_root_file(workspace_dir, 'history.md', 'log.md')
    if history_text is not None:
        reopenings = {'value': count_reopenings(history_text), 'source': source(history_file)}
    else:
        reopenings = {'value': 'n/a', 'source': None}

    telemetry_text, telemetry_file = read_root_file(
        workspace_dir, 'resource-usage.telemetry.jsonl', 'usage.telemetry.jsonl')
    if telemetry_text is not None:
        tokens = {'value': sum_telemetry(telemetry_text), 'source': source(telemetry_file)}
    else:
        tokens = {'value': 'n/a', 'source': None}

    return {
        'bucket': {'value': bucket, 'source': source(bucket_file)},
        'tasks': tasks,
        'attempts': attempts,
        'rework': rework,
        'reopenings': reopenings,
        'tokens': tokens,
    }


# ---------------------------------------------------------------------------------------------
# Repository-wide effort split: `git log --numstat` over the since..until range (since exclusive,
# until inclusive -- ordinary git double-dot range semantics).
# ---------------------------------------------------------------------------------------------

CLASSES = ('skill', 'evaluation', 'maintenance', 'other')
_MAINTENANCE_FILES = ('MAINTAINING.md', 'CHANGELOG.md', 'README.md')
_MAINTENANCE_DIRS = ('maintaining/', 'extras/', '.github/')


def classify_path(path):
    if path == 'SKILL.md' or path.startswith('references/'):
        return 'skill'
    if path.startswith('eval/'):
        return 'evaluation'
    if path in _MAINTENANCE_FILES or path.startswith(_MAINTENANCE_DIRS):
        return 'maintenance'
    return 'other'


def run_git(repo, *args):
    return subprocess.run(['git', '-C', str(repo)] + list(args), capture_output=True, text=True)


def resolve_commit(repo, rev):
    """The full sha rev resolves to (as a commit), or None if it does not resolve."""
    result = run_git(repo, 'rev-parse', '--verify', '--end-of-options', rev + '^{commit}')
    return result.stdout.strip() if result.returncode == 0 else None


def effort_split(repo, since, until):
    result = run_git(repo, '-c', 'core.quotepath=off', 'log', '--no-renames', '--numstat',
                     '--pretty=format:%x00%H', '--end-of-options', '%s..%s' % (since, until))
    if result.returncode != 0:
        return None
    lines_by_class = {c: 0 for c in CLASSES}
    commits_by_class = {c: set() for c in CLASSES}
    all_commits = set()
    for chunk in result.stdout.split('\x00'):
        rows = chunk.splitlines()
        if not rows or not rows[0].strip():
            continue
        commit_hash = rows[0].strip()
        all_commits.add(commit_hash)
        for row in rows[1:]:
            if not row.strip():
                continue
            parts = row.split('\t')
            if len(parts) != 3:
                continue
            added, deleted, path = parts
            cls = classify_path(path)
            commits_by_class[cls].add(commit_hash)
            if added != '-' and deleted != '-':
                try:
                    lines_by_class[cls] += int(added) + int(deleted)
                except ValueError:
                    pass
    total_lines = sum(lines_by_class.values())
    classes = {}
    for c in CLASSES:
        ratio = round(lines_by_class[c] / total_lines, 4) if total_lines else 'n/a'
        classes[c] = {'lines': lines_by_class[c], 'commits': len(commits_by_class[c]), 'ratio': ratio}
    return {'range': '%s..%s' % (since, until), 'classes': classes, 'total_lines': total_lines,
            'total_commits': len(all_commits)}


# ---------------------------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------------------------

def format_value(value):
    if value == 'n/a' or value is None:
        return 'n/a'
    if isinstance(value, dict):
        if not value:
            return 'n/a'
        return ', '.join('%s=%s' % (k, format_value(v)) for k, v in sorted(value.items()))
    if isinstance(value, float):
        return '%.4f' % value
    return str(value)


def render_markdown(report):
    lines = ['# Field report', '']
    repo = report['repo']
    lines.append('Revision range: `%s` (`%s`..`%s`)' % (report['effort_split']['range'],
                                                        repo['since_sha'], repo['until_sha']))
    lines.append('')
    lines.append('## Effort split')
    lines.append('')
    lines.append('The since bound is exclusive and the until bound is inclusive (`git log '
                 '<since>..<until>`), so `--since <rev>` never counts `<rev>`’s own commit. A '
                 'merge commit produces no `--numstat` rows by default and so is never attributed to '
                 'any class, even though it is still counted in the total commit count below.')
    lines.append('')
    lines.append('| Class | Lines | Commits | Ratio |')
    lines.append('|---|---|---|---|')
    for cls in CLASSES:
        row = report['effort_split']['classes'][cls]
        ratio = '%.4f' % row['ratio'] if isinstance(row['ratio'], float) else row['ratio']
        lines.append('| %s | %d | %d | %s |' % (cls, row['lines'], row['commits'], ratio))
    lines.append('')
    lines.append('Total lines: %d. Total commits: %d. Source: `git log --no-renames --numstat %s` '
                 'in `%s`.' % (report['effort_split']['total_lines'], report['effort_split']['total_commits'],
                               report['effort_split']['range'], report['repo']['path']))
    lines.append('')
    lines.append('## Workspaces')
    for slug in sorted(report['workspaces']):
        ws = report['workspaces'][slug]
        lines.append('')
        lines.append('### %s' % slug)
        lines.append('')
        lines.append('| Field | Value | Source |')
        lines.append('|---|---|---|')
        for field in ('bucket', 'tasks', 'attempts', 'rework', 'reopenings', 'tokens'):
            cell = ws[field]
            value = format_value(cell['value'])
            if field in ('attempts', 'rework') and cell['value'] != 'n/a':
                value += ' (used=%d, skipped=%d)' % (cell['rows_used'], cell['rows_skipped'])
            source = cell['source'] or 'n/a'
            lines.append('| %s | %s | %s |' % (field, value, source))
            if field == 'tasks' and cell.get('unmapped'):
                lines.append('| tasks (unmapped) | %s | %s |' % (
                    ', '.join(repr(u) for u in cell['unmapped']), source))
    lines.append('')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

def build_report(plans_arg, repo, since_sha, until_sha, since_arg, until_arg, slugs):
    workspaces = {slug: workspace_report(plans_arg, slug) for slug in slugs}
    split = effort_split(repo, since_sha, until_sha)
    return {
        'schema': SCHEMA,
        'repo': {'since': since_arg, 'until': until_arg, 'since_sha': since_sha, 'until_sha': until_sha,
                'path': str(repo)},
        'workspaces': workspaces,
        'effort_split': split,
    }


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--plans', required=True)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--since', required=True)
    parser.add_argument('--until', default='HEAD')
    parser.add_argument('--workspace', action='append', default=None)
    parser.add_argument('--json', required=True)
    parser.add_argument('--markdown', required=True)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    repo = Path(args.repo)
    is_tree = run_git(repo, 'rev-parse', '--is-inside-work-tree') if repo.is_dir() else None
    if is_tree is None or is_tree.returncode != 0 or is_tree.stdout.strip() != 'true':
        print('usage error: --repo is not a git work tree: %s' % args.repo, file=sys.stderr)
        return 2

    plans_dir = Path(args.plans)
    if not plans_dir.is_dir():
        print('usage error: --plans is not a directory: %s' % args.plans, file=sys.stderr)
        return 2

    since_sha = resolve_commit(repo, args.since)
    if since_sha is None:
        print('usage error: --since does not resolve to a commit: %s' % args.since, file=sys.stderr)
        return 2
    until_sha = resolve_commit(repo, args.until)
    if until_sha is None:
        print('usage error: --until does not resolve to a commit: %s' % args.until, file=sys.stderr)
        return 2

    if args.workspace:
        for slug in args.workspace:
            if not (plans_dir / slug).is_dir():
                print('usage error: --workspace does not exist under --plans: %s' % slug, file=sys.stderr)
                return 2
        slugs = list(args.workspace)
    else:
        slugs = sorted(p.name for p in plans_dir.iterdir() if p.is_dir())

    report = build_report(args.plans, repo, since_sha, until_sha, args.since, args.until, slugs)
    markdown = render_markdown(report)

    json_path, markdown_path = Path(args.json), Path(args.markdown)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    markdown_path.write_text(markdown, encoding='utf-8')

    print('workspaces=%d since=%s until=%s json=%s markdown=%s'
         % (len(slugs), since_sha[:12], until_sha[:12], args.json, args.markdown))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
