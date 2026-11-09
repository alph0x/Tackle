#!/usr/bin/env python3
"""Write workspace records from a tackle-record/1 JSON specification."""
import sys
sys.dont_write_bytecode = True
import argparse
import datetime
import errno
import fcntl
import hashlib
import json
import math
import os
import re
import stat
import uuid


class Refusal(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refusal(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict), 'expected object')
    require(set(required) <= set(value) and set(value) <= set(required) | set(optional), 'invalid fields')


def scalar(value, name='value'):
    require(isinstance(value, str) and value.strip() == value and bool(value) and not any(c in value for c in '\r\n|'), 'invalid ' + name)
    return value


def relative(value):
    scalar(value, 'path')
    require(not value.startswith('/') and all(part not in ('', '.', '..') for part in value.split('/')), 'invalid relative path')
    return value


def reference(value):
    scalar(value, 'reference')
    if value == 'n/a':
        return value
    match = re.fullmatch(r'(?:\[[^\]\r\n]+\]\()?([A-Za-z0-9_.\-/]+(?:#[A-Za-z0-9_.-]+)?)(?:\))?', value)
    require(match is not None, 'invalid reference')
    target = match.group(1).split('#', 1)[0]
    relative(target)
    require('.md' in target or '/' in target, 'invalid reference')
    return value


def append(text, added):
    return text + ('' if not text or text.endswith('\n') else '\n') + added


def _umask():
    if not hasattr(_umask, 'value'):
        old = os.umask(0)
        os.umask(old)
        _umask.value = old
    return _umask.value


class Workspace:
    def __init__(self, path):
        require(os.path.isabs(path), 'workspace must be absolute')
        # Walk from the filesystem root, refusing links in every component.
        parts = [p for p in path.split('/') if p]
        require(all(p not in ('.', '..') for p in parts), 'invalid workspace')
        fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in parts:
                new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = new
            fcntl.flock(fd, fcntl.LOCK_EX)
        except BaseException:
            os.close(fd)
            raise
        self.fd = fd

    def close(self):
        os.close(self.fd)

    def parent(self, path):
        parts = relative(path).split('/')
        fd = os.dup(self.fd)
        try:
            for part in parts[:-1]:
                new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = new
            return fd, parts[-1]
        except BaseException:
            os.close(fd)
            raise

    def read(self, path, optional=False):
        fd, name = self.parent(path)
        try:
            try:
                child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            except FileNotFoundError:
                if optional:
                    return None
                raise
            try:
                require(stat.S_ISREG(os.fstat(child).st_mode), 'not a regular file: ' + path)
                with os.fdopen(child, 'rb') as stream:
                    child = -1
                    return stream.read()
            finally:
                if child != -1:
                    os.close(child)
        finally:
            os.close(fd)

    def text(self, path, optional=False):
        data = self.read(path, optional)
        if data is None:
            return None
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            raise Refusal('invalid UTF-8: ' + path)

    def check_target(self, path):
        fd, name = self.parent(path)
        try:
            try:
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                return
            require(stat.S_ISREG(info.st_mode), 'not a regular target: ' + path)
        finally:
            os.close(fd)

    def write(self, path, content):
        fd, name = self.parent(path)
        tmp = '.record-' + uuid.uuid4().hex
        created = False
        try:
            try:
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                info = None
            require(info is None or stat.S_ISREG(info.st_mode), 'not a regular target: ' + path)
            child = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            created = True
            with os.fdopen(child, 'wb') as stream:
                stream.write(content)
                stream.flush()
                os.fchmod(stream.fileno(), stat.S_IMODE(info.st_mode) & 0o777 if info else 0o666 & ~_umask())
                os.fsync(stream.fileno())
            os.replace(tmp, name, src_dir_fd=fd, dst_dir_fd=fd)
            created = False
        finally:
            if created:
                os.unlink(tmp, dir_fd=fd)
            os.close(fd)


