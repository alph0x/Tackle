```python
"""Pure functions over a project map (schema tackle-map/1) and a plan's map delta (schema tackle-map-delta/1).

Nothing here reads or writes a file except `stale`, which only tests that source paths exist.
Every function leaves its inputs unchanged.
"""
import copy
from pathlib import Path

DELTA_SCHEMA = 'tackle-map-delta/1'
OPS = ('add', 'change')
STATES = ('planned', 'done')
PLAIN = ('op', 'id', 'task', 'state', 'relations')


def _relation_problems(relations, known, where):
    problems = []
    for rel in relations or []:
        if not isinstance(rel, (list, tuple)) or len(rel) < 2 or not all(isinstance(x, str) for x in rel):
            problems.append('%s has a relation that is not [from, to, label]: %r' % (where, rel))
            continue
        for end in rel[:2]:
            if end not in known:
                problems.append('%s has a relation to unknown component %s' % (where, end))
    return problems


def validate(base, delta):
    """Return every problem found in the base and the delta, as sentences that name the id."""
    problems = []
    groups = {g.get('id') for g in base.get('groups', [])}
    known = set()
    for comp in base.get('components', []):
        if comp.get('id') in known:
            problems.append('the base lists component %s twice' % comp.get('id'))
        known.add(comp.get('id'))
        if comp.get('group') not in groups:
            problems.append('base component %s is in unknown group %s' % (comp.get('id'), comp.get('group')))
    for rel in base.get('relations', []):
        problems += _relation_problems([rel], known, 'the base')
    if not isinstance(delta, dict) or not isinstance(delta.get('changes'), list):
        return problems + ['the delta holds no list of changes']
    if delta.get('schema', DELTA_SCHEMA) != DELTA_SCHEMA:
        problems.append('the delta schema is %s, not %s' % (delta.get('schema'), DELTA_SCHEMA))
    pending = []
    for change in delta['changes']:
        if not isinstance(change, dict) or not isinstance(change.get('id'), str) or not change.get('id'):
            problems.append('a change names no component id: %r' % (change,))
            continue
        cid = change['id']
        where = 'change %s' % cid
        if change.get('op') not in OPS:
            problems.append('%s has op %s, outside %s' % (where, change.get('op'), ', '.join(OPS)))
        if change.get('state') not in STATES:
            problems.append('%s has state %s, outside %s' % (where, change.get('state'), ', '.join(STATES)))
        if not change.get('task'):
            problems.append('%s names no owning task' % where)
        if change.get('op') == 'add':
            if cid in known:
                problems.append('%s adds a component that already exists' % where)
            if change.get('group') not in groups:
                problems.append('%s is in unknown group %s' % (where, change.get('group')))
            if not change.get('title'):
                problems.append('%s adds a component with no title' % where)
            known.add(cid)
        elif change.get('op') == 'change':
            if cid not in known:
                problems.append('%s changes unknown component %s' % (where, cid))
            if 'group' in change and change['group'] not in groups:
                problems.append('%s moves it into unknown group %s' % (where, change['group']))
        pending.append((where, change.get('relations')))
    for where, relations in pending:
        problems += _relation_problems(relations, known, where)
    return problems


def _apply(base, changes):
    out = copy.deepcopy(base)
    index = {c['id']: c for c in out['components']}
    seen = {tuple(r) for r in out.get('relations', [])}
    for change in changes:
        fields = {k: copy.deepcopy(v) for k, v in change.items() if k not in PLAIN}
        if change['op'] == 'add':
            fields.setdefault('sources', [])
            fields.setdefault('text', '')
            comp = {'id': change['id']}
            comp.update(fields)
            out['components'].append(comp)
            index[change['id']] = comp
        else:
            index[change['id']].update(fields)
        for rel in change.get('relations', []):
            if tuple(rel) not in seen:
                seen.add(tuple(rel))
                out.setdefault('relations', []).append(list(rel))
    return out


def after(base, delta):
    """The map with every change applied. ValueError when validate finds a problem."""
    problems = validate(base, delta)
    if problems:
        raise ValueError('; '.join(problems))
    return _apply(base, delta['changes'])


def neighbors(map_, ids):
    """The ids plus every component related to one of them, in either direction, sorted."""
    wanted = set(ids)
    found = set(wanted)
    for rel in map_.get('relations', []):
        if rel[0] in wanted:
            found.add(rel[1])
        if rel[1] in wanted:
            found.add(rel[0])
    return sorted(found)


def stale(map_, root):
    """Sorted ids of components with a source path missing under root. Nothing is deleted."""
    base = Path(root)
    missing = []
    for comp in map_.get('components', []):
        for source in comp.get('sources', []):
            path = Path(source)
            if path.is_absolute() or '..' in path.parts or not (base / path).exists():
                missing.append(comp['id'])
                break
    return sorted(missing)


def planned(delta):
    """The planned changes, as [component id, owning task] pairs, in delta order."""
    return [[c['id'], c.get('task', '')] for c in delta.get('changes', []) if c.get('state') == 'planned']


def fold(base, delta, revision, commit=None, date=None):
    """A new base holding only the done changes. ValueError on a problem, on a done change that
    needs a planned one, or on a done relation that would end at a planned component."""
    problems = validate(base, delta)
    if problems:
        raise ValueError('; '.join(problems))
    done = dict(delta, changes=[c for c in delta['changes'] if c['state'] == 'done'])
    problems = validate(base, done)
    if problems:
        raise ValueError('the done changes cannot fold alone: ' + '; '.join(problems))
    out = _apply(base, done['changes'])
    stamp = dict(out.get('verified_at', {}), revision=revision)
    if commit is not None:
        stamp['commit'] = commit
    if date is not None:
        stamp['date'] = date
    out['verified_at'] = stamp
    return out
```
