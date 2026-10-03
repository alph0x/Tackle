```python
MOMENTS = ('lock', 'repeat-failure', 'complete')
PREFIX = '**Adversary**:'


def review_lines(report):
    return [[cell.strip() for cell in line[len(PREFIX):].split(' · ')]
            for line in report.splitlines() if line.startswith(PREFIX)]


def line_problem(cells, paths):
    if len(cells) != 4 or not all(cells):
        return 'an adversary line needs four non-empty cells'
    moment, verdict, _, independence = cells
    if moment not in MOMENTS:
        return 'unknown adversary moment %r' % moment
    decision = verdict.startswith('decisions.md#')
    if decision != (independence == 'waived'):
        return 'a waiver cites a decision and a decision is cited only by a waiver'
    if (verdict if decision else verdict.split('#')[0]) not in paths:
        return 'adversary verdict %s does not resolve' % verdict
    return None


def adversary_findings(tasks, paths):
    findings = []
    for task_id, task in sorted(tasks.items()):
        if task.get('before_adoption'):
            continue
        lines = review_lines(task.get('report') or '')
        for cells in lines:
            problem = line_problem(cells, paths)
            if problem:
                findings.append('%s: %s' % (task_id, problem))
        if task.get('status') == 'Complete' and not any(cells[0] == 'complete' for cells in lines):
            findings.append('%s: Complete without a complete review line' % task_id)
        seen, pending = set(), False
        for kind, value in task.get('events') or []:
            if kind == 'failure':
                pending = pending or value in seen
                seen.add(value)
            elif kind == 'review' and value == 'repeat-failure':
                pending = False
            elif kind == 'attempt' and pending:
                findings.append('%s: a repeated failure was corrected without a repeat-failure review' % task_id)
                pending = False
        if pending and task.get('status') == 'Complete':
            findings.append('%s: Complete after an unreviewed repeated failure' % task_id)
    return findings
```