def table(text, needed):
    lines = text.splitlines(keepends=True)
    for i in range(len(lines) - 1):
        if not lines[i].lstrip().startswith('|'):
            continue
        cols = [x.strip() for x in lines[i].strip().strip('|').split('|')]
        sep = [x.strip() for x in lines[i+1].strip().strip('|').split('|')]
        if set(needed) <= set(cols) and len(cols) == len(sep) and all(re.fullmatch(r':?-+:?', x) for x in sep):
            end = i + 2
            while end < len(lines) and lines[end].lstrip().startswith('|'):
                end += 1
            return lines, cols, i + 2, end
    raise Refusal('missing table')


def cells(line):
    return [x.strip() for x in line.strip().strip('|').split('|')]


def board_info(ws):
    board = ws.text('task-board.md')
    lines, columns, start, end = table(board, ('Task', 'Brief', 'Verification', 'Status'))
    tasks = {}
    for i in range(start, end):
        values = cells(lines[i])
        if len(values) == len(columns):
            task = values[columns.index('Task')]
            if re.fullmatch(r'[PT]-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*', task):
                require(task not in tasks, 'duplicate task')
                tasks[task] = (i, values)
    obligations = {}
    try:
        olines, cols, first, last = table(board, ('Obligation', 'State'))
    except Refusal:
        return board, lines, columns, tasks, obligations
    for line in olines[first:last]:
        values = cells(line)
        require(len(values) == len(cols), 'malformed obligation')
        oid = values[cols.index('Obligation')]
        state = values[cols.index('State')]
        require(re.fullmatch(r'O-[0-9][0-9]', oid) and oid not in obligations and state in ('Open', 'Discharged', 'Withdrawn'), 'invalid obligation')
        obligations[oid] = state
    return board, lines, columns, tasks, obligations


def id_value(value, name):
    scalar(value, name)
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.\-/]*', value) is not None, 'invalid ' + name)
    if name in ('event id', 'event_id'):
        require('/' not in value, 'invalid event id')
    return value


def visible_text(text, reader='markdown'):
    """Mask code without moving offsets, using the exact destination grammar."""
    assert reader in ('markdown', 'counter', 'seal')
    lines = []
    marker = ''
    for line in text.splitlines(keepends=True):
        boundary = False
        if reader != 'markdown':
            boundary = line.strip().startswith(('```', '~~~')) if reader == 'counter' else line.startswith('```')
            if boundary:
                marker = '' if marker else reader
        else:
            unindented = re.sub(r'^ {0,3}', '', line)
            if marker:
                count = len(unindented) - len(unindented.lstrip(marker[0]))
                if count >= len(marker) and not unindented[count:].strip():
                    marker = ''
                    boundary = True
            else:
                match = re.match(r'(`{3,}|~{3,})', unindented)
                if match:
                    marker = match.group()
                    boundary = True
        lines.append(re.sub(r'[^\r\n]', ' ', line) if marker or boundary else line)
    return ''.join(lines)


def append_record(text, added, reader='markdown'):
    candidate = append(text, added)
    visible = visible_text(candidate).endswith(added)
    if reader != 'markdown':
        visible = visible and visible_text(candidate, reader=reader).endswith(added)
    require(visible, 'record would be hidden by the destination consumer fence state')
    return candidate


RECORD_ALIASES = {'task': 'taskid', 'fault': 'failureid', 'observedfailure': 'observed',
                  'repair': 'correction', 'check': 'validationcommand'}


