#!/usr/bin/env python3
"""Render task record fragments as JSON for placement in a workspace."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--brief', required=True, type=Path)
    p.add_argument('--task', required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--attempts', required=True, type=int)
    p.add_argument('--observed-absence')
    p.add_argument('--failure')
    p.add_argument('--correction')
    p.add_argument('--validation-command')
    p.add_argument('--result')
    p.add_argument('--correction-event', action='append', default=[], help='JSON object with failure, correction, validation_command and result; repeat for each cycle')
    p.add_argument('--role', default='Driver')
    p.add_argument('--harness', default='generic')
    p.add_argument('--tier', default='standard')
    p.add_argument('--model', default='n/a')
    p.add_argument('--effort', default='n/a')
    p.add_argument('--remains', default='none')
    a = p.parse_args()
    if a.attempts < 0:
        p.error('attempts must be nonnegative')
    if a.attempts == 0 and not a.observed_absence:
        p.error('zero attempts requires observed absence')
    events = []
    for raw in a.correction_event:
        try:
            item = json.loads(raw)
            if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in ('failure', 'correction', 'validation_command', 'result')):
                raise ValueError('missing event fields')
            events.append(item)
        except (ValueError, TypeError) as exc:
            p.error('invalid correction event: ' + str(exc))
    if any((a.failure, a.correction, a.validation_command, a.result)):
        if not all((a.failure, a.correction, a.validation_command, a.result)):
            p.error('correction event requires all fields')
        events.append(dict(failure=a.failure, correction=a.correction, validation_command=a.validation_command, result=a.result))
    if len(events) != a.attempts:
        p.error('attempts must equal the number of correction events')
    for item in events:
        for value in item.values():
            if not isinstance(value, str) or any(c in value for c in '\n\r|'):
                p.error('event fields must be single lines without a pipe')
        if not __import__('re').search(r'(^failed(?:[ ;]|$)|exit\s*[1-9][0-9]*|nonzero)', item['result']):
            p.error('correction result must record a failed validation')
    fields = vars(a).copy()
    for name, value in fields.items():
        if isinstance(value, str) and ('\n' in value or '|' in value or '\r' in value):
            p.error(name + ' must be a single line without a pipe')
    event_id = a.run_id.replace('/', '-')
    source = 'history.md#event-' + event_id
    common = [a.run_id, None, a.task, a.role, a.harness, a.tier, a.model, a.effort, 'n/a']
    def row(event, outcome, attempts, verification, source_value):
        return '| ' + ' | '.join(common[:1] + [event] + common[2:] + [outcome, attempts, 'n/a', verification, source_value]) + ' |\n'
    header = ('Schema: tackle-observability/2\n| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |\n'
              '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n')
    usage = header + row('start', 'running', 'n/a', 'n/a', 'synthetic') + row('finish', 'success', str(a.attempts), 'n/a', source)
    if a.attempts:
        source = 'history.md'
        usage = header + row('start', 'running', 'n/a', 'n/a', 'synthetic') + row('finish', 'success', str(a.attempts), 'n/a', source)
        event = ''
        for index, item in enumerate(events, 1):
            eid = f'{event_id}-{index}'
            event += (f"### Event {eid}\nTask: {a.task}\nEvent ID: {eid}\nRun ID: {a.run_id}\nRole: {a.role}\nKind: correction-validation\nFailure ID: fault-{eid}\nObserved failure: {item['failure']}\nCorrection: {item['correction']}\nValidation command: {item['validation_command']}\nResult: {item['result']}\nCycle count: 1\nAuthorization: n/a\n\n")
    else:
        event = f'### Event {event_id}\nTask ID: {a.task}\nRun ID: {a.run_id}\nKind: observed-absence\nObserved: {a.observed_absence}\n'
    receipt = '**Brief sha256**: ' + hashlib.sha256(a.brief.read_bytes()).hexdigest() + '\n**Remains**: ' + a.remains
    print(json.dumps({'resource_usage': usage, 'closure_receipt': receipt, 'event': event}, indent=2))


if __name__ == '__main__':
    main()
