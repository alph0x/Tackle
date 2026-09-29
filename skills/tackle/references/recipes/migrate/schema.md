```python
import re


ID_RE = r'[PT]-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*'
ID_TOKEN = re.compile(ID_RE)
LEGACY_STATE_MAP = {
    '\U0001F534': 'Draft',
    '\U0001F7E1': 'In progress',
    '⏸': 'Blocked',
    '\U0001F7E2': 'Complete',
    '⚪': 'Skipped',
}
VALID_STATES = ('Draft', 'Ready to run', 'In progress', 'Checking', 'Complete',
                'Blocked', 'Interrupted', 'Skipped', 'Unverifiable')
TERMINAL_STATES = ('Complete', 'Blocked', 'Unverifiable')
RENAME_FILES = (
    ('board.md', 'task-board.md'),
    ('log.md', 'history.md'),
    ('log-archive.md', 'history-archive.md'),
    ('usage.md', 'resource-usage.md'),
    ('coordinator.md', 'current-work.md'),
    ('HANDOFF.md', 'handoff-brief.md'),
)
RENAME_DIRS = (
    ('evidence/', 'verification-records/'),
    ('points/', 'tasks/'),
)


def is_legacy_path(path):
    return path.split('/', 1)[0].startswith('legacy-')


def root_files(files):
    """The top-level files of a workspace: no '/' in the path, and never a legacy-*/ entry."""
    return {path: data for path, data in files.items() if '/' not in path and not is_legacy_path(path)}


def workspace_files(files):
    """Every file of a workspace except legacy-*/ snapshots (still includes nested paths)."""
    return {path: data for path, data in files.items() if not is_legacy_path(path)}


def decode(data):
    return data.decode('utf-8')


def unfenced_lines(text, strict=False):
    """Lines of text outside fenced code blocks, tracking fences exactly like candidate_board().
    With strict, a fence still open at the end raises ValueError('unclosed fenced example')."""
    fence = None
    out = []
    for line in text.splitlines():
        delimiter = re.match(r'^\s{0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if (delimiter and delimiter[1][0] == fence[0]
                    and len(delimiter[1]) >= fence[1] and not delimiter[2].strip()):
                fence = None
            continue
        if delimiter:
            fence = (delimiter[1][0], len(delimiter[1]))
            continue
        out.append(line)
    if strict and fence:
        raise ValueError('unclosed fenced example')
    return out


def schema_token(text):
    """The value after 'Schema:' on the first unfenced line that declares one, or None."""
    for line in unfenced_lines(text):
        if line.startswith('Schema:'):
            return line[len('Schema:'):].strip()
    return None


def split_row(line):
    """A table row's cells (no leading/trailing empty cell), or None if not a table row."""
    if '|' not in line:
        return None
    cells = line.split('|')
    if len(cells) < 3:
        return None
    return [cell.strip() for cell in cells[1:-1]]


def is_delimiter_row(line):
    stripped = line.strip()
    return bool(re.fullmatch(r'\|?[\s:|-]+\|?', stripped)) and '-' in stripped


def board_header_has(text, id_words, status_word='Status'):
    """True if some unfenced header row (followed by a delimiter row) names a Status column and one
    of id_words (e.g. {'Point'} or {'Point', 'Task'})."""
    lines = unfenced_lines(text, strict=True)
    for i in range(len(lines) - 1):
        if not lines[i].strip().startswith('|') or not is_delimiter_row(lines[i + 1]):
            continue
        cells = split_row(lines[i])
        if cells and status_word in cells and any(word in cells for word in id_words):
            return True
    return False


def schema_of(files):
    """Bucket a workspace: 'pre-3', '3', '4', '5', 'lite', or 'unknown' (zero or 2+ matches)."""
    root = root_files(files)
    flags = {}
    if 'plan.md' in root:
        lines = decode(root['plan.md']).splitlines()
        flags['lite'] = bool(lines) and lines[0].strip() == 'Gate: Lite'
    if 'board.md' in root:
        text = decode(root['board.md'])
        token = schema_token(text)
        if token == 'tackle-workspace/3':
            flags['3'] = True
        elif token is None and board_header_has(text, {'Point', 'Task'}):
            flags['pre-3'] = True
    if 'task-board.md' in root:
        text = decode(root['task-board.md'])
        token = schema_token(text)
        if token == 'tackle-workspace/4':
            flags['4'] = True
        elif token == 'tackle-workspace/5':
            flags['5'] = True
    matches = [bucket for bucket in ('pre-3', '3', '4', '5', 'lite') if flags.get(bucket)]
    return matches[0] if len(matches) == 1 else 'unknown'


def parse_board(text):
    """(lines, header_index, header_cells, [(row_index, cells), ...]) for the first header+delimiter
    table found outside fences; raises ValueError if none exists. Row scan stops at the first
    non-table line after the header, and skips fenced examples entirely (they never reach `lines`
    as table rows because fenced content is not returned by line index here -- fenced examples are
    filtered by rebuilding the unfenced line set and mapping back to original indices)."""
    lines = text.split('\n')
    fenced = set()
    fence = None
    for index, line in enumerate(lines):
        delimiter = re.match(r'^\s{0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            fenced.add(index)
            if (delimiter and delimiter[1][0] == fence[0]
                    and len(delimiter[1]) >= fence[1] and not delimiter[2].strip()):
                fence = None
            continue
        if delimiter:
            fenced.add(index)
            fence = (delimiter[1][0], len(delimiter[1]))
            continue
    if fence:
        raise ValueError('unclosed fenced example')
    header_index = None
    for index in range(len(lines) - 1):
        if index in fenced or (index + 1) in fenced:
            continue
        if not lines[index].strip().startswith('|') or not is_delimiter_row(lines[index + 1]):
            continue
        cells = split_row(lines[index])
        if cells:
            header_index = index
            break
    if header_index is None:
        raise ValueError('no board table found')
    header = split_row(lines[header_index])
    rows = []
    index = header_index + 2
    while index < len(lines) and index not in fenced:
        cells = split_row(lines[index])
        if cells is None:
            break
        rows.append((index, cells))
        index += 1
    return lines, header_index, header, rows


def column_index(header, name):
    for i, cell in enumerate(header):
        if cell == name:
            return i
    return None


def map_ids(text, id_map):
    """Replace every occurrence of an old id with its mapped id, longest id first so a multi-segment
    id is never partly matched by a shorter prefix, and never inside a longer identifier. The
    boundary excludes only alphanumerics (not '-'): a real id is routinely followed by a '-slug' in
    file names ('P-01-lint-trust.md'), and every id already ends its own last segment at a
    non-alnum-or-end boundary, so this cannot swallow a longer, unrelated id."""
    if not id_map:
        return text
    ordered = sorted(id_map, key=len, reverse=True)
    pattern = re.compile(r'(?<![A-Za-z0-9])(?:%s)(?![A-Za-z0-9])' % '|'.join(re.escape(i) for i in ordered))
    return pattern.sub(lambda m: id_map[m.group(0)], text)


def rename_path(path, id_map):
    """Apply the migrate.md artifact-name map, then the id map, to one workspace-relative path."""
    for old, new in RENAME_DIRS:
        if path == old.rstrip('/') or path.startswith(old):
            path = new + path[len(old):]
            break
    for old, new in RENAME_FILES:
        if path == old:
            path = new
            break
    return map_ids(path, id_map)


def fix_task_heading(text):
    """Ensure a brief's first content line (skipping blank lines and an `<a id=` anchor) reads
    '# Task <id> ...', whether the source said bare '# <id> ...' or '# Point <id> ...'. Call after
    id substitution so <id> is already the new (T-) id."""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('<a id='):
            continue
        match = re.match(r'^(#\s*)(?:Point\s+)?(' + ID_RE + r')(.*)$', line)
        if match:
            lines[i] = match.group(1) + 'Task ' + match.group(2) + match.group(3)
        break
    return '\n'.join(lines)


METHODOLOGY_RE = re.compile(r'(Methodology:\s*)(Tackle \d+\.\d+(?:\.\d+)?(?: candidate)?)')


def set_methodology(text, value):
    """Replace only the version substring after 'Methodology:', keeping any bold/comment decoration.
    A no-op when the line is absent (display-only, written when present)."""
    return METHODOLOGY_RE.sub(lambda m: m.group(1) + value, text, count=1)


def terminal_reference_errors(header, rows, id_column=0):
    """Row 10's rule for a modern (schema 3/4/5) board: every Complete/Blocked/Unverifiable row's
    Verification cell is exactly 'reports/<id>-report.md'."""
    status_col = column_index(header, 'Status')
    verification_col = column_index(header, 'Verification')
    errors = []
    if status_col is None or verification_col is None:
        return ['board is missing a Status or Verification column']
    for _, cells in rows:
        if len(cells) <= max(status_col, verification_col, id_column):
            errors.append('unsupported task row: ' + ' | '.join(cells))
            continue
        status = cells[status_col]
        if status not in VALID_STATES:
            errors.append('unsupported task row status: ' + status)
            continue
        if status in TERMINAL_STATES:
            expected = 'reports/' + cells[id_column] + '-report.md'
            if cells[verification_col] != expected:
                errors.append('terminal task without verification reference: ' + cells[id_column])
    return errors


def old_names_left(after, renamed_from):
    """Any root-level artifact name a step renames away from, still present after the step."""
    present = root_files(after)
    return [name for name in renamed_from if name in present]


class PoisonContext(dict):
    """A context whose values must never be read: a true no-op re-run of transform() reaches no
    branch that needs the adoption date, Run ID or Methodology value."""

    def __getitem__(self, key):
        raise AssertionError('idempotent re-run must not read context[%r]' % (key,))

    def get(self, key, default=None):
        raise AssertionError('idempotent re-run must not read context.get(%r)' % (key,))


def adopt(files, context, transform):
    """The adoption wrapper: runs `transform` on the workspace root (legacy-*/ stripped), then
    reassembles the result with every pre-existing legacy-*/ directory carried forward unchanged,
    plus this step's own legacy-<bucket-before>/ snapshot of the untouched original root files."""
    scoped = workspace_files(files)
    bucket_before = schema_of(scoped)
    new_files, renames = transform(scoped, context)
    result = dict(new_files)
    for path, data in files.items():
        if is_legacy_path(path):
            result[path] = data
    prefix = 'legacy-%s/' % bucket_before
    for path, data in scoped.items():
        result[prefix + path] = data
    return result, renames
```
