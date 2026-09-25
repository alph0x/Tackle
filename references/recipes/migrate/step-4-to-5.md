```python
PLACEHOLDER_VERIFICATION = ('pending', '', '—', '-')
DEFAULT_READY_TEXT = 'ready: legacy /4 readiness'


def detect(files):
    return schema_of(files) == '4'


def transform(files, context):
    bucket = schema_of(files)
    if bucket != '4':
        if bucket == '5':
            return dict(files), {}
        raise ValueError('not a /4 workspace: bucket is ' + bucket)
    text = decode(files['task-board.md'])
    lines, header_index, header, rows = parse_board(text)
    status_col = column_index(header, 'Status')
    verification_col = column_index(header, 'Verification')
    if status_col is None or verification_col is None:
        raise ValueError('board is missing a Status or Verification column')
    for _, cells in rows:
        if len(cells) <= max(status_col, verification_col):
            raise ValueError('unsupported task row: ' + ' | '.join(cells))
        if cells[status_col] not in VALID_STATES:
            raise ValueError('unsupported task row status: ' + cells[status_col])
    changed = []
    for index, cells in rows:
        if cells[status_col] != 'Ready to run':
            continue
        cell = cells[verification_col]
        if cell.startswith('ready: ') and cell[len('ready: '):].strip():
            continue
        if cell.strip() in PLACEHOLDER_VERIFICATION:
            cells[verification_col] = DEFAULT_READY_TEXT
            lines[index] = '| ' + ' | '.join(cells) + ' |'
            changed.append(cells[0])
    new_text = '\n'.join(lines)
    new_text = re.sub(r'^Schema: tackle-workspace/4$', 'Schema: tackle-workspace/5', new_text, flags=re.M)
    new_files = dict(files)
    new_files['task-board.md'] = new_text.encode('utf-8')
    if 'AGENTS.md' in files:
        new_files['AGENTS.md'] = set_methodology(decode(files['AGENTS.md']), context['methodology']).encode('utf-8')
    return new_files, {'defaulted_ready_rows': changed}


def verify(before, after):
    errors, residue = [], []
    try:
        bucket = schema_of(after)
    except Exception as exc:
        return {'errors': ['could not determine bucket after transform: ' + repr(exc)], 'residue': residue}
    if bucket != '5':
        errors.append('wrong bucket after transform: ' + bucket)
    try:
        _, _, header, rows = parse_board(decode(after['task-board.md']))
        status_col = column_index(header, 'Status')
        verification_col = column_index(header, 'Verification')
        id_col = column_index(header, 'Task') or 0
        for _, cells in rows:
            if status_col is None or verification_col is None:
                errors.append('board is missing a Status or Verification column')
                break
            if cells[status_col] == 'Ready to run':
                cell = cells[verification_col]
                if not (cell.startswith('ready: ') and cell[len('ready: '):].strip()):
                    residue.append(cells[id_col] + ': Ready to run row has non-standard Verification '
                                    'text %r; not overwritten (would destroy a possible citation).' % cell)
    except ValueError as exc:
        errors.append('board invariant: ' + str(exc))
    try:
        second, changed_again = transform(after, PoisonContext())
    except Exception as exc:
        errors.append('second transform is not a no-op: ' + repr(exc))
    else:
        if second != after or changed_again != {}:
            errors.append('second transform is not a byte-identical no-op')
    return {'errors': errors, 'residue': residue}
```