def records(text):
    result = []
    record = None
    for line in visible_text(text, reader='counter').splitlines():
        raw = line.strip()
        match = re.match(r'^###\s+Event\s+(.+)$', raw)
        if re.match(r'^#{1,3}\s', raw):
            if record is not None:
                result.append(record)
            record = {'eventid': match.group(1).strip()} if match else None
            continue
        if ':' not in raw:
            continue
        key, val = raw.split(':', 1)
        key = re.sub(r'[\s*_\-]', '', key.lower())
        key = RECORD_ALIASES.get(key, key)
        if key not in ('taskid', 'eventid', 'runid', 'kind', 'failureid', 'observed', 'correction', 'validationcommand', 'result', 'authorization'):
            continue
        if record is None:
            record = {}
        if (key == 'taskid' and record.get('taskid') and record.get('eventid')) or (key == 'eventid' and record.get('eventid') and record['eventid'] != val.strip()):
            result.append(record)
            record = {}
        record[key] = val.strip()
    if record is not None:
        result.append(record)
    return result


def reference_parts(ref):
    if ref == 'n/a':
        return None, ''
    if ref.startswith('['):
        ref = ref[ref.index('](')+2:-1]
    path, _, anchor = ref.partition('#')
    return path, re.sub(r'^event-', '', anchor)


def evidence(ws, source, verification, task, run):
    seen, absence, escalation = set(), False, False
    refs = []
    for ref in (source, verification):
        if ref != 'n/a':
            path, anchor = reference_parts(ref)
            refs.append((path, anchor))
    for path, anchor in refs:
        text = ws.text(path, optional=True)
        if text is None:
            continue
        for rec in records(text):
            eid = rec.get('eventid', '')
            if not eid or (anchor and anchor != eid) or rec.get('taskid') != task:
                continue
            kind = rec.get('kind', '')
            if kind == 'observed-absence':
                absence |= rec.get('runid') == run and bool(rec.get('observed'))
                continue
            if eid in seen:
                continue
            observed = rec.get('observed', '')
            result = rec.get('result', '')
            if kind == 'declared-capability-escalation':
                auth = rec.get('authorization', '')
                if escalation or not re.fullmatch(r'tasks/[A-Za-z0-9._-]+\.md', auth):
                    continue
                brief = ws.text(auth, optional=True)
                if brief:
                    brief = '\n'.join(line.strip() for line in visible_text(brief, reader='counter').splitlines())
                if brief and re.search(r'^# Task ' + re.escape(task) + r'(?:[ \t]|:|-|$)', brief, re.M) and re.search(r'^[-*+]?[ \t]*(?:\*\*)?Escalation(?:\*\*)?:[ \t]*declared[ \t]*$', brief, re.M) and observed and result:
                    escalation = True
                    seen.add(eid)
                continue
            fault = rec.get('failureid', '')
            repair = rec.get('correction', '')
            check = rec.get('validationcommand', '')
            failure = re.search(r'(^failed(?:\s|;|$)|exit\s*[1-9][0-9]*|nonzero)', result) if result else re.search(r'(exit\s*[1-9][0-9]*|nonzero)', check)
            if kind in ('', 'correction-validation') and fault not in ('', 'n/a') and observed and repair and check and failure:
                seen.add(eid)
    return len(seen), absence


METRICS = {'input_tokens', 'output_tokens', 'reasoning_tokens', 'cache_read_tokens', 'cache_write_tokens', 'requests', 'tool_calls', 'compactions', 'context_tokens', 'cost', 'currency'}


def telemetry(data, run=None):
    fields(data, ('captured_at', 'collector', 'source', 'scope', 'scope_id', 'run_id', 'metrics', 'provenance'))
    for k in ('captured_at', 'collector', 'source', 'scope', 'scope_id', 'run_id'):
        scalar(data[k], k)
    require(data['scope'] in ('role', 'session', 'account'), 'invalid telemetry scope')
    require((data['scope'] == 'role' and data['run_id'] != 'n/a') or (data['scope'] != 'role' and data['run_id'] == 'n/a'), 'invalid telemetry mapping')
    if run is not None:
        require(data['scope'] == 'role' and data['run_id'] == run, 'mismatched telemetry run')
    require(isinstance(data['provenance'], (str, dict)) and bool(data['provenance']), 'invalid provenance')
    if isinstance(data['provenance'], str):
        scalar(data['provenance'], 'provenance')
    metrics = data['metrics']
    require(isinstance(metrics, dict) and set(metrics) <= METRICS, 'invalid metrics')
    for key, value in metrics.items():
        if key == 'currency':
            scalar(value, 'currency')
        else:
            require(value == 'n/a' or (type(value) in (int, float) and (type(value) is int or math.isfinite(value)) and value >= 0), 'invalid metric')
    if 'cost' in metrics and metrics['cost'] != 'n/a':
        require('non-comparable' in (data['source'] + ' ' + json.dumps(data['provenance'])).lower(), 'cost requires non-comparable provenance')
    return dict(schema='tackle-observability-telemetry/1', **data)


