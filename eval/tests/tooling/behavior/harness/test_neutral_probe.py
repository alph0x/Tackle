"""Neutral transport components, with synthetic auth and no external requests.

These checks do not establish plan entitlement, live OAuth identity, cancellation,
provider cost, worker isolation, agent behavior or release readiness.
"""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[5]
HARNESS = ROOT / 'eval/behavior/harness'
sys.path.insert(0, str(HARNESS))
import neutral_probe as probe
import opaque_session as auth


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode() + b'\n'


def terminal(text='READY', **changes):
    response = dict(model='gpt-5.6-luna', status='completed',
                    output=[dict(type='message', role='assistant',
                                 content=[dict(type='output_text', text=text)])])
    response.update(changes)
    return b'event: response.completed\ndata: ' + encoded(dict(
        type='response.completed', response=response)) + b'\n'


class NeutralProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='neutral-components-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.state = self.root / 'state'
        self.state.mkdir(mode=0o700)

    def gate(self, **kwargs):
        return probe.AttemptGate(self.state, **kwargs)

    def consume(self, raw):
        parser = probe.TerminalConsumer()
        width = 7 if len(raw) < 8192 else 4096
        for i in range(0, len(raw), width):
            parser.feed(raw[i:i + width])
        return parser.finish()

    def test_fixed_wire_has_only_neutral_stateless_supported_fields(self):
        value = json.loads(probe.REQUEST)
        self.assertEqual(set(value), {'model', 'reasoning', 'input', 'store', 'stream'})
        self.assertEqual(value['model'], 'gpt-5.6-luna')
        self.assertEqual(value['reasoning'], {'effort': 'xhigh'})
        self.assertEqual(value['input'], [dict(role='user', content=[
            dict(type='input_text', text='Reply with the single word READY.')])])
        self.assertFalse(value['store'])
        self.assertTrue(value['stream'])
        self.assertEqual(probe.REQUEST_SHA,
                         'dc5adb600db15b2c2234cec070f6d03790be4643c288779d966dadecaaf2f7e5')

    def test_first_attempt_is_durable_and_restart_cannot_dispatch(self):
        calls = []
        with self.gate() as gate:
            gate.initiate()
            calls.append(1)
        with self.assertRaises(probe.Refusal):
            with self.gate() as gate:
                gate.initiate()
                calls.append(2)
        self.assertEqual(calls, [1])
        (self.state / 'attempt.json').unlink()
        with self.assertRaises(probe.Refusal):
            with self.gate():
                self.fail('missing checkpoint reset a consumed gate')

    def test_unknown_and_completed_outcomes_never_refund_the_unit(self):
        for result in ('uncertain', 'completed'):
            with self.subTest(result=result):
                path = self.root / result
                path.mkdir(mode=0o700)
                with probe.AttemptGate(path) as gate:
                    gate.initiate()
                    gate.finalize(result)
                with self.assertRaises(probe.Refusal):
                    with probe.AttemptGate(path) as gate:
                        gate.initiate()

    def test_concurrent_gate_refuses_without_changing_first_reservation(self):
        with self.gate() as gate:
            before = (self.state / 'attempt.json').read_bytes()
            with self.assertRaises(probe.Refusal):
                with self.gate():
                    self.fail('concurrent gate admitted')
            self.assertEqual((self.state / 'attempt.json').read_bytes(), before)

    def test_deadline_is_carried_across_restart_and_expiry_refuses(self):
        with self.gate(clock=lambda: 100) as gate:
            self.assertEqual(gate.remaining(), 120)
        with self.gate(clock=lambda: 110) as gate:
            self.assertEqual(gate.remaining(), 110)
        with self.assertRaises(probe.Refusal):
            with self.gate(clock=lambda: 221):
                pass

    def test_monotonic_rollback_and_corrupt_state_refuse(self):
        with self.gate(clock=lambda: 100):
            pass
        with self.assertRaises(probe.Refusal):
            with self.gate(clock=lambda: 99):
                pass
        (self.state / 'attempt.json').write_bytes(b'broken')
        with self.assertRaises(probe.Refusal):
            with self.gate():
                pass

    def test_links_and_insecure_state_are_rejected(self):
        target = self.root / 'target'
        target.write_bytes(b'')
        (self.state / 'attempt.lock').symlink_to(target)
        with self.assertRaises(probe.Refusal):
            with self.gate():
                pass
        self.assertEqual(target.read_bytes(), b'')

    def test_completed_stream_and_usage_are_actual_optional_facts(self):
        usage = dict(input_tokens=7, output_tokens=2, total_tokens=9)
        result = self.consume(terminal(usage=usage))
        self.assertEqual(result, dict(status='completed', text='READY',
                                    model='gpt-5.6-luna', effort='n/a',
                                    usage=usage, cost_usd='n/a'))
        self.assertEqual(self.consume(terminal())['usage'], 'n/a')

    def test_nonterminal_failed_and_duplicate_streams_are_not_success(self):
        for raw in (b'', b'data: {"type":"response.failed"}\n\n',
                    terminal() + terminal(), terminal(status='incomplete')):
            with self.subTest(raw=raw), self.assertRaises(probe.Refusal):
                self.consume(raw)

    def test_tool_or_changed_model_never_supplies_completion(self):
        for changes in (dict(output=[dict(type='function_call', name='Read')]),
                        dict(model='gpt-6.1-sol')):
            with self.subTest(changes=changes), self.assertRaises(probe.Refusal):
                self.consume(terminal(**changes))

    def test_sensitive_and_unexpected_output_is_not_retained_or_hashed(self):
        for text in ('Bearer synthetic-secret', 'sk-' + 'x' * 40,
                     'READY plus private details', 'access_token=synthetic'):
            parser = probe.TerminalConsumer()
            with self.subTest(text=text), self.assertRaises(probe.Refusal):
                parser.feed(terminal(text))
            self.assertIsNone(parser.result)
            with self.assertRaises(probe.Refusal):
                parser.feed(terminal())
            with self.assertRaises(probe.Refusal):
                parser.finish()

    def test_oversized_and_malformed_streams_refuse(self):
        for raw in (b'x' * (probe.MAX_STREAM + 1), b'data: {bad}\n\n',
                    b'data: {"type":"response.completed","type":"response.failed"}\n\n'):
            with self.subTest(raw=raw[:30]), self.assertRaises(probe.Refusal):
                self.consume(raw)

    def test_sse_crlf_boundaries_and_done_marker_are_valid_alternatives(self):
        self.assertEqual(self.consume(terminal().replace(b'\n', b'\r\n') +
                                     b'data: [DONE]\r\n\r\n')['text'], 'READY')

    def test_dispatch_requires_observed_admission_before_reserving(self):
        with self.gate() as gate:
            with self.assertRaises(probe.Refusal):
                probe.dispatch(gate, None, lambda *_: self.fail('dispatch reached'))
            self.assertEqual(gate.state['initiated'], 0)

    def test_admitted_transport_is_called_once_and_failure_stays_consumed(self):
        # A test authority is explicit; production code supplies no policy observer.
        admission = probe.Admission.for_qualification()
        sender = probe.QualificationSender(fail=True)
        calls = sender.calls
        with self.gate() as gate:
            with self.assertRaises(probe.Refusal):
                probe.dispatch(gate, admission, sender)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], probe.REQUEST)
        self.assertEqual(json.loads((self.state / 'attempt.json').read_bytes())['initiated'], 1)

    def test_transport_connection_has_one_fixed_endpoint_and_no_retries(self):
        fake = mock.Mock()
        response = fake.getresponse.return_value
        response.status = 200
        response.getheader.return_value = 'text/event-stream'
        response.read.side_effect = [terminal(), b'']
        with mock.patch.object(probe.http.client, 'HTTPSConnection', return_value=fake) as factory:
            result = probe.single_https_request('synthetic-bearer', probe.REQUEST, 1)
        factory.assert_called_once()
        self.assertEqual(factory.call_args.args[0], 'api.openai.com')
        self.assertEqual(fake.request.call_count, 1)
        self.assertEqual(fake.request.call_args.args[:2], ('POST', '/v1/responses'))
        self.assertEqual(result['text'], 'READY')
        fake.close.assert_called_once()

    def test_redirect_and_network_error_have_no_retry(self):
        for status in (302, 401, 429, 500):
            fake = mock.Mock()
            fake.getresponse.return_value.status = status
            with self.subTest(status=status), mock.patch.object(
                    probe.http.client, 'HTTPSConnection', return_value=fake):
                with self.assertRaises(probe.Refusal):
                    probe.single_https_request('synthetic-bearer', probe.REQUEST, 1)
            self.assertEqual(fake.request.call_count, 1)
            fake.getresponse.return_value.read.assert_not_called()


class OpaqueSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='opaque-synthetic-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.store = self.home / '.tackle/runtime/chatgpt-oauth'
        self.store.mkdir(mode=0o700, parents=True)
        for p in (self.home / '.tackle', self.home / '.tackle/runtime', self.store):
            p.chmod(0o700)
        self.values = dict(issuer='https://auth.openai.com', client_id='oaiapp_synthetic',
                           subject='synthetic-subject', token_type='Bearer',
                           access_token='synthetic-bearer', scopes=['resource.invoke',
                           'chatgpt.tokens.use.direct'], saved_at=1000, expires_at=2000,
                           authentication_reference=dict(iss='https://auth.openai.com',
                           sub='synthetic-subject', aud='oaiapp_synthetic'))
        self.put('credentials.json', self.values)
        self.put('registration.json', dict(client_id='oaiapp_synthetic'))
        self.put('pending.json', dict(stage='complete', client_id='oaiapp_synthetic'))
        self.put('invocation.lock', {})

    def put(self, name, value):
        p = self.store / name
        p.write_bytes(encoded(value))
        p.chmod(0o600)

    def inspect(self):
        return auth.inspect_existing(self.home, now=1100)

    def test_valid_session_reports_retained_binding_and_no_paid_admission(self):
        result = self.inspect()
        self.assertEqual(result['stage'], 'session_ready')
        self.assertEqual(result['binding'], 'retained_binding_checked')
        self.assertEqual(result['included_only_admission'], 'unestablished')
        self.assertEqual(result['inference_requests'], 0)
        self.assertNotIn('synthetic', json.dumps(result))
        self.put('pending.json', dict(stage='complete'))
        self.assertEqual(self.inspect()['stage'], 'session_ready')

    def test_expired_session_and_insufficient_lifetime_refuse(self):
        for expiry in (1100, 1219):
            self.values['expires_at'] = expiry
            self.put('credentials.json', self.values)
            self.assertEqual(self.inspect()['reason'], 'expired')

    def test_changed_client_subject_issuer_and_scope_refuse(self):
        changes = [dict(client_id='oaiapp_other'), dict(subject='other'),
                   dict(issuer='https://example.invalid'), dict(scopes=[])]
        original = dict(self.values)
        for change in changes:
            self.put('credentials.json', {**original, **change})
            with self.subTest(change=change):
                self.assertEqual(self.inspect()['stage'], 'refused')

    def test_existing_source_is_never_created_or_written(self):
        before = {p.name: p.read_bytes() for p in self.store.iterdir()}
        self.inspect()
        self.assertEqual({p.name: p.read_bytes() for p in self.store.iterdir()}, before)
        missing = self.home / 'missing'
        self.assertEqual(auth.inspect_existing(missing, now=1100)['stage'], 'refused')
        self.assertFalse(missing.exists())

    def test_refresh_fence_and_unfinished_authorization_refuse(self):
        self.put('refresh-inflight.json', dict(stage='inflight'))
        self.assertEqual(self.inspect()['stage'], 'refused')
        (self.store / 'refresh-inflight.json').unlink()
        self.put('pending.json', dict(stage='exchange_pending', client_id='oaiapp_synthetic'))
        self.assertEqual(self.inspect()['stage'], 'refused')

    def test_unsafe_symlink_and_mode_do_not_expose_target(self):
        p = self.store / 'credentials.json'
        p.chmod(0o644)
        self.assertEqual(self.inspect()['stage'], 'refused')
        p.unlink()
        p.symlink_to(self.home / 'outside')
        self.assertEqual(self.inspect()['stage'], 'refused')

    def test_busy_store_refuses_without_wait_or_mutation(self):
        with open(self.store / 'invocation.lock', 'rb') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.inspect()['reason'], 'busy')

    def test_duplicate_keys_nonfinite_dates_and_control_bearer_refuse(self):
        p = self.store / 'credentials.json'
        for value in ({**self.values, 'saved_at': float('nan')},
                      {**self.values, 'access_token': 'synthetic\r\nbody'}):
            self.put('credentials.json', value)
            self.assertEqual(self.inspect()['stage'], 'refused')
        p.write_bytes(b'{"issuer":"secret","issuer":"other"}')
        self.assertEqual(self.inspect()['stage'], 'refused')


if __name__ == '__main__':
    unittest.main()
