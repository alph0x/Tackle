import hashlib
import json
import re


def task_fields(text):
    retired = {'Touches', 'Done-signal', 'Run', 'Target check', 'Surround check'}
    fields = {}
    for line in text.splitlines():
        match = re.fullmatch(r'\s*(?:-\s*)?\*\*([^*:]+)(?:\*\*\s*:|:\*\*)\s*(.*?)\s*', line)
        if not match:
            continue
        key = match[1]
        if key in retired:
            raise ValueError('migrate first: retired field name ' + key + ' (references/guides/migrate.md#forward-only)')
        if key in fields and fields[key] != match[2]:
            raise ValueError('conflicting field values: ' + key)
        fields[key] = match[2]
    return fields


def prepare_tasks(requirements, tasks, selected, available, fingerprints, delivery):
    identities = [task['id'] for task in tasks]
    if len(set(identities)) != len(identities) or not identities:
        raise ValueError('duplicate or empty task identities')
    if any(not re.fullmatch(r'T-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*', identity) for identity in identities):
        raise ValueError('invalid stable task identity')
    by_id = dict(zip(identities, tasks))
    if len(requirements) != len(set(requirements)) or not requirements:
        raise ValueError('duplicate or missing requirements')
    if not selected or len(selected) != len(set(selected)) or set(selected) - by_id.keys():
        raise ValueError('invalid readiness scope')
    owners = {requirement: [] for requirement in requirements}
    for task in tasks:
        if not task.get('requirements') or not task.get('outcome'):
            raise ValueError('task lacks required outcome or scope')
        for requirement in task['requirements']:
            if requirement not in owners:
                raise ValueError('unjustified task scope')
            owners[requirement].append(task['id'])
        for dependency in task.get('consumes', []):
            producer = by_id.get(dependency['task'])
            if producer is None:
                raise ValueError('missing dependency identity')
            output = producer.get('produces', {}).get(dependency['artifact'])
            expected = {'interface': dependency['interface'], 'revision': dependency['revision']}
            if output != expected:
                raise ValueError('incompatible declared producer/consumer')
    if any(not names for names in owners.values()):
        raise ValueError('unowned requirement')
    if not delivery or any(not row.get(k) for row in delivery for k in ('owner', 'check', 'record')):
        raise ValueError('unowned deliverable obligation')
    visiting, visited = set(), set()
    def visit(identity):
        if identity in visiting:
            raise ValueError('cyclic dependency')
        if identity in visited:
            return
        visiting.add(identity)
        for dependency in by_id[identity].get('consumes', []):
            visit(dependency['task'])
        visiting.remove(identity)
        visited.add(identity)
    for identity in identities:
        visit(identity)
    required_inputs = {'contract', 'source', 'configuration', 'dependencies', 'selectors', 'runtime'}
    if not required_inputs.issubset(fingerprints):
        raise ValueError('missing relevant fingerprint')
    for key in required_inputs - {'selectors'}:
        if not isinstance(fingerprints[key], str) or not fingerprints[key].strip():
            raise ValueError('missing relevant fingerprint: ' + key)
    if not isinstance(fingerprints['selectors'], (dict, list)) or not fingerprints['selectors']:
        raise ValueError('missing selector membership fingerprint')
    states, findings = {}, {}
    for identity, task in by_id.items():
        states[identity] = 'Draft'
        if identity not in selected:
            if not task.get('milestone') or not task.get('future_check'):
                raise ValueError('deferred scope lacks milestone/check owner')
            continue
        gaps = []
        for key in ('write_scope', 'inputs', 'acceptance_check', 'regression_check', 'record'):
            if not task.get(key):
                gaps.append('missing ' + key)
        for requirement in task['requirements']:
            cases = [case for case in task.get('cases', []) if case.get('requirement') == requirement]
            if not cases or any(k not in case for case in cases for k in ('input', 'expected', 'check')) or any(not case['check'] for case in cases):
                gaps.append('missing observable case: ' + requirement)
        if task.get('pending_product_decisions'):
            gaps.append('material decision unresolved')
        if task.get('semantic_review') != 'passed' or task.get('boundary_fixtures') != 'passed':
            gaps.append('readiness observations unavailable')
        for dependency in task.get('consumes', []):
            key = dependency['task'] + '/' + dependency['artifact']
            expected = {'interface': dependency['interface'], 'revision': dependency['revision']}
            if available.get(key) != expected:
                gaps.append('missing or stale dependency output: ' + key)
        findings[identity] = gaps
        if not gaps:
            states[identity] = 'Ready to run'
    revision = hashlib.sha256(json.dumps(
        [requirements, tasks, selected, available, fingerprints, delivery],
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'states': states, 'findings': findings, 'owners': owners,
            'revision': revision, 'execution_authorized': False, 'product_pass': False}