def sidecar(ws, data):
    path = 'resource-usage.telemetry.jsonl'
    old = ws.text(path, optional=True) or ''
    return path, append(old, json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n')


def lifecycle(ws, d):
    fields(d, ('run_id', 'event', 'task', 'role'), ('harness', 'tier', 'model', 'effort', 'at', 'attempts', 'rework', 'verification', 'source', 'outcome', 'absence', 'telemetry'))
    run = id_value(d['run_id'], 'run id')
    task = id_value(d['task'], 'task')
    role = scalar(d['role'], 'role')
    event = d['event']
    require(isinstance(event, str) and event in ('start', 'finish', 'observe-incomplete'), 'invalid event')
    require(event != 'finish' or 'outcome' in d, 'finish outcome required')
    outcome = d.get('outcome', {'start': 'running', 'finish': 'success', 'observe-incomplete': 'incomplete'}[event])
    require(isinstance(outcome, str) and outcome in {'start': ('running',), 'finish': ('success', 'failed', 'blocked', 'aborted'), 'observe-incomplete': ('incomplete',)}[event], 'invalid outcome')
    values = {key: scalar(d.get(key, 'n/a'), key) for key in ('harness', 'tier', 'model', 'effort', 'at')}
    require(values['at'] == 'n/a' or re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)', values['at']) is not None, 'invalid clock')
    nums = {}
    for key in ('attempts', 'rework'):
        v = d.get(key, 'n/a')
        require(v == 'n/a' or (type(v) is int and v >= 0), 'invalid counter')
        nums[key] = v
    source = reference(d.get('source', 'n/a'))
    verification = reference(d.get('verification', 'n/a'))
    usage = ws.text('resource-usage.md')
    lines, cols, start, end = table(usage, ('Run ID', 'Event', 'Task', 'Role', 'Outcome', 'Attempts', 'Rework', 'Verification', 'Source'))
    require('Schema: tackle-observability/2' in usage, 'missing ledger schema')
    existing = [dict(zip(cols, cells(line))) for line in lines[start:end] if len(cells(line)) == len(cols)]
    matching = [row for row in existing if row['Run ID'] == run]
    require(all(row['Task'] == task and row['Role'] == role for row in matching), 'run identity changed')
    require((event == 'start' and not matching) or (event != 'start' and sum(row['Event'] == 'start' for row in matching) == 1 and not any(row['Event'] in ('finish', 'observe-incomplete') for row in matching)), 'invalid transition')
    writes = {}
    if 'absence' in d:
        require(nums['attempts'] == 0 or nums['rework'] == 0, 'absence without zero')
        absence = d['absence']
        fields(absence, ('event_id', 'observed'))
        eid = id_value(absence['event_id'], 'event id')
        observed = scalar(absence['observed'], 'observation')
        history = ws.text('history.md')
        require(not any(r.get('eventid') == eid for r in records(history)), 'duplicate event')
        writes['history.md'] = append_record(history, '\n### Event ' + eid + '\nTask ID: ' + task + '\nRun ID: ' + run + '\nKind: observed-absence\nObserved: ' + observed + '\n', reader='counter')
        if nums['attempts'] != 'n/a' and nums['attempts'] > 0:
            require(verification == 'history.md', 'verification must include absence evidence')
        else:
            source = 'history.md#event-' + eid
    if isinstance(nums['attempts'], int):
        if 'history.md' in writes and nums['attempts'] == 0:
            found, absent = 0, True
        else:
            found, absent = evidence(ws, source, verification, task, run)
        require(absent if nums['attempts'] == 0 else found >= nums['attempts'], 'missing attempts evidence')
        if nums['attempts'] > 0:
            require(source != 'n/a' and bool(reference_parts(source)[1]) and evidence(ws, source, 'n/a', task, run)[0] >= 1, 'positive attempts need task-linked event source')
    if nums['rework'] == 0:
        require('absence' in d or evidence(ws, source, verification, task, run)[1], 'missing rework absence')
    row = {'Run ID': run, 'Event': event, 'Task': task, 'Role': role, 'Outcome': outcome,
           'Attempts': str(nums['attempts']), 'Rework': str(nums['rework']), 'Verification': verification, 'Source': source,
           'Harness': values['harness'], 'Tier': values['tier'], 'Model': values['model'], 'Effort': values['effort'], 'At': values['at']}
    require(set(cols) == set(row) and len(cols) == len(row), 'invalid ledger header')
    if end and not lines[end - 1].endswith('\n'):
        lines[end - 1] += '\n'
    lines.insert(end, '| ' + ' | '.join(row[col] for col in cols) + ' |\n')
    writes['resource-usage.md'] = ''.join(lines)
    if event == 'finish':
        t = d.get('telemetry')
        if t is None:
            t = {'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'), 'collector': 'n/a', 'source': 'n/a', 'scope': 'role', 'scope_id': run, 'run_id': run, 'metrics': {}, 'provenance': 'n/a'}
        path, content = sidecar(ws, telemetry(t, run))
        writes[path] = content
    else:
        require('telemetry' not in d, 'telemetry only on finish')
    return writes


