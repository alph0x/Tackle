"""Pure functions over a project's requirements base (one Markdown file per domain) and a plan's requirements delta.

Nothing here reads or writes a file. Every function leaves its inputs unchanged; fold returns new file text.
"""
import re

TITLE_PREFIX = '# Requirements — '
HEADING = re.compile(r'^### REQ-([A-Z0-9][A-Z0-9-]*)-(\d{2,}) · (.+)$')
SECTIONS = ('ADDED', 'MODIFIED', 'REMOVED')
STATES = ('planned', 'done')
SHALL = re.compile(r'\b(SHALL|MUST)\b')
TASK = re.compile(r'Task:\s*(.*?)\s*(?:·\s*State:\s*(\S+))?\s*$')


def _problem(kind, id_, detail):
    return {'kind': kind, 'id': id_, 'detail': detail}


def _domain_of(id_):
    return re.match(r'REQ-([A-Z0-9][A-Z0-9-]*)-\d{2,}$', id_).group(1).lower()


def _domain_title(domain):
    return domain.replace('-', ' ').title()


def _blocks(text):
    """Return (title, [(section, heading, body lines)]) for one Markdown file, in file order."""
    title = None
    blocks = []
    section = None
    current = None
    for line in text.split('\n'):
        if line.startswith('## '):
            section = line[3:].strip()
            current = None
        elif line.startswith('### '):
            current = []
            blocks.append((section, line, current))
        elif current is not None:
            current.append(line)
        elif title is None and line.startswith(TITLE_PREFIX):
            title = line[len(TITLE_PREFIX):].strip()
    return title, blocks


def _scenarios(lines):
    found = []
    current = None
    section = None
    for line in lines:
        if line.startswith('#### Scenario:'):
            current = {'name': line[len('#### Scenario:'):].strip(), 'given': [], 'when': [], 'then': [], 'check': None}
            found.append(current)
            section = None
            continue
        bullet = line.strip()
        if current is None or not bullet.startswith('- '):
            continue
        text = bullet[2:].strip()
        if text.startswith('Check:'):
            current['check'] = text[len('Check:'):].strip() or None
            section = None
            continue
        keyword, _, rest = text.partition(' ')
        if keyword in ('GIVEN', 'WHEN', 'THEN'):
            section = keyword.lower()
        elif keyword == 'AND':
            section = section or 'when'
        else:
            continue
        current[section].append(rest.strip())
    return found


def _meta_and_body(lines):
    """Split one block into its meta fields, its statement text and its scenarios."""
    meta = {}
    statement = []
    body = []
    for line in lines:
        if line.startswith('#### ') or body:
            body.append(line)
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('Task:'):
            match = TASK.match(stripped)
            meta['task'] = match.group(1) or None
            meta['state'] = match.group(2)
        elif stripped.startswith('Repository:'):
            meta['repository'] = stripped[len('Repository:'):].strip() or None
        elif stripped.startswith('Reason:'):
            meta['reason'] = stripped[len('Reason:'):].strip() or None
        elif stripped.startswith('Retired:'):
            meta['retired'] = stripped[len('Retired:'):].strip() or None
        else:
            statement.append(stripped)
    return meta, ' '.join(statement), _scenarios(body)


def parse_base(files):
    requirements = {}
    problems = []
    for domain in sorted(files):
        _, blocks = _blocks(files[domain])
        for section, heading, body in blocks:
            match = HEADING.match(heading)
            if not match or section not in ('Active', 'Retired'):
                problems.append(_problem('malformed', '', 'base entry without a requirement id or outside Active and Retired: %s' % heading))
                continue
            id_ = 'REQ-%s-%s' % (match.group(1), match.group(2))
            if _domain_of(id_) != domain:
                problems.append(_problem('malformed', id_, 'requirement is filed under the wrong domain'))
                continue
            if id_ in requirements:
                problems.append(_problem('duplicate', id_, 'id appears twice in the base'))
                continue
            meta, statement, scenarios = _meta_and_body(body)
            requirements[id_] = {'id': id_, 'domain': domain, 'title': match.group(3).strip(), 'statement': statement,
                                 'scenarios': scenarios, 'state': 'active' if section == 'Active' else 'retired',
                                 'retired': meta.get('retired')}
    return {'requirements': requirements, 'problems': problems}


def parse_delta(text):
    revision = re.search(r'^Base revision:\s*(.*?)\s*$', text, re.M)
    entries = []
    problems = []
    _, blocks = _blocks(text)
    for section, heading, body in blocks:
        if section not in SECTIONS:
            continue
        match = HEADING.match(heading)
        if not match:
            problems.append(_problem('malformed', '', 'entry heading without a requirement id: %s' % heading))
            continue
        id_ = 'REQ-%s-%s' % (match.group(1), match.group(2))
        meta, statement, scenarios = _meta_and_body(body)
        entry = {'section': section, 'id': id_, 'title': match.group(3).strip(), 'task': meta.get('task'),
                 'state': meta.get('state'), 'repository': meta.get('repository'), 'statement': statement,
                 'scenarios': scenarios, 'reason': meta.get('reason')}
        entries.append(entry)
        if not entry['task'] or entry['state'] not in STATES:
            problems.append(_problem('malformed', id_, 'entry lacks a Task: line or a State: of planned or done'))
        if section == 'REMOVED':
            if not entry['reason']:
                problems.append(_problem('malformed', id_, 'REMOVED entry has no Reason: line'))
        else:
            if not SHALL.search(statement):
                problems.append(_problem('malformed', id_, 'statement has no SHALL or MUST'))
            if not scenarios:
                problems.append(_problem('malformed', id_, 'entry has no scenario'))
    return {'base_revision': revision.group(1) if revision else None, 'entries': entries, 'problems': problems}


