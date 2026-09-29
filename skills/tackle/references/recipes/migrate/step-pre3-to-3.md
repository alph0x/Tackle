```python
REQUIRED_PRE3_COLUMNS = (
    ('Task or Point', ('Task', 'Point')),
    ('What', ('What',)),
    ('Brief or Briefing', ('Brief', 'Briefing')),
    ('Depends on', ('Depends on',)),
    ('Status', ('Status',)),
    ('Confidence or Verification', ('Confidence', 'Verification')),
)
PLACEHOLDER_CONFIDENCE = ('', '—', '-')


def find_column(header, names):
    for name in names:
        index = column_index(header, name)
        if index is not None:
            return index, name
    return None, None


def locate_pre3_columns(header):
    """Every column this step needs, located by header name -- never by position: a pre-3
    board's columns can appear in any order, and different workspaces spell some of them differently
    ('Brief' or 'Briefing', 'Confidence' or 'Verification'). A header this step does not fully and
    unambiguously recognize -- a required column missing, a synonym pair both present, or a header
    cell that matches none of the recognized columns -- is a named refusal, never a guess: a column
    the step does not know about may hold real content (a note, a citation) that would otherwise be
    silently dropped from the schema-3 board."""
    located, matched_names = {}, {}
    for label, names in REQUIRED_PRE3_COLUMNS:
        present = [name for name in names if column_index(header, name) is not None]
        if len(present) > 1:
            raise ValueError('unrecognized pre-3 header layout: both %s and %s present' % tuple(present[:2]))
        if present:
            located[label] = column_index(header, present[0])
            matched_names[label] = present[0]
    missing = [label for label, _ in REQUIRED_PRE3_COLUMNS if label not in located]
    if missing:
        raise ValueError('unrecognized pre-3 header layout: missing ' + ', '.join(missing))
    recognized = set(located.values())
    extra = [cell for index, cell in enumerate(header) if index not in recognized]
    if extra:
        raise ValueError('unrecognized pre-3 header layout: unrecognized column(s) ' + ', '.join(extra))
    return located, matched_names


def detect(files):
    return schema_of(files) == 'pre-3'


def transform(files, context):
    bucket = schema_of(files)
    if bucket != 'pre-3':
        if bucket in ('3', '4', '5'):
            return dict(files), {}
        raise ValueError('not a pre-3 workspace: bucket is ' + bucket)
    text = decode(files['board.md'])
    lines, header_index, header, rows = parse_board(text)
    columns, matched_names = locate_pre3_columns(header)
    id_col = columns['Task or Point']
    what_col = columns['What']
    brief_col = columns['Brief or Briefing']
    depends_col = columns['Depends on']
    status_col = columns['Status']
    confidence_col = columns['Confidence or Verification']
    confidence_is_verification = matched_names['Confidence or Verification'] == 'Verification'
    required = (id_col, what_col, brief_col, depends_col, status_col, confidence_col)
    reports = {path for path in files if path.startswith('reports/') and path.endswith('.md')}
    identities, legacy, out_rows = set(), {}, []
    for _, cells in rows:
        identity_cell = cells[id_col] if cells and id_col < len(cells) else ''
        if not cells or not re.fullmatch(ID_RE, identity_cell):
            continue  # a legend or note row shaped like a table row, not a task row
        if len(cells) <= max(required):
            raise ValueError('unsupported legacy task row: ' + ' | '.join(cells))
        identity = identity_cell
        if identity in identities:
            raise ValueError('duplicate identity: ' + identity)
        status = cells[status_col]
        if status not in LEGACY_STATE_MAP:
            raise ValueError('unsupported legacy state: ' + status)
        identities.add(identity)
        grade = cells[confidence_col]
        legacy[identity] = {'status': status, 'grade': grade}
        new_status = LEGACY_STATE_MAP[status]
        reference = 'reports/' + identity + '-report.md'
        if new_status in ('Complete', 'Blocked') and reference not in reports:
            raise ValueError('missing historical verification report: ' + identity)
        verification = reference if reference in reports else ''
        if confidence_is_verification and grade.strip() not in PLACEHOLDER_CONFIDENCE and grade.strip() != verification:
            raise ValueError(
                'unsupported legacy row: existing Verification text would be overwritten, not preserved: '
                + identity)
        what = cells[what_col]
        brief = cells[brief_col]
        depends = cells[depends_col]
        out_rows.append('| %s | %s | %s | %s | %s | %s |' % (
            identity, what, brief, depends, new_status, verification))
    if not identities:
        raise ValueError('no legacy task rows')
    new_board = ('# Task board\n\nSchema: tackle-workspace/3\n\n'
                 '| Task | What | Brief | Depends on | Status | Verification |\n'
                 '|---|---|---|---|---|---|\n' + '\n'.join(out_rows) + '\n')
    new_files = dict(files)
    new_files['board.md'] = new_board.encode('utf-8')
    if 'AGENTS.md' in files:
        new_files['AGENTS.md'] = set_methodology(decode(files['AGENTS.md']), context['methodology']).encode('utf-8')
    return new_files, legacy


def verify(before, after):
    errors, residue = [], []
    try:
        bucket = schema_of(after)
    except Exception as exc:
        return {'errors': ['could not determine bucket after transform: ' + repr(exc)], 'residue': residue}
    if bucket != '3':
        errors.append('wrong bucket after transform: ' + bucket)
    try:
        _, _, header, rows = parse_board(decode(after['board.md']))
        errors.extend(terminal_reference_errors(header, rows))
        status_col = column_index(header, 'Status')
        for _, cells in rows:
            if status_col is not None and len(cells) > status_col and cells[status_col] == 'Ready to run':
                errors.append('inferred Ready to run row: ' + cells[0])
        # Every non-status source cell (id, What, Brief, Depends on) must survive verbatim in
        # its corresponding output row, so a regression back to positional reading -- or any future
        # change that drops or scrambles a cell -- goes red here even when the input header is the
        # fixture's own standard order. Confidence/Verification is deliberately excluded: it is never
        # copied into the schema-3 board verbatim (it becomes a computed report reference, or is
        # refused in transform() when that would discard real citation text), so it has no
        # single "correct" surviving cell to compare against.
        after_id_col = column_index(header, 'Task')
        after_what_col = column_index(header, 'What')
        after_brief_col = column_index(header, 'Brief')
        after_depends_col = column_index(header, 'Depends on')
        after_by_id = {}
        if after_id_col is not None:
            for _, cells in rows:
                if cells and after_id_col < len(cells) and re.fullmatch(ID_RE, cells[after_id_col]):
                    after_by_id[cells[after_id_col]] = cells
        _, _, before_header, before_rows = parse_board(decode(before['board.md']))
        before_columns, _ = locate_pre3_columns(before_header)
        before_id_col = before_columns['Task or Point']
        source_columns = (
            ('What', before_columns['What'], after_what_col),
            ('Brief', before_columns['Brief or Briefing'], after_brief_col),
            ('Depends on', before_columns['Depends on'], after_depends_col),
        )
        for _, cells in before_rows:
            identity_cell = cells[before_id_col] if cells and before_id_col < len(cells) else ''
            if not cells or not re.fullmatch(ID_RE, identity_cell):
                continue
            target_cells = after_by_id.get(identity_cell)
            if target_cells is None:
                errors.append('row dropped by transform: ' + identity_cell)
                continue
            for column_name, before_col, after_col in source_columns:
                expected = cells[before_col] if before_col < len(cells) else ''
                actual = (target_cells[after_col] if after_col is not None and after_col < len(target_cells)
                          else None)
                if actual != expected:
                    errors.append('row %s: %s cell changed or dropped by transform (expected %r, got %r)' % (
                        identity_cell, column_name, expected, actual))
    except ValueError as exc:
        errors.append('board invariant: ' + str(exc))
    try:
        second, renames_again = transform(after, PoisonContext())
    except Exception as exc:
        errors.append('second transform is not a no-op: ' + repr(exc))
    else:
        if second != after or renames_again != {}:
            errors.append('second transform is not a byte-identical no-op')
    return {'errors': errors, 'residue': residue}
```