def reconcile(ws, d):
    fields(d, ('run_id', 'event_id', 'observed'))
    run = id_value(d['run_id'], 'run id')
    eid = id_value(d['event_id'], 'event id')
    observed = d['observed']
    require(isinstance(observed, str) and bool(observed.strip()) and not any(c in observed for c in '\r\n'), 'invalid observation')
    usage = ws.text('resource-usage.md')
    columns = ('Run ID', 'Event', 'Task', 'Role', 'Harness', 'Tier', 'Model', 'Effort',
               'At', 'Outcome', 'Attempts', 'Rework', 'Verification', 'Source')
    require('Schema: tackle-observability/2' in usage, 'missing ledger schema')
    lines, cols, start, end = table(usage, columns)
    require(set(cols) == set(columns) and len(cols) == len(columns), 'invalid ledger header')
    try:
        table(''.join(lines[start:]), columns)
    except Refusal:
        pass
    else:
        raise Refusal('multiple ledger tables')
    matching = []
    for i in range(start, len(lines)):
        line = lines[i].strip()
        if not line.startswith('|'):
            continue
        parts = line.split('|')
        if len(parts) != len(cols) + 2:
            continue
        values = [part.strip() for part in parts[1:-1]]
        if all(re.fullmatch(r':?-+:?', value) for value in values):
            continue
        if values[cols.index('Run ID')] == run:
            matching.append((i, dict(zip(cols, values))))
    require(len(matching) == 1 and matching[0][1]['Event'] in ('finish', 'observe-incomplete'), 'not an orphan terminal')
    index, terminal = matching[0]
    history = ws.text('history.md')
    require(not any(r.get('eventid') == eid for r in records(history)), 'duplicate event')
    event = ('\n### Event ' + eid + '\nTask ID: ' + terminal['Task'] + '\nRun ID: ' + run
             + '\nKind: reconciled-start\nObserved: ' + observed + '\n')
    updated_history = append_record(history, event, reader='counter')
    row = dict(terminal, Event='start', At='n/a', Outcome='running', Attempts='n/a',
               Rework='n/a', Verification='n/a', Source='history.md#event-' + eid)
    lines.insert(index, '| ' + ' | '.join(row[col] for col in cols) + ' |\n')
    return {'resource-usage.md': ''.join(lines), 'history.md': updated_history}


