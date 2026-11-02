"""Functional native cumulative-accounting and live-cap controls."""
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import unittest

import test_codex_login_route as fixtures

spec = importlib.util.spec_from_file_location('native_usage_route', fixtures.ROUTE)
route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)


def meta(identity):
    return {'type': 'session_meta', 'payload': {'id': identity}}


def count(total, inp=100, cached=80, out=20):
    return {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {'total_token_usage': {
        'total_tokens': total, 'input_tokens': inp, 'cached_input_tokens': cached, 'output_tokens': out}}}}


def data(*rows):
    return b''.join((json.dumps(row) + '\n').encode() for row in rows)


class NativeSessionUsageTests(unittest.TestCase):
    # Guarantee: parent and worker count once; fault: global last; consumer: final route;
    # alternative: reversing streams produces the same aggregate.
    def test_native_stream_order_and_snapshots(self):
        a = data(meta('a'), count(10), count(20), count(20))
        b = data(meta('b'), count(20))
        for raw in (a + b, b + a):
            self.assertEqual(route.token_usage(raw)['total_tokens'], 40)
        self.assertEqual(route.token_usage(a + data(meta('a'), count(20)))['total_tokens'], 20)

    # Guarantee: independent incremental files; fault: one latest replaces another;
    # alternative: complete a partial line on the next read.
    def test_tail_partial_and_distinct_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            sessions = home / 'sessions'
            sessions.mkdir()
            a, b = sessions / 'a.jsonl', sessions / 'b.jsonl'
            a.write_bytes(data(meta('a'), count(20)))
            raw = data(meta('b'), count(30))
            b.write_bytes(raw[:-2])
            tail = route.RolloutTail(home, set())
            self.assertIsNone(tail.read())
            with b.open('ab') as handle:
                handle.write(raw[-2:])
            self.assertEqual(tail.read()['total_tokens'], 50)
            self.assertEqual(tail.read(), route.token_usage(a.read_bytes() + b.read_bytes()))

    # Guarantee: unknown native streams cannot become measured zero or a partial total;
    # alternative: an anonymous legacy stream remains supported.
    def test_unknown_and_legacy(self):
        self.assertIsNone(route.token_usage(data(meta('a'), count(10), meta('b'))))
        self.assertIsNone(route.token_usage(data(count(10), meta('b'), count(20))))
        self.assertEqual(route.token_usage(data(count(10)))['total_tokens'], 10)

    def exercise_launch(self, cap):
        fixture = fixtures.CodexRouteTests(methodName='test_usage')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.data['caps']['probe'] = cap
        fixture.save()
        fixture.fake.write_text(fixture.fake.read_text() + '''\nimport time\ndef native(name, value):\n    return [{'type':'session_meta','payload':{'id':name}}, {'type':'event_msg','payload':{'type':'token_count','info':{'total_token_usage':{'input_tokens':100,'cached_input_tokens':80,'output_tokens':20,'total_tokens':value}}}}]\nrollout.write_text(''.join(json.dumps(r)+'\\n' for r in [rows[0]] + native('parent',120)))\n(sessions / 'worker.jsonl').write_text(''.join(json.dumps(r)+'\\n' for r in native('worker',120)))\ntime.sleep(0.5)\nprint('completed-marker')\n''')
        result = fixture.probe()
        observed = json.loads((fixture.root / 'out' / 'result.json').read_text())
        stdout = (fixture.root / 'out' / 'method' / 'stdout.jsonl').read_text()
        return result, observed, stdout

    # Guarantee: real launch stops on the first summed observation; fault: each stream alone below cap;
    # alternative: same synthetic CLI completes when the summed total is below cap.
    def test_launch_interrupts_at_summed_cap(self):
        result, observed, stdout = self.exercise_launch(205)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(observed['sessions']['method']['reason'], 'cap')
        self.assertEqual(observed['sessions']['method']['overshoot_tokens'], 35)
        self.assertEqual(observed['tokens']['method'], 240)
        self.assertNotIn('completed-marker', stdout)

    def test_launch_below_summed_cap_completes(self):
        result, observed, stdout = self.exercise_launch(1000)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(observed['tokens']['method'], 240)
        self.assertIn('completed-marker', stdout)

    def exercise_unknown_worker(self, parent, cap):
        fixture = fixtures.CodexRouteTests(methodName='test_usage')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.data['caps']['probe'] = cap
        fixture.save()
        fixture.fake.write_text(fixture.fake.read_text() + '''
import time
(sessions / 'worker.jsonl').write_text(json.dumps({'type':'session_meta','payload':{'id':'worker'}})+'\\n')
parent = [{'type':'session_meta','payload':{'id':'parent'}},
          {'type':'event_msg','payload':{'type':'token_count','info':{'total_token_usage':
           {'input_tokens':70,'cached_input_tokens':40,'output_tokens':10,'total_tokens':PARENT}}}}]
rollout.write_text(''.join(json.dumps(r)+'\\n' for r in [rows[0]] + parent))
time.sleep(0.5)
print('completed-marker')
'''.replace('PARENT', str(parent)))
        result = fixture.probe()
        observed = json.loads((fixture.root / 'out' / 'result.json').read_text())
        stdout = (fixture.root / 'out' / 'method' / 'stdout.jsonl').read_text()
        ledger = json.loads((fixture.root / 'state' / 'codex-spend.json').read_text())
        return result, observed, stdout, ledger

    # Guarantee: an unknown worker cannot erase measured parent spend;
    # fault: unknown aggregate becomes zero for monitoring and reservation for settlement;
    # consumer: actual launch and ledger; alternative: below-cap parent retains reservation.
    def test_launch_unknown_worker_stops_and_settles_known_parent(self):
        result, observed, stdout, ledger = self.exercise_unknown_worker(300, 205)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(observed['sessions']['method']['reason'], 'cap')
        self.assertEqual(observed['sessions']['method']['overshoot_tokens'], 95)
        self.assertEqual(observed['tokens']['method'], 'n/a')
        self.assertNotIn('completed-marker', stdout)
        self.assertEqual([(row['tokens'], row['settled']) for row in ledger], [(300, True)])

    def test_launch_unknown_worker_below_cap_preserves_reservation(self):
        result, observed, stdout, ledger = self.exercise_unknown_worker(80, 1000)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(observed['sessions']['method']['state'], 'ok')
        self.assertEqual(observed['tokens']['method'], 'n/a')
        self.assertIn('completed-marker', stdout)
        self.assertEqual([(row['tokens'], row['settled']) for row in ledger], [(100, True), (100, True)])

    # Guarantee: source-aware final/live accounting rejects unidentifiable multi-file streams;
    # fault: separate anonymous files collapse into a false measured last snapshot;
    # consumer: route, cap and retained evidence; alternatives: one anonymous file and native IDs.
    def test_file_boundary_matrix(self):
        native = data(meta('parent'), count(120))
        anonymous = data(count(200))
        smaller = data(count(120))
        worker = data(meta('worker'), count(200))
        equal_worker = data(meta('worker'), count(120))
        fragment = data(meta('parent'), count(200))
        no_usage = data(meta('worker'))
        cases = [([native, anonymous], None, 200), ([anonymous, native], None, 200),
                 ([smaller, anonymous], None, 200), ([anonymous, smaller], None, 200),
                 ([anonymous, anonymous], None, 200), ([native, worker], 320, 320),
                 ([native, equal_worker], 240, 240), ([native, fragment], 200, 200),
                 ([fragment, native], 200, 200), ([native, no_usage], None, 120),
                 ([data(count(120), count(200))], 200, 200)]
        for pieces, expected, lower_bound in cases:
            with self.subTest(expected=expected, pieces=pieces), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                sessions = home / 'sessions'
                sessions.mkdir()
                for index, piece in enumerate(pieces):
                    (sessions / ('%02d.jsonl' % index)).write_bytes(piece)
                tail = route.RolloutTail(home, set())
                live = tail.read()
                accumulator = route.UsageAccumulator()
                for source, piece in enumerate(route.rollout_parts(home)):
                    accumulator.consume(piece, source=source)
                final = accumulator.result()
                self.assertEqual(final['total_tokens'] if final else None, expected)
                self.assertEqual(live['total_tokens'] if live else None, expected)
                self.assertEqual(accumulator.lower_bound(), lower_bound)
                self.assertEqual(tail.known_lower_bound, lower_bound)
                self.assertEqual(route.rollout_bytes(home), b'\n'.join(pieces))

    # Guarantee: physical boundaries survive real launch and redacted retention;
    # fault: two anonymous files collapse into a false complete snapshot;
    # consumer: probe and settled ledger; alternative: mixed files remain unknown in both orders.
    def test_launch_mixed_files_both_orders_and_redacted_map(self):
        for kind, extra, child_total in [('mixed', 'aaa.jsonl', 200), ('mixed', 'zzz.jsonl', 200),
                                         ('anonymous', 'aaa.jsonl', 200), ('anonymous', 'zzz.jsonl', 200),
                                         ('anonymous', 'aaa.jsonl', 120)]:
            with self.subTest(kind=kind, extra=extra, child_total=child_total):
                fixture = fixtures.CodexRouteTests(methodName='test_usage')
                fixture.setUp()
                self.addCleanup(fixture.doCleanups)
                fixture.fake.write_text(fixture.fake.read_text() + '''
parent = [{'type':'session_meta','payload':{'id':'parent'}},
          {'type':'event_msg','payload':{'type':'token_count','info':{'total_token_usage':{'total_tokens':120}}}},
          {'type':'note','payload':'sample-account-id'}]
if ANONYMOUS:
    parent = parent[1:]
anonymous = [{'type':'event_msg','payload':{'type':'token_count','info':{'total_token_usage':{'total_tokens':CHILD}}}}]
rollout.write_text(''.join(json.dumps(r)+'\\n' for r in [rows[0]] + parent))
(sessions / EXTRA).write_text(''.join(json.dumps(r)+'\\n' for r in anonymous))
'''.replace('EXTRA', repr(extra)).replace('ANONYMOUS', repr(kind == 'anonymous')).replace('CHILD', str(child_total)))
                result = fixture.probe()
                observed = json.loads((fixture.root / 'out' / 'result.json').read_text())
                retained = (fixture.root / 'out' / 'method' / 'rollout.jsonl').read_bytes()
                mapping = observed['sessions']['method']['rollout_files']
                self.assertEqual(result.returncode, 0)
                self.assertEqual(observed['tokens']['method'], 'n/a')
                self.assertEqual(len(mapping), 2)
                self.assertEqual(mapping[0]['start'], 0)
                self.assertEqual(mapping[1]['start'], mapping[0]['end'] + 1)
                self.assertEqual(retained[mapping[0]['end']:mapping[1]['start']], b'\n')
                self.assertEqual(mapping[-1]['end'], len(retained))
                for item in mapping:
                    self.assertEqual(item['sha256'], hashlib.sha256(retained[item['start']:item['end']]).hexdigest())
                if kind == 'anonymous':
                    decoded = [[json.loads(line) for line in retained[item['start']:item['end']].splitlines()
                                if line.strip()] for item in mapping]
                    self.assertTrue(all(not any(event.get('type') == 'session_meta' for event in part) for part in decoded))
                    self.assertEqual(sorted(event['payload']['info']['total_token_usage']['total_tokens']
                                            for part in decoded for event in part
                                            if event.get('type') == 'event_msg'), sorted([120, child_total]))
                self.assertIn(b'<account-id>', retained)
                self.assertNotIn(b'sample-account-id', retained)
                ledger = json.loads((fixture.root / 'state' / 'codex-spend.json').read_text())
                self.assertEqual([row['tokens'] for row in ledger], [max(120, child_total)] * 2)

    # Guarantee: the shared cancellation flag stops before start and during an actual launch;
    # fault: backend cancellation flag ignored; alternative: ordinary uncancelled controls above.
    def test_launch_shared_cancellation_flag(self):
        for before_start in (True, False):
            with self.subTest(before_start=before_start):
                fixture = fixtures.CodexRouteTests(methodName='test_usage')
                fixture.setUp()
                self.addCleanup(fixture.doCleanups)
                fixture.fake.write_text(fixture.fake.read_text() + '\nimport time\ntime.sleep(1)\n')
                root = fixture.root / 'direct'
                for name in ('home/codex', 'work', 'tmp'):
                    (root / name).mkdir(parents=True)
                cfg = SimpleNamespace(**fixture.data)
                login_data, needles, account = route.login(cfg)
                ledger = route.Ledger(cfg, 'probe')
                (fixture.root / 'state').mkdir()
                active = {'cancelled': before_start}
                original = route.RolloutTail.read
                def observe(tail):
                    result = original(tail)
                    if result:
                        active['cancelled'] = True
                    return result
                with patch.object(route.RolloutTail, 'read', observe):
                    result = route.launch(cfg, fixture.repo, root, 'test', ledger, login_data, needles, account, active)
                self.assertEqual((result['state'], result['reason']), ('incomplete', 'interrupted'))
                self.assertTrue(active['cancelled'])
                self.assertEqual(active['started'], not before_start)
                self.assertFalse((root / 'home/codex/auth.json').exists())
                self.assertTrue(ledger.rows[-1]['settled'])
