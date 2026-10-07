#!/usr/bin/env python3
"""Finite, non-billable Responses-shaped process fixture. No provider adapter."""
import argparse
import hashlib
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--script', required=True)
    parser.add_argument('--attempt-id', required=True)
    parser.add_argument('--body-sha256', required=True)
    args = parser.parse_args()
    body = sys.stdin.buffer.read(1048577)
    if len(body) > 1048576 or hashlib.sha256(body).hexdigest() != args.body_sha256:
        return 8
    script = json.loads(open(args.script, encoding='utf-8').read())
    request = json.loads(body)
    session = script['session_id']
    response = 'r_' + args.attempt_id
    if script['fault'] != 'drop_ack':
        ack = {'schema': 'tackle-controlled-stub-ack/1', 'attempt_id': args.attempt_id,
               'body_sha256': args.body_sha256, 'pid': os.getpid()}
        sys.stderr.write(json.dumps(ack, sort_keys=True, separators=(',', ':')) + '\n')
        sys.stderr.flush()
    if script['fault'] == 'nonzero':
        return 9
    records = []

    def add(kind, **extra):
        records.append(dict(schema='tackle-controlled-stub-event/1',
                            event_id='e_%s_%s' % (args.attempt_id, len(records)),
                            session_id=session, attempt_id=args.attempt_id,
                            response_id=response, kind=kind, **extra))

    add('response_started', model_echo=request['model'])
    for index, item in enumerate(script['items']):
        add('item_completed', item_index=index, item=item)
        if script['fault'] == 'conflict_item' and index == 0:
            changed = dict(item)
            changed['id'] = 'conflicting_item'
            add('item_completed', item_index=index, item=changed)
    if script['fault'] != 'missing_completion':
        if script['status'] == 'completed':
            add('response_completed', status='completed', item_count=len(script['items']))
        else:
            add('response_failed', status=script['status'], error_code='fixture_failure')
    if script['fault'] == 'duplicate_event':
        records.append(records[0])
    raw = ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n' for r in records).encode()
    width = script['chunk_bytes'] or len(raw) or 1
    for start in range(0, len(raw), width):
        sys.stdout.buffer.write(raw[start:start + width])
        sys.stdout.buffer.flush()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