def correction(ws, d):
    keys = ('event_id', 'task', 'run_id', 'failure_id', 'observed_failure', 'correction', 'validation_command', 'result')
    fields(d, keys)
    for k in keys:
        scalar(d[k], k)
    for k in ('event_id', 'task', 'run_id', 'failure_id'):
        id_value(d[k], k)
    require(re.search(r'(^failed(?:\s|;|$)|exit\s*[1-9][0-9]*|nonzero)', d['result']) is not None, 'result is not a failed validation')
    history = ws.text('history.md')
    require(not any(r.get('eventid') == d['event_id'] for r in records(history)), 'duplicate event')
    text = ('\n### Event {event_id}\nRun ID: {run_id}\nFailure ID: {failure_id}\nTask ID: {task}\nEvent ID: {event_id}\nKind: correction-validation\nObserved failure: {observed_failure}\nCorrection: {correction}\nValidation command: {validation_command}\nResult: {result}\nCycle count: 1\n\n').format(**d)
    return {'history.md': append_record(history, text, reader='counter')}


def closure(ws, d):
    fields(d, ('task', 'remains'), ('erratum',))
    task = id_value(d['task'], 'task')
    board, lines, cols, tasks, obligations = board_info(ws)
    require(task in tasks, 'task not in board')
    i, row = tasks[task]
    brief = row[cols.index('Brief')].strip('`')
    relative(brief)
    require(brief.startswith('tasks/'), 'invalid brief')
    digest = hashlib.sha256(ws.read(brief)).hexdigest()
    remains = d['remains']
    if remains != 'none':
        require(isinstance(remains, list) and bool(remains) and all(isinstance(x, str) for x in remains), 'invalid remains')
        require(len(set(remains)) == len(remains) and all(x in obligations for x in remains), 'unknown obligation')
        remains = ', '.join(remains)
    report_path = 'reports/' + task + '-report.md'
    report = ws.text(report_path)
    require(len(report.strip().splitlines()) >= 2, 'report is not substantive')
    visible_report = visible_text(report)
    hashes = re.findall(r'^\*\*Brief sha256\*\*:[ \t]*([0-9a-f]{64})[ \t]*\r?$', visible_report, re.M)
    require(len(hashes) <= 1 and (not re.search(r'^\*\*Brief sha256\*\*:', visible_report, re.M) or hashes), 'malformed receipt')
    archive = ws.text('history-archive.md', optional=True) or ''
    history = visible_text(archive) + '\n' + visible_text(ws.text('history.md', optional=True) or '')
    hm = re.search(r'^(?:[-*] )?Brief sha256 ' + re.escape(task) + r':[ \t]*([0-9a-f]{64})[ \t]*\r?$', history, re.M)
    original = hashes[0] if hashes else (hm.group(1) if hm else digest)
    require(not hm or original == hm.group(1), 'original hash differs from history')
    errata = re.findall(r'^\*\*Brief erratum\*\*:[ \t]*(D-[0-9]+) · sha256 ([0-9a-f]{64})[ \t]*\r?$', visible_report, re.M)
    require(len(errata) == len(re.findall(r'^\*\*Brief erratum\*\*:', visible_report, re.M)), 'malformed erratum')
    if errata:
        decisions = visible_text(ws.text('decisions.md'))
        for decision, unused in errata:
            require(re.search(r'^## ' + re.escape(decision) + r' [^\r\n]*✅ active', decisions, re.M) is not None, 'erratum decision not active')
    effective = errata[-1][1] if errata else original
    if effective != digest:
        decision = d.get('erratum')
        require(isinstance(decision, str) and re.fullmatch(r'D-[0-9]+', decision), 'active erratum required')
        decisions = visible_text(ws.text('decisions.md'))
        require(re.search(r'^## ' + re.escape(decision) + r' [^\r\n]*✅ active', decisions, re.M) is not None, 'erratum decision not active')
        report = append_record(report, '\n**Brief erratum**: ' + decision + ' · sha256 ' + digest + '\n')
    else:
        require('erratum' not in d, 'unnecessary erratum')
    if not hashes:
        report = append_record(report, '\n**Brief sha256**: ' + original + '\n')
    matches = list(re.finditer(r'^[ \t]*(?:[-*+][ \t]+)?\*\*Remains\*\*:[^\r\n]*', visible_text(report), re.M))
    require(len(matches) <= 1, 'multiple remains')
    if matches:
        match = matches[0]
        report = report[:match.start()] + '**Remains**: ' + remains + report[match.end():]
    else:
        report = append_record(report, '**Remains**: ' + remains + '\n')
    ref = 'reports/' + task + '-report.md'
    if row[cols.index('Verification')] != ref:
        parts = lines[i].split('|')
        pos = cols.index('Verification') + 1
        require(len(parts) == len(cols) + 2, 'malformed board row')
        old = parts[pos]
        parts[pos] = re.sub(r'\S(?:.*\S)?', ref, old) if old.strip() else ' ' + ref + ' '
        lines[i] = '|'.join(parts)
    return {'task-board.md': ''.join(lines), report_path: report}


