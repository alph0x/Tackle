```python
PAIRS = (
    ('board.md', 'task-board.md'),
    ('log-archive.md', 'history-archive.md'),
    ('log.md', 'history.md'),
    ('usage.md', 'resource-usage.md'),
    ('coordinator.md', 'current-work.md'),
    ('HANDOFF.md', 'handoff-brief.md'),
    ('evidence/', 'verification-records/'),
    ('points/', 'tasks/'),
    ('Point decomposition', 'Task decomposition'),
)
UNTOUCHED = ('decisions.md', 'design-contract.md')
HISTORY_ADOPTION_MARKER = 'adoption · migrated to schema tackle-workspace/4'
# A real adoption entry is the exact '## <date> · <marker>' heading transform() itself
# writes below -- matched line by line via unfenced_lines() (so a quoted heading inside a fenced
# example never counts), never a bare substring match anywhere in the file. A bare substring also
# matches an unrelated line that merely quotes the marker phrase (e.g. a session note discussing
# this migration tooling itself) and would silently suppress this run's real entry.
_HISTORY_ADOPTION_HEADING_RE = re.compile(r'## \S+ · ' + re.escape(HISTORY_ADOPTION_MARKER))


def _has_real_adoption_entry(text):
    """True if `text` already carries the real '## <date> · <marker>' adoption heading."""
    return any(_HISTORY_ADOPTION_HEADING_RE.fullmatch(line) for line in unfenced_lines(text))


# Every artifact this step renames, derived from schema.md's own RENAME_FILES/RENAME_DIRS so
# the AGENTS.md residue scan below can never silently drift out of sync with a token those tables add
# or remove. (PAIRS above is not the source here: its one extra entry, 'Point decomposition', is a
# prose phrase, not a renamed artifact.)
STALE_ARTIFACT_NAMES = tuple(old for old, _ in RENAME_FILES + RENAME_DIRS)
_NAME_BOUNDARY = '[A-Za-z0-9_-]'


def _name_alternative(token):
    """One boundary-guarded alternation branch for `token`: excludes a preceding or
    following identifier character so the token is never matched as part of a longer compound name --
    'usage.md' inside 'resource-usage.md', 'board.md' inside 'task-board.md', 'log.md' inside an
    unrelated 'backlog.md'. A directory prefix (ends in '/') gets no trailing guard: it is always
    followed by the rest of a path, which is exactly the identifier content the guard exists to
    exclude for a file name."""
    lookahead = '' if token.endswith('/') else '(?!%s)' % _NAME_BOUNDARY
    return '(?<!%s)%s%s' % (_NAME_BOUNDARY, re.escape(token), lookahead)


_PAIRS_MAP = dict(PAIRS)
_PAIRS_PATTERN = re.compile('|'.join(
    _name_alternative(old) for old, _ in sorted(PAIRS, key=lambda pair: len(pair[0]), reverse=True)))
_STALE_NAME_PATTERN = re.compile('|'.join(
    _name_alternative(name) for name in sorted(STALE_ARTIFACT_NAMES, key=len, reverse=True)))


def detect(files):
    return schema_of(files) == '3'


def build_id_map(header, rows):
    id_col = column_index(header, 'Task')
    if id_col is None:
        id_col = 0
    id_map, seen_targets, seen_ids = {}, {}, set()
    for _, cells in rows:
        if not cells or id_col >= len(cells) or not re.fullmatch(ID_RE, cells[id_col]):
            continue
        identity = cells[id_col]
        if identity in seen_ids:
            raise ValueError('duplicate identity: ' + identity)
        seen_ids.add(identity)
        target = identity if identity.startswith('T-') else 'T-' + identity[len('P-'):]
        if target in seen_targets and seen_targets[target] != identity:
            raise ValueError('duplicate identity after mapping: ' + target)
        seen_targets[target] = identity
        if target != identity:
            id_map[identity] = target
    return id_map


def rewrite_content(text, id_map):
    """Rewrite every PAIRS artifact-name mention, then every mapped id -- each in one single,
    boundary-guarded regex pass over the original text, never a chain of independent `str.replace`
    calls (that naive chain turns pre-existing 'resource-usage.md' into
    'resource-resource-usage.md', because 'usage.md' is a literal substring of it). `map_ids` already
    applies this same one-pass, longest-id-first technique for ids, so a short id such as 'P-1' can
    never swallow part of a longer one such as 'P-10'."""
    text = _PAIRS_PATTERN.sub(lambda m: _PAIRS_MAP[m.group(0)], text)
    return map_ids(text, id_map)


def is_rewritten(new_path):
    return (new_path == 'task-board.md' or new_path == 'plan.md' or new_path == 'resource-usage.md'
            or ((new_path.startswith('tasks/') or new_path.startswith('reports/')) and new_path.endswith('.md')))


def transform(files, context):
    bucket = schema_of(files)
    if bucket != '3':
        if bucket in ('4', '5'):
            return dict(files), {}
        raise ValueError('not a /3 workspace: bucket is ' + bucket)
    lines, header_index, header, rows = parse_board(decode(files['board.md']))
    status_col = column_index(header, 'Status')
    verification_col = column_index(header, 'Verification')
    if status_col is None or verification_col is None:
        raise ValueError('board is missing a Status or Verification column')
    for _, cells in rows:
        if not cells or not re.fullmatch(ID_RE, cells[0]):
            continue
        if len(cells) <= max(status_col, verification_col):
            raise ValueError('unsupported task row: ' + ' | '.join(cells))
        if cells[status_col] not in VALID_STATES:
            raise ValueError('unsupported task row status: ' + cells[status_col])
    id_map = build_id_map(header, rows)

    # Every source path's final destination is computed up front, into one map, before
    # anything is written. Two different sources reaching the same target -- an old name and its new
    # name both already present (usage.md + resource-usage.md, board.md + task-board.md, log.md +
    # history.md, points/X + tasks/X) -- is a named refusal, never a silent overwrite of one by the
    # other. Because rename_path() sends both 'log.md' and a pre-existing 'history.md' to the same
    # 'history.md' target, that pair is caught here too, with no separate special case needed.
    renamable = [path for path in files if path not in UNTOUCHED]
    new_paths, claimed_by = {}, {}
    for path in renamable:
        new_path = rename_path(path, id_map)
        new_paths[path] = new_path
        if new_path in claimed_by:
            raise ValueError('rename target collision: %s and %s both map to %s' % (
                claimed_by[new_path], path, new_path))
        claimed_by[new_path] = path

    new_files = {}
    for path in renamable:
        new_path = new_paths[path]
        data = files[path]
        if path == 'AGENTS.md':
            new_files[new_path] = set_methodology(decode(data), context['methodology']).encode('utf-8')
        elif new_path == 'history.md':
            # log.md's or history.md's own bytes, untouched (never id-mapped or PAIRS-
            # rewritten) -- the adoption entry is appended below, once collision detection above has
            # already confirmed there is exactly one source for this target.
            new_files[new_path] = data
        elif is_rewritten(new_path):
            text = rewrite_content(decode(data), id_map)
            if new_path.startswith('tasks/'):
                text = fix_task_heading(text)
            if new_path == 'task-board.md':
                text = re.sub(r'^Schema: tackle-workspace/3$', 'Schema: tackle-workspace/4', text, flags=re.M)
            new_files[new_path] = text.encode('utf-8')
        else:
            new_files[new_path] = data
    for path in UNTOUCHED:
        if path in files:
            new_files[path] = files[path]

    # Only log.md exists -> rename it and append one entry; only history.md exists -> keep it
    # and append one entry; both exist -> already refused above as a collision. The heading
    # check runs before context is touched at all, so a genuine no-op re-run (which never reaches this
    # branch, since bucket is no longer '3') and a workspace that already carries the entry both leave
    # it written exactly once.
    if 'history.md' in new_files:
        original = decode(new_files['history.md'])
        if not _has_real_adoption_entry(original):
            summary = ', '.join('%s→%s' % (old, new) for old, new in sorted(id_map.items())) or 'no P-ids to map'
            entry = ('\n## %s · %s\n\n'
                     '- Adopted the v8.3 → v8.4 layout (Run %s): %s.\n') % (
                context['date'], HISTORY_ADOPTION_MARKER, context['run_id'], summary)
            new_files['history.md'] = (original + entry).encode('utf-8')
    return new_files, id_map


def verify(before, after):
    errors, residue = [], []
    try:
        bucket = schema_of(after)
    except Exception as exc:
        return {'errors': ['could not determine bucket after transform: ' + repr(exc)], 'residue': residue}
    if bucket != '4':
        errors.append('wrong bucket after transform: ' + bucket)
    stale = old_names_left(after, ['board.md', 'log.md', 'log-archive.md', 'usage.md',
                                    'coordinator.md', 'HANDOFF.md'])
    errors.extend('old artifact name left in root: ' + name for name in stale)
    if any(path.startswith('points/') for path in after):
        errors.append('old artifact name left in root: points/')
    if any(path.startswith('evidence/') and not is_legacy_path(path) for path in after):
        errors.append('old artifact name left in root: evidence/')
    header, rows = None, None
    if 'task-board.md' in after:
        try:
            _, _, header, rows = parse_board(decode(after['task-board.md']))
            id_col = column_index(header, 'Task')
            errors.extend(terminal_reference_errors(header, rows, id_column=id_col if id_col is not None else 0))
        except ValueError as exc:
            errors.append('board invariant: ' + str(exc))
    else:
        errors.append('old artifact name left in root: board.md (task-board.md missing)')
    leftover = set()
    for path, data in after.items():
        if path in ('task-board.md', 'plan.md', 'resource-usage.md') or (
                (path.startswith('tasks/') or path.startswith('reports/')) and path.endswith('.md')):
            leftover.update(re.findall(r'\bP-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b', decode(data)))
    residue.extend('P-id mention left in rewritten content: ' + identity for identity in sorted(leftover))
    if 'AGENTS.md' in after:
        # AGENTS.md's own prose is never rewritten (only its Methodology line is), so a stale
        # artifact name or old id it already named survives untouched -- residue for a human to review,
        # boundary-guarded the same way rewrite_content() is, so 'task-board.md'/'resource-usage.md'
        # mentions are not misread as the old 'board.md'/'usage.md'.
        agents_text = decode(after['AGENTS.md'])
        stale_names = sorted(set(_STALE_NAME_PATTERN.findall(agents_text)))
        residue.extend('AGENTS.md still names the old artifact: ' + name for name in stale_names)
        agents_ids = sorted(set(re.findall(r'\bP-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b', agents_text)))
        residue.extend('AGENTS.md still mentions the old id: ' + identity for identity in agents_ids)
    if header is not None and rows is not None:
        status_col = column_index(header, 'Status')
        id_col = column_index(header, 'Task')
        id_col = id_col if id_col is not None else 0
        for _, cells in rows:
            if status_col is not None and len(cells) > status_col and cells[status_col] == 'Interrupted':
                residue.append(cells[id_col] + " is Interrupted; adopt this workspace only at that "
                                "task's own boundary (R-MIGRATE-02).")
    try:
        second, id_map_again = transform(after, PoisonContext())
    except Exception as exc:
        errors.append('second transform is not a no-op: ' + repr(exc))
    else:
        if second != after or id_map_again != {}:
            errors.append('second transform is not a byte-identical no-op')
    return {'errors': errors, 'residue': residue}
```