def validate(base, delta, repositories=None):
    problems = [dict(p) for p in base['problems'] + delta['problems']]
    known = base['requirements']
    active = {id_ for id_, req in known.items() if req['state'] == 'active'}
    added = set()
    sections = {}
    for entry in delta['entries']:
        id_ = entry['id']
        sections.setdefault(id_, set()).add(entry['section'])
        if entry['section'] == 'ADDED':
            if id_ in known or id_ in added:
                problems.append(_problem('duplicate', id_, 'ADDED id already exists in the base or repeats in the delta'))
            added.add(id_)
        elif id_ not in active:
            problems.append(_problem('unknown', id_, '%s id is not active in the base' % entry['section']))
        if repositories is not None:
            if entry['repository'] is None:
                problems.append(_problem('repository', id_, 'entry has no Repository: line'))
            elif entry['repository'] not in repositories:
                problems.append(_problem('repository', id_, 'Repository %s is not declared' % entry['repository']))
        if entry['section'] != 'REMOVED':
            for scenario in entry['scenarios']:
                if scenario['check'] is None:
                    problems.append(_problem('unchecked', id_, 'scenario %s has no Check: line' % scenario['name']))
    for id_, names in sections.items():
        if len(names) > 1:
            problems.append(_problem('conflict', id_, 'id appears in %s' % ' and '.join(sorted(names))))
    return problems


def _passed(records, check, revision):
    return check is not None and any(r['check'] == check and r['passed'] is True and r['revision'] == revision for r in records)


def reconcile(delta, records, final_revision):
    reconciled = []
    unreconciled = []
    for entry in delta['entries']:
        if entry['state'] != 'done':
            unreconciled.append({'id': entry['id'], 'scenario': None, 'check': None, 'reason': 'planned'})
            continue
        if entry['section'] == 'REMOVED':
            reconciled.append(entry['id'])
            continue
        complete = True
        for scenario in entry['scenarios']:
            if _passed(records, scenario['check'], final_revision):
                continue
            complete = False
            stale = scenario['check'] is not None and any(
                r['check'] == scenario['check'] and r['passed'] is True and r['revision'] != final_revision for r in records)
            unreconciled.append({'id': entry['id'], 'scenario': scenario['name'], 'check': scenario['check'],
                                 'reason': 'stale record' if stale else 'no passing record'})
        if complete:
            reconciled.append(entry['id'])
    return reconciled, unreconciled


def _bullets(scenario):
    lines = []
    for key in ('given', 'when', 'then'):
        for index, text in enumerate(scenario[key]):
            lines.append('- %s %s' % ('AND' if index else key.upper(), text))
    if scenario['check'] is not None:
        lines.append('- Check: %s' % scenario['check'])
    return lines


def _block(req):
    lines = ['### %s · %s' % (req['id'], req['title'])]
    if req['state'] == 'retired':
        lines.append('Retired: %s' % req['retired'])
    lines.extend(['', req['statement']])
    for scenario in req['scenarios']:
        lines.extend(['', '#### Scenario: %s' % scenario['name']])
        lines.extend(_bullets(scenario))
    return lines


def _render(title, items):
    lines = [TITLE_PREFIX + title, '', '## Active', '']
    for item in items:
        if item['section'] == 'active':
            lines.extend(_block(item['req']) + [''])
    lines.extend(['## Retired', ''])
    for item in items:
        if item['section'] == 'retired':
            lines.extend(_block(item['req']) + [''])
    return '\n'.join(lines).rstrip('\n') + '\n'


def fold(files, delta_text, records, final_revision, plan_slug, date):
    base = parse_base(files)
    delta = parse_delta(delta_text)
    problems = validate(base, delta)
    if problems:
        raise ValueError('; '.join('%s %s: %s' % (p['kind'], p['id'] or '(no id)', p['detail']) for p in problems))
    reconciled, _ = reconcile(delta, records, final_revision)
    ready = set(reconciled)
    titles = {domain: _blocks(text)[0] for domain, text in files.items()}
    model = {}
    for req in base['requirements'].values():
        section = 'active' if req['state'] == 'active' else 'retired'
        model.setdefault(req['domain'], []).append({'section': section, 'req': dict(req)})
    touched = set()
    for entry in delta['entries']:
        if entry['id'] not in ready:
            continue
        domain = _domain_of(entry['id'])
        items = model.setdefault(domain, [])
        touched.add(domain)
        if entry['section'] == 'ADDED':
            items.append({'section': 'active', 'req': _requirement(entry, domain, 'active', None)})
            continue
        for item in items:
            if item['req']['id'] != entry['id'] or item['section'] != 'active':
                continue
            if entry['section'] == 'MODIFIED':
                item['req'] = _requirement(entry, domain, 'active', None)
            else:
                item['section'] = 'retired'
                item['req'] = _requirement(item['req'], domain, 'retired', '%s · %s · %s' % (plan_slug, date, entry['reason']))
    out = {}
    for domain in sorted(touched):
        title = titles.get(domain) or _domain_title(domain)
        out[domain] = _render(title, model[domain])
    return out


def _requirement(source, domain, state, retired):
    return {'id': source['id'], 'domain': domain, 'title': source['title'], 'statement': source['statement'],
            'scenarios': list(source['scenarios']), 'state': state, 'retired': retired}