def history_entry(ws, d):
    fields(d, ('heading', 'did', 'decisions', 'blockers', 'next', 'state'))
    heading = scalar(d['heading'], 'heading')
    require(re.fullmatch(r'20[0-9]{2}-[0-9]{2}-[0-9]{2}\s+.+', heading), 'undated heading')
    try:
        datetime.date.fromisoformat(heading[:10])
    except ValueError:
        raise Refusal('invalid date')
    state = d['state']
    skeys = ('task_state', 'in_flight', 'blocked_on', 'resume_from', 'checkpoint')
    fields(state, skeys)
    for key in skeys:
        scalar(state[key], key)
    old = ws.text('history.md')
    require('## ' + heading not in old.splitlines(), 'duplicate heading')
    blocks = []
    for key, title in (('did', 'Did'), ('decisions', 'Decisions'), ('blockers', 'Blockers'), ('next', 'Next')):
        values = d[key]
        require(isinstance(values, list) and bool(values), 'invalid history list')
        blocks.append('### ' + title + '\n' + ''.join('- ' + scalar(v, key) + '\n' for v in values))
    _, _, _, _, obligations = board_info(ws)
    active = ', '.join(k for k, v in obligations.items() if v == 'Open') or 'none'
    labels = ('Task state', 'In flight', 'Blocked on', 'Resume from', 'Checkpoint')
    snapshot = '### State snapshot\n' + ''.join('- ' + label + ': ' + state[key] + '\n' for key, label in zip(skeys, labels)) + '- Active obligations: ' + active + '\n'
    entry = '\n## ' + heading + '\n\n' + '\n'.join(blocks) + '\n' + snapshot
    agents = ws.text('AGENTS.md', optional=True) or ''
    match = re.search(r'^History entry budget: ([0-9]+)', agents, re.M)
    budget = int(match.group(1)) if match else 120
    require(len(entry.strip().splitlines()) <= budget, 'history entry exceeds budget')
    return {'history.md': append_record(old, entry)}


