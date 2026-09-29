```python
TASK_POOL_LIMIT = 3
UNOWNED_INTEGRATION_POOL_LIMIT = 2


def correction_usage(events, pool_ids, limits=None):
    unique = {}
    for event in events:
        identity = event['cycle_id']
        if not identity or event.get('kind') != 'failed-correction':
            raise ValueError('invalid correction event')
        if identity in unique and unique[identity] != event:
            raise ValueError('conflicting correction history')
        unique[identity] = event
    selected = set(pool_ids)
    limits = dict(limits or {})
    if not set(limits) <= selected or any(
            limit not in (TASK_POOL_LIMIT, UNOWNED_INTEGRATION_POOL_LIMIT) for limit in limits.values()):
        raise ValueError('invalid pool limit')
    caps = {pool: limits.get(pool, TASK_POOL_LIMIT) for pool in selected}
    pools = {pool: 0 for pool in selected}
    counted = set()
    for identity, event in unique.items():
        affected = event.get('pool_ids', [event.get('pool_id')])
        if not isinstance(affected, list) or not affected or any(not isinstance(p, str) or not p for p in affected):
            raise ValueError('invalid correction pool')
        for pool in selected & set(affected):
            pools[pool] += 1
            counted.add(identity)
    return {'spent': len(counted), 'pools': pools,
            'remaining': min((max(0, caps[pool] - n) for pool, n in pools.items()), default=TASK_POOL_LIMIT),
            'exhausted': any(n >= caps[pool] for pool, n in pools.items())}


def transfer_lineage(previous, descendants, unresolved, failure_pools):
    required = set(previous) & set(unresolved)
    inherited = set().union(*(set(failures) for failures in descendants.values())) if descendants else set()
    if required != inherited or not required.issubset(failure_pools):
        raise ValueError('lost, invented or unrelated failure lineage')
    return {identity: sorted({failure_pools[failure] for failure in failures})
            for identity, failures in descendants.items()}
```