def compile_clause(ws, d):
    fields(d, ('clause_id', 'brief'))
    cid = id_value(d['clause_id'], 'clause id')
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*', cid), 'invalid clause id')
    path = relative(d['brief'])
    require(path.startswith('tasks/') and path.endswith('.md'), 'invalid brief path')
    contract = ws.read('design-contract.md')
    lines = contract.split(b'\n')
    found = []
    for i, line in enumerate(lines):
        words = line.split()
        if len(words) >= 2 and words[0] == b'##' and words[1] == cid.encode():
            found.append(i)
    require(len(found) == 1, 'unresolved or duplicate clause')
    start = found[0]
    end = start + 1
    while end < len(lines) and not lines[end].startswith((b'## ', b'<a id=')):
        end += 1
    # awk prints one LF for each record, including a final unterminated record.
    selected = lines[start:end]
    if end == len(lines) and selected and selected[-1] == b'':
        selected = selected[:-1]
    clause = b''.join(line + b'\n' for line in selected)
    try:
        text = clause.decode('utf-8')
    except UnicodeDecodeError:
        raise Refusal('invalid clause encoding')
    require(not any(line.startswith('```') for line in text.splitlines()), 'clause cannot be represented in seal block')
    heading = selected[0].decode('utf-8').rstrip('\r')
    title = re.sub(r'^##\s+' + re.escape(cid) + r'\s*[·-]\s*', '', heading)
    require(title != heading and bool(title), 'invalid clause heading')
    brief = ws.text(path)
    require(re.search(r'^\s*[-*+]\s+\*\*' + re.escape(cid) + r'\s+·', brief, re.M) is None, 'duplicate compiled clause')
    digest = hashlib.sha256(clause).hexdigest()
    title = re.sub(r'([\\`*])', r'\\\1', title)
    bullet = '\n- **' + cid + ' · ' + title + ' · sha256 `' + digest + '`**\n\n'
    compiled = append_record(brief, bullet, reader='seal')
    return {path: compiled + '```text\n' + text + '```\n'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--spec', required=True)
    args = parser.parse_args()
    ws = Workspace(args.workspace)
    try:
        raw = ws.read(relative(args.spec))
        def reject_constant(value):
            raise Refusal('nonfinite JSON number')
        def finite_float(value):
            number = float(value)
            require(math.isfinite(number), 'nonfinite JSON number')
            return number
        def unique(pairs):
            result = {}
            for key, value in pairs:
                require(key not in result, 'duplicate JSON field')
                result[key] = value
            return result
        try:
            spec = json.loads(raw.decode('utf-8'), parse_constant=reject_constant, parse_float=finite_float, object_pairs_hook=unique)
        except (ValueError, UnicodeDecodeError):
            raise Refusal('malformed JSON')
        fields(spec, ('schema', 'kind', 'data'))
        require(spec['schema'] == 'tackle-record/1', 'unknown schema')
        kind = spec['kind']
        functions = {'lifecycle': lifecycle, 'correction': correction, 'closure': closure, 'history': history_entry, 'compile-clause': compile_clause, 'reconcile': reconcile}
        if kind == 'telemetry':
            path, content = sidecar(ws, telemetry(spec['data']))
            changes = {path: content}
        else:
            require(isinstance(kind, str) and kind in functions, 'unknown kind')
            changes = functions[kind](ws, spec['data'])
        require(args.spec not in changes, 'spec overlaps target')
        encoded = {path: content.encode('utf-8') for path, content in changes.items()}
        for path in encoded:
            ws.check_target(path)
        for path, content in encoded.items():
            ws.write(path, content)
        print(json.dumps({'kind': kind, 'written': [{'path': p, 'sha256': hashlib.sha256(v).hexdigest()} for p, v in encoded.items()]}, separators=(',', ':')))
    finally:
        ws.close()


if __name__ == '__main__':
    try:
        main()
    except Refusal as exc:
        print('record: ' + str(exc), file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            print('record: symbolic link or non-directory path', file=sys.stderr)
            sys.exit(2)
        print('record: filesystem operation failed: ' + str(exc), file=sys.stderr)
        sys.exit(1)
