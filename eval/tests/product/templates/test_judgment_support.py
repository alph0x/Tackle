"""Optional, bounded Judgment Layer support through the two shipped System One modules."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from test_system_one_functional import load_recipe, state
from test_system_one_integration import load_integration

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / 'skills/tackle/scripts'
BRIEF_SHA = 'b86e5991c4a16c74abfd970b9d66a3b31f6c5ed8f1d96f9946f9ed7845c044a9'
RESULT_KEYS = {'judgment', 'source', 'reason', 'state', 'question', 'model', 'confidence'}
OLD_USES = ('resume-selection', 'failure-class', 'no-progress', 'intake-size')


def bounded_policy(resolved=None, eligible=None):
    selected = ['retry-after-correction'] if eligible is None else list(eligible)
    choices = ['retry-after-correction', 'rerun-read-only']
    return {'choices': choices, 'eligible': selected,
            'fallback': selected[0] if selected else 'defer', 'resolved': resolved}


def evidence_policy(resolved=None):
    choices = ['supports', 'partial', 'insufficient', 'contradictory']
    return {'choices': choices, 'eligible': list(choices), 'fallback': 'requires-review', 'resolved': resolved}


def local_for(policy):
    return {'choice': policy['resolved'] if policy['resolved'] is not None else policy['fallback'],
            'confidence': None}


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode('utf-8')


def budget_directory(workspace, scope):
    return (Path(workspace) / 'verification-records' / scope['owner'] / 'judgment-budget'
            / hashlib.sha256(scope['identity'].encode()).hexdigest())


def scope_record(workspace, scope):
    return {'schema': 'tackle-judgment-budget/1', 'workspace': str(Path(workspace).resolve()),
            'owner': scope['owner'], 'identity': scope['identity'],
            'contract_sha256': scope['contract_sha256'],
            'limits': {'bounded-recovery': 1, 'evidence-signal': 1}}


def reservation_record(workspace, scope, use, policy):
    scope_bytes = canonical_bytes(scope_record(workspace, scope))
    return {'scope_sha256': hashlib.sha256(scope_bytes).hexdigest(),
            'policy_sha256': hashlib.sha256(canonical_bytes(policy)).hexdigest(),
            'use': use, 'status': 'reserved'}


def budget_scope(identity):
    return {'owner': 'T-ADVICE', 'identity': identity, 'contract_sha256': BRIEF_SHA}


def normalized(choice, confidence=0.9, model='jev-1.13.0'):
    return {'model': model, 'confidence': confidence,
            'judgment': {'choice': choice, 'confidence': confidence}}


def fake_factory(choice, confidence=0.9, model='jev-1.13.0', before_construct=None, on_send=None):
    answer = SimpleNamespace(type='choice', choice=choice, score=choice, confidence=confidence)

    def send(**kwargs):
        if on_send is not None:
            on_send(kwargs)
        return SimpleNamespace(model=model, answers={'judgment': answer})

    def factory(**kwargs):
        if before_construct is not None:
            before_construct(kwargs)
        return SimpleNamespace(system_one=send, close=lambda: None)
    return factory


# This bootstrap runs only in the isolated concurrency/restart fixtures. It imports the named
# state module from the checkout path and supplies a local fake response; it never starts a CLI.
_CHILD_BOOTSTRAP = r'''import importlib.util, json, os, pathlib, sys
root = pathlib.Path(os.environ['T02_ROOT'])
sys.path.insert(0, str(root / 'skills/tackle/scripts'))
spec = importlib.util.spec_from_file_location('system_one_state', root / 'skills/tackle/scripts/system_one_state.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
decision_spec = importlib.util.spec_from_file_location('system_one_decide', root / 'skills/tackle/scripts/system_one_decide.py')
decision_module = importlib.util.module_from_spec(decision_spec)
decision_spec.loader.exec_module(decision_module)
workspace = pathlib.Path(os.environ['T02_WORKSPACE'])
use = os.environ['T02_USE']
policy = json.loads(os.environ['T02_POLICY'])
scope = json.loads(os.environ['T02_SCOPE'])
choice = 'retry-after-correction' if use == 'bounded-recovery' else 'supports'
answer = type('Answer', (), {'type': 'choice', 'choice': choice, 'score': choice, 'confidence': 0.9})()
def append_log(name):
    path = os.environ.get(name)
    if path:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, (use + '\n').encode())
        finally:
            os.close(fd)
def system_one(**kwargs):
    append_log('T02_SEND_LOG')
    return type('Response', (), {'model': 'jev-1.13.0', 'answers': {'judgment': answer}})()
client = type('Client', (), {'system_one': lambda self, **kwargs: system_one(**kwargs), 'close': lambda self: None})()
def factory(**kwargs):
    append_log('T02_FACTORY_LOG')
    if os.environ.get('T02_CRASH_AFTER_RESERVATION') == '1':
        raise KeyboardInterrupt('fixture interruption after reservation')
    return client
local = {'choice': policy['resolved'] if policy['resolved'] is not None else policy['fallback'], 'confidence': None}
result = module.system_one_use(workspace=workspace, configured=True, asked=[], use=use,
    fragment='Public fixture context', local_judgment=local, sensitivity='public',
    decide=decision_module.system_one_decide, client_factory=factory,
    support_policy=policy, budget_scope=scope)
print(json.dumps(result, sort_keys=True))
'''


class JudgmentSupportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='tackle-judgment-support-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        self.ns = load_integration()
        self.decide = load_recipe()

    def answer(self, value='yes'):
        return self.ns['record_consent'](self.workspace, value, 'Owner', '2026-10-22')

    def sdk_absent(self):
        # Same guard as test_system_one_integration: without the official SDK the adapter keeps the local
        # fallback and the SDK-dependent assertions are not run, unless the scoped acceptance requires it.
        if importlib.util.find_spec('typesafe_sdk') is not None:
            return False
        self.assertNotEqual(os.environ.get('TACKLE_TYPESAFE_SDK_REQUIRED'), '1', 'Scoped acceptance requires official SDK')
        return True

    def call(self, use, policy, identity, *, workspace=None, client_factory=None, sensitivity='public',
             fragment='Public fixture context', configured=True):
        target = self.workspace if workspace is None else Path(workspace)
        return self.ns['system_one_use'](
            workspace=target, configured=configured, asked=[], use=use, fragment=fragment,
            local_judgment=local_for(policy), sensitivity=sensitivity, decide=self.decide,
            client_factory=client_factory, support_policy=policy,
            budget_scope=budget_scope(identity))

    def test_new_choice_wire_domains_and_local_fallbacks(self):
        # The pure function accepts normalized new-use responses only against the planner's policy.
        for use, policy, choice in (
            ('bounded-recovery', bounded_policy(), 'retry-after-correction'),
            ('evidence-signal', evidence_policy(), 'supports'),
        ):
            with self.subTest(use=use):
                local = local_for(policy)
                seen = []
                result = self.decide(state(), use, 'Public failure details', local,
                                     lambda request: (seen.append(request) or normalized(choice)),
                                     support_policy=policy)
                self.assertEqual(result['judgment'], {'choice': choice, 'confidence': 0.9})
                self.assertEqual(result['source'], 'jev')
                self.assertEqual(set(result), RESULT_KEYS)
                self.assertEqual(len(seen), 1)
                boundary = self.decide(state(), use, 'Public failure details', local,
                                       lambda request: normalized(choice, 0.8), support_policy=policy)
                below = self.decide(state(), use, 'Public failure details', local,
                                    lambda request: normalized(choice, 0.799), support_policy=policy)
                self.assertEqual((boundary['source'], boundary['confidence']), ('jev', 0.8))
                self.assertEqual(below['source'], 'local')
                self.assertEqual(below['judgment'], local)

        # Recovery IDs belong to the planner's public policy, beyond the two example labels.
        custom_policy = {'choices': ['recheck-owned-fixture', 'restore-owned-staging'],
                         'eligible': ['recheck-owned-fixture'], 'fallback': 'recheck-owned-fixture',
                         'resolved': None}
        for response_choice in custom_policy['choices']:
            with self.subTest(boundary='custom-policy-pure', response=response_choice):
                custom_requests = []
                custom_result = self.decide(
                    state(), 'bounded-recovery', 'Public custom recovery fixture', local_for(custom_policy),
                    lambda request, choice=response_choice: (custom_requests.append(request) or normalized(choice)),
                    support_policy=custom_policy)
                self.assertEqual(len(custom_requests), 1)
                expected = ({'choice': response_choice, 'confidence': 0.9}
                            if response_choice in custom_policy['eligible'] else local_for(custom_policy))
                self.assertEqual(custom_result['judgment'], expected)
                self.assertEqual(custom_result['source'],
                                 'jev' if response_choice in custom_policy['eligible'] else 'local')

        policy = bounded_policy()
        local = local_for(policy)
        # A single eligible option with resolved=None still consults when the brief leaves uncertainty.
        consulted = []
        result = self.decide(state(), 'bounded-recovery', 'Public failure details', local,
                             lambda request: (consulted.append(request) or normalized('retry-after-correction')),
                             support_policy=policy)
        self.assertEqual(len(consulted), 1)
        self.assertEqual(result['source'], 'jev')

        # A declared defer response is valid; an empty eligible set never consults.
        deferred = self.decide(state(), 'bounded-recovery', 'Public failure details', local,
                               lambda request: normalized('defer'), support_policy=policy)
        self.assertEqual((deferred['source'], deferred['judgment']['choice']), ('jev', 'defer'))
        empty = bounded_policy(eligible=[])
        empty_requests = []
        empty_result = self.decide(state(), 'bounded-recovery', 'Public failure details', local_for(empty),
                                   lambda request: (empty_requests.append(request) or normalized('defer')),
                                   support_policy=empty)
        self.assertEqual((empty_result['source'], empty_result['judgment'], empty_requests),
                         ('local', local_for(empty), []))

        # An explicit deterministic resolution returns before transport; it creates no adapter effects.
        resolved = bounded_policy(resolved='retry-after-correction')
        consulted.clear()
        skipped = self.decide(state(), 'bounded-recovery', 'Public failure details', local_for(resolved),
                              lambda request: (consulted.append(request) or normalized('retry-after-correction')),
                              support_policy=resolved)
        self.assertEqual((skipped['reason'], skipped['source'], consulted),
                         ('deterministic-resolution', 'local', []))

        self.answer('yes')
        adapter_factory_calls, adapter_request_calls = [], []
        adapter_resolved = self.call(
            'bounded-recovery', resolved, 'adapter-deterministic-skip-01',
            client_factory=fake_factory('retry-after-correction',
                                        before_construct=lambda kwargs: adapter_factory_calls.append(kwargs),
                                        on_send=lambda kwargs: adapter_request_calls.append(kwargs)))
        self.assertEqual((adapter_resolved['reason'], adapter_resolved['source']),
                         ('deterministic-resolution', 'local'))
        self.assertEqual((adapter_factory_calls, adapter_request_calls), ([], []))
        adapter_budget = budget_directory(self.workspace, budget_scope('adapter-deterministic-skip-01'))
        self.assertFalse(adapter_budget.exists(), 'resolved adapter call must not create budget files')

        # Invalid predicates/policies and all invalid response neighbors preserve the exact local choice.
        for invalid in (
            dict(bounded_policy(), resolved='rerun-read-only'),
            dict(bounded_policy(), eligible=['not-a-choice']),
            dict(bounded_policy(), eligible=['retry-after-correction', 'retry-after-correction']),
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    self.decide(state(), 'bounded-recovery', 'Public failure details', local,
                                lambda request: self.fail('invalid policy must be rejected before transport'),
                                support_policy=invalid)
        for invalid_evidence in (
            dict(evidence_policy(), choices=['supports', 'partial']),
            dict(evidence_policy(), eligible=['supports', 'outside-domain']),
            dict(evidence_policy(), fallback='supports'),
            dict(evidence_policy(), resolved='outside-domain'),
        ):
            with self.subTest(invalid_evidence=invalid_evidence):
                with self.assertRaises(ValueError):
                    self.decide(state(), 'evidence-signal', 'Public failure details', local_for(evidence_policy()),
                                lambda request: self.fail('closed evidence policy must reject before transport'),
                                support_policy=invalid_evidence)

        malformed = [
            normalized('retry-after-correction', 0.799),
            normalized('retry-after-correction', 1.01),
            normalized('retry-after-correction', -0.01),
            normalized('retry-after-correction', float('nan')),
            normalized('retry-after-correction', True),
            normalized('retry-after-correction', 0.9, model='other-model'),
            {'model': 'jev-1.13.0', 'confidence': 0.9, 'judgment': {'choice': 'retry-after-correction', 'confidence': 0.8}},
            normalized('rerun-read-only'),
            normalized('outside-policy'),
        ]
        for index, raw in enumerate(malformed):
            with self.subTest(response=index):
                result = self.decide(state(), 'bounded-recovery', 'Public failure details', local,
                                     lambda request, raw=raw: raw, support_policy=policy)
                self.assertEqual(result['source'], 'local')
                self.assertEqual(result['judgment'], local)

        evidence_local = local_for(evidence_policy())
        evidence_malformed = [
            normalized('supports', 0.799), normalized('supports', 1.01),
            normalized('supports', -0.01), normalized('supports', float('nan')),
            normalized('supports', True), normalized('supports', model='other-model'),
            {'model': 'jev-1.13.0', 'confidence': 0.9,
             'judgment': {'choice': 'supports', 'confidence': 0.8}},
            normalized('outside-domain'),
        ]
        for index, raw in enumerate(evidence_malformed):
            with self.subTest(evidence_response=index):
                result = self.decide(state(), 'evidence-signal', 'Public failure details', evidence_local,
                                     lambda request, raw=raw: raw, support_policy=evidence_policy())
                self.assertEqual(result['source'], 'local')
                self.assertEqual(result['judgment'], evidence_local)

        # Transport exceptions, like malformed responses, preserve the local fallback.
        for use, policy_for_failure, local_failure in (
            ('bounded-recovery', policy, local), ('evidence-signal', evidence_policy(), evidence_local),
        ):
            for failure in (TimeoutError('fixture timeout'), OSError('fixture transport error')):
                with self.subTest(use=use, transport=type(failure).__name__):
                    result = self.decide(state(), use, 'Public failure details', local_failure,
                                         lambda request, failure=failure: (_ for _ in ()).throw(failure),
                                         support_policy=policy_for_failure)
                    self.assertEqual(result['source'], 'local')
                    self.assertEqual(result['judgment'], local_failure)

        # The state adapter uses the official SDK serializer with an in-process transport.
        if self.sdk_absent():
            self.answer('yes')
            absent = self.call('evidence-signal', evidence_policy(), 'wire-public-identity',
                               client_factory=fake_factory('supports'))
            self.assertEqual((absent['source'], absent['reason']), ('local', 'sdk-unavailable'))
            self.assertEqual(set(absent), RESULT_KEYS)
            return
        import httpx2
        from typesafe_sdk import TypeSafeClient
        self.answer('yes')
        captured = []

        def handle(request):
            captured.append(request)
            return httpx2.Response(200, json={
                'model': 'jev-1.13.0', 'usage': {'input_tokens': 1, 'output_tokens': 1},
                'answers': {'judgment': {'type': 'choice', 'choice': 'supports', 'confidence': 0.9,
                                         'probabilities': {'supports': 1.0}}},
            })

        def factory(**kwargs):
            return TypeSafeClient(api_key='fictitious-test-key', transport=httpx2.MockTransport(handle), **kwargs)

        evidence = evidence_policy()
        adapter_result = self.call('evidence-signal', evidence, 'wire-public-identity', client_factory=factory)
        self.assertEqual(adapter_result['source'], 'jev', adapter_result)
        self.assertEqual(set(adapter_result), RESULT_KEYS)
        self.assertEqual(len(captured), 1)
        wire = json.loads(captured[0].content)
        self.assertEqual(set(wire), {'model', 'state', 'questions'})
        self.assertEqual(wire['state'], {'fragment': 'Public fixture context'})
        evidence_criteria = wire['questions']['judgment']['criteria']
        self.assertEqual(set(evidence_criteria), set(evidence['choices']))
        for private in (str(self.workspace), 'wire-public-identity', 'T-ADVICE', BRIEF_SHA):
            self.assertNotIn(private, json.dumps(wire), private)

        bounded = bounded_policy()
        bounded_captured = []

        def bounded_handle(request):
            bounded_captured.append(request)
            return httpx2.Response(200, json={
                'model': 'jev-1.13.0', 'usage': {'input_tokens': 1, 'output_tokens': 1},
                'answers': {'judgment': {'type': 'choice', 'choice': 'retry-after-correction', 'confidence': 0.9,
                                         'probabilities': {'retry-after-correction': 1.0}}},
            })

        def bounded_factory(**kwargs):
            return TypeSafeClient(api_key='fictitious-test-key', transport=httpx2.MockTransport(bounded_handle), **kwargs)

        bounded_adapter = self.call('bounded-recovery', bounded, 'wire-bounded-identity',
                                    client_factory=bounded_factory)
        self.assertEqual(bounded_adapter['source'], 'jev', bounded_adapter)
        bounded_wire = json.loads(bounded_captured[0].content)
        recovery_criteria = bounded_wire['questions']['judgment']['criteria']
        labels = set(recovery_criteria)
        self.assertEqual(labels, set(bounded['eligible']) | {'defer'})
        for forbidden in set(bounded['choices']) - set(bounded['eligible']):
            self.assertNotIn(forbidden, labels)
        for private in (str(self.workspace), 'wire-bounded-identity', 'T-ADVICE', BRIEF_SHA):
            self.assertNotIn(private, json.dumps(bounded_wire), private)

        for response_choice in custom_policy['choices']:
            with self.subTest(boundary='custom-policy-wire', response=response_choice):
                custom_captured = []

                def custom_handle(request):
                    custom_captured.append(request)
                    return httpx2.Response(200, json={
                        'model': 'jev-1.13.0', 'usage': {'input_tokens': 1, 'output_tokens': 1},
                        'answers': {'judgment': {'type': 'choice', 'choice': response_choice,
                                                 'confidence': 0.9,
                                                 'probabilities': {response_choice: 1.0}}},
                    })

                def custom_factory(**kwargs):
                    return TypeSafeClient(api_key='fictitious-test-key',
                                          transport=httpx2.MockTransport(custom_handle), **kwargs)

                custom_result = self.call('bounded-recovery', custom_policy,
                                          'custom-policy-wire-' + response_choice,
                                          client_factory=custom_factory)
                self.assertEqual(len(custom_captured), 1)
                custom_wire = json.loads(custom_captured[0].content)
                self.assertEqual(set(custom_wire['questions']['judgment']['criteria']),
                                 {'recheck-owned-fixture', 'defer'})
                expected = ({'choice': response_choice, 'confidence': 0.9}
                            if response_choice in custom_policy['eligible'] else local_for(custom_policy))
                self.assertEqual(custom_result['judgment'], expected)
                self.assertEqual(custom_result['source'],
                                 'jev' if response_choice in custom_policy['eligible'] else 'local')

        # Missing yes/client and nonpublic dynamic content stay local and reserve nothing.
        for case, kwargs in (
            ('no-consent', {'workspace': self.root / 'no-consent'}),
            ('no-client', {'client_factory': None}),
            ('private-fragment', {'sensitivity': 'private'}),
            ('unknown-fragment', {'sensitivity': 'unknown'}),
            ('not-configured', {'configured': False}),
        ):
            with self.subTest(case=case):
                workspace = kwargs.pop('workspace', self.workspace)
                workspace.mkdir(exist_ok=True)
                if case == 'not-configured':
                    self.ns = load_integration()
                    self.ns['record_consent'](workspace, 'yes', 'Owner', '2026-10-22')
                construct_calls, request_calls = [], []
                client = fake_factory('supports', before_construct=lambda call: construct_calls.append(call),
                                      on_send=lambda call: request_calls.append(call))
                if case != 'no-client':
                    kwargs.setdefault('client_factory', client)
                result = self.call('evidence-signal', evidence_policy(), 'no-send-' + case,
                                   workspace=workspace, **kwargs)
                self.assertEqual(result['source'], 'local')
                self.assertEqual(result['judgment'], local_for(evidence_policy()))
                scope = budget_scope('no-send-' + case)
                reservation = (workspace / 'verification-records/T-ADVICE/judgment-budget'
                               / hashlib.sha256(scope['identity'].encode()).hexdigest()
                               / 'evidence-signal.reservation.json')
                self.assertFalse(reservation.exists(), f'{case} must not consume a slot')
                self.assertEqual((construct_calls, request_calls), ([], []),
                                 f'{case} must block before client construction and send')

    def test_budget_survives_errors_and_process_restart(self):
        self.answer('yes')
        policy = evidence_policy()
        scope = budget_scope('budget-error-restart-01')
        if self.sdk_absent():
            constructed = []
            absent = self.call('evidence-signal', policy, scope['identity'],
                               client_factory=fake_factory('supports', before_construct=lambda kwargs: constructed.append(kwargs)))
            self.assertEqual((absent['source'], absent['reason'], absent['judgment']),
                             ('local', 'sdk-unavailable', local_for(policy)))
            self.assertEqual(constructed, [])
            return
        expected_directory = budget_directory(self.workspace, scope)
        expected_reservation = expected_directory / 'evidence-signal.reservation.json'
        expected_scope = scope_record(self.workspace, scope)
        expected_reservation_json = reservation_record(self.workspace, scope, 'evidence-signal', policy)
        factory_observations, fsync_inodes, factory_events = [], [], []
        real_fsync = os.fsync

        def observe_fsync(fd):
            result = real_fsync(fd)
            metadata = os.fstat(fd)
            fsync_inodes.append((metadata.st_dev, metadata.st_ino))
            factory_events.append(('fsync', metadata.st_dev, metadata.st_ino))
            return result

        def raising_factory(**kwargs):
            scope_bytes = (expected_directory / 'scope.json').read_bytes()
            reservation_bytes = expected_reservation.read_bytes()
            metadata = expected_reservation.stat()
            factory_observations.append((scope_bytes, reservation_bytes, metadata.st_dev, metadata.st_ino))
            factory_events.append(('factory', metadata.st_dev, metadata.st_ino))
            raise RuntimeError('fixture ordinary client construction error')

        with patch.object(os, 'fsync', side_effect=observe_fsync):
            result = self.call('evidence-signal', policy, scope['identity'], client_factory=raising_factory)
        self.assertEqual(result['source'], 'local')
        self.assertEqual(len(factory_observations), 1)
        scope_bytes, reservation_bytes, reservation_dev, reservation_ino = factory_observations[0]
        self.assertEqual(scope_bytes, canonical_bytes(expected_scope))
        self.assertEqual(json.loads(reservation_bytes), expected_reservation_json)
        self.assertEqual(reservation_bytes, canonical_bytes(expected_reservation_json))
        self.assertIn((reservation_dev, reservation_ino), fsync_inodes,
                      'reservation fsync must complete before factory construction')
        fsync_position = factory_events.index(('fsync', reservation_dev, reservation_ino))
        factory_position = factory_events.index(('factory', reservation_dev, reservation_ino))
        self.assertLess(fsync_position, factory_position)
        terminal_files = list(expected_reservation.parent.glob('evidence-signal.terminal.json'))
        self.assertEqual(len(terminal_files), 1)
        terminal = json.loads(terminal_files[0].read_text(encoding='utf-8'))
        self.assertTrue(terminal.get('status'))
        self.assertTrue(terminal.get('reason'))

        restarted = load_integration()
        local = local_for(policy)
        attempted = []
        replay = restarted['system_one_use'](
            workspace=self.workspace, configured=True, asked=[], use='evidence-signal',
            fragment='Public fixture context', local_judgment=local, sensitivity='public',
            decide=load_recipe(), client_factory=fake_factory('supports', before_construct=lambda kwargs: attempted.append(kwargs)),
            support_policy=policy, budget_scope=scope)
        self.assertEqual(replay['source'], 'local')
        self.assertEqual(replay['judgment'], local)
        self.assertEqual(attempted, [])
        self.assertTrue(terminal_files[0].is_file())

        # A factory can complete a request before raising; its send outcome cannot be known-unsent.
        import httpx2
        effect_scope = budget_scope('factory-request-then-error-01')
        factory_requests = []

        def factory_handle(request):
            factory_requests.append(request)
            return httpx2.Response(200, json={'observed': True})

        def request_then_raise_factory(**kwargs):
            with httpx2.Client(transport=httpx2.MockTransport(factory_handle)) as client:
                client.post('https://factory-fixture.invalid/judgment', json={'fixture': 'public'})
            raise RuntimeError('fixture factory failed after its request')

        effect_result = self.call('evidence-signal', policy, effect_scope['identity'],
                                  client_factory=request_then_raise_factory)
        self.assertEqual(len(factory_requests), 1)
        self.assertEqual(factory_requests[0].method, 'POST')
        self.assertEqual(effect_result['source'], 'local')
        self.assertEqual(effect_result['judgment'], local)
        effect_directory = budget_directory(self.workspace, effect_scope)
        self.assertTrue((effect_directory / 'evidence-signal.reservation.json').is_file())
        effect_terminal = json.loads((effect_directory / 'evidence-signal.terminal.json').read_text())
        self.assertEqual(effect_terminal['status'], 'unknown')
        restarted_after_effect = load_integration()
        effect_replay_factories = []
        effect_replay = restarted_after_effect['system_one_use'](
            workspace=self.workspace, configured=True, asked=[], use='evidence-signal',
            fragment='Public fixture context', local_judgment=local, sensitivity='public',
            decide=load_recipe(), support_policy=policy, budget_scope=effect_scope,
            client_factory=fake_factory('supports',
                                        before_construct=lambda kwargs: effect_replay_factories.append(kwargs),
                                        on_send=lambda kwargs: factory_requests.append(kwargs)))
        self.assertEqual((effect_replay['source'], effect_replay['judgment']), ('local', local))
        self.assertEqual(effect_replay_factories, [])
        self.assertEqual(len(factory_requests), 1)

        response_scope = budget_scope('observed-response-terminal-control-01')
        response_requests = []
        response_result = self.call('evidence-signal', policy, response_scope['identity'],
                                    client_factory=fake_factory('supports',
                                        on_send=lambda kwargs: response_requests.append(kwargs)))
        self.assertEqual(len(response_requests), 1)
        self.assertEqual(response_result['source'], 'jev')
        response_terminal = json.loads((budget_directory(self.workspace, response_scope)
                                        / 'evidence-signal.terminal.json').read_text())
        self.assertEqual(response_terminal['status'], 'observed-response')

        # An uncaught interruption after reservation has no terminal receipt; a new process still sees it used.
        crash_workspace = self.root / 'crash-workspace'
        crash_workspace.mkdir()
        ns = load_integration()
        ns['record_consent'](crash_workspace, 'yes', 'Owner', '2026-10-22')
        crash_scope = budget_scope('budget-process-crash-01')
        crash_env = dict(os.environ)
        crash_env.update({
            'T02_ROOT': str(ROOT), 'T02_WORKSPACE': str(crash_workspace),
            'T02_USE': 'evidence-signal', 'T02_POLICY': json.dumps(policy),
            'T02_SCOPE': json.dumps(crash_scope),
            'T02_SEND_LOG': str(self.root / 'crash-send.log'),
            'T02_CRASH_AFTER_RESERVATION': '1',
        })
        crashed = subprocess.run([sys.executable, '-I', '-c', _CHILD_BOOTSTRAP], cwd=ROOT, env=crash_env,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(crashed.returncode, 0, crashed.stdout)
        crash_directory = (crash_workspace / 'verification-records/T-ADVICE/judgment-budget'
                           / hashlib.sha256(crash_scope['identity'].encode()).hexdigest())
        self.assertTrue((crash_directory / 'evidence-signal.reservation.json').is_file())
        self.assertFalse((crash_directory / 'evidence-signal.terminal.json').exists())
        restarted = load_integration()
        after_crash_calls = []
        after_crash = restarted['system_one_use'](
            workspace=crash_workspace, configured=True, asked=[], use='evidence-signal',
            fragment='Public fixture context', local_judgment=local, sensitivity='public',
            decide=load_recipe(), client_factory=fake_factory('supports', before_construct=lambda kwargs: after_crash_calls.append(kwargs)),
            support_policy=policy, budget_scope=crash_scope)
        self.assertEqual(after_crash['source'], 'local')
        self.assertEqual(after_crash_calls, [])
        self.assertFalse(list(crash_workspace.rglob('*sidecar*')), 'budget survives without optional sidecar evidence')

        # A correctly shaped but mismatching scope and an unsafe symlink cannot create a client/send.
        for case in ('mismatch', 'symlink'):
            with self.subTest(case=case):
                workspace = self.root / case
                workspace.mkdir()
                self.ns['record_consent'](workspace, 'yes', 'Owner', '2026-10-22')
                scope = budget_scope('budget-invalid-' + case)
                digest = hashlib.sha256(scope['identity'].encode()).hexdigest()
                owner_root = workspace / 'verification-records/T-ADVICE'
                owner_root.mkdir(parents=True)
                budget_root = owner_root / 'judgment-budget'
                if case == 'mismatch':
                    scope_dir = budget_root / digest
                    scope_dir.mkdir(parents=True)
                    mismatched_scope = dict(scope_record(workspace, scope), contract_sha256='f' * 64)
                    (scope_dir / 'scope.json').write_bytes(canonical_bytes(mismatched_scope))
                else:
                    external = self.root / 'external-budget'
                    external.mkdir()
                    external_sentinel = external / 'public-sentinel.txt'
                    external_sentinel.write_bytes(b'outside owner bytes\n')
                    budget_root.symlink_to(external, target_is_directory=True)
                constructed = []
                result = self.ns['system_one_use'](
                    workspace=workspace, configured=True, asked=[], use='evidence-signal',
                    fragment='Public fixture context', local_judgment=local, sensitivity='public',
                    decide=self.decide, client_factory=fake_factory('supports', before_construct=lambda kwargs: constructed.append(kwargs)),
                    support_policy=policy, budget_scope=scope)
                self.assertEqual(result['source'], 'local')
                self.assertEqual(result['judgment'], local)
                self.assertEqual(constructed, [])
                if case == 'symlink':
                    self.assertEqual(external_sentinel.read_bytes(), b'outside owner bytes\n')

        # A reservation fsync failure is targeted to its own fd and prevents construction and request.
        failure_workspace = self.root / 'reservation-fsync-failure'
        failure_workspace.mkdir()
        self.ns['record_consent'](failure_workspace, 'yes', 'Owner', '2026-10-22')
        failure_scope = budget_scope('reservation-fsync-failure-01')
        failure_policy = evidence_policy()
        failure_reservation = budget_directory(failure_workspace, failure_scope) / 'evidence-signal.reservation.json'
        fsync_failures, failures_constructed, failures_sent = [], [], []

        def fail_target_fsync(fd):
            metadata = os.fstat(fd)
            try:
                target = failure_reservation.lstat()
            except OSError:
                target = None
            if (target is not None and stat.S_ISREG(target.st_mode)
                    and (metadata.st_dev, metadata.st_ino) == (target.st_dev, target.st_ino)):
                fsync_failures.append((metadata.st_dev, metadata.st_ino))
                raise OSError('fixture reservation fsync failure')
            return real_fsync(fd)

        failure_factory = fake_factory('supports',
                                       before_construct=lambda kwargs: failures_constructed.append(kwargs),
                                       on_send=lambda kwargs: failures_sent.append(kwargs))
        with patch.object(os, 'fsync', side_effect=fail_target_fsync):
            failed_persist = self.call('evidence-signal', failure_policy, failure_scope['identity'],
                                       workspace=failure_workspace, client_factory=failure_factory)
        self.assertEqual(failed_persist['source'], 'local')
        self.assertTrue(fsync_failures, 'fixture must target a real reservation fsync')
        self.assertEqual((failures_constructed, failures_sent), ([], []))

        # Terminal receipt failure after a real request consumes the existing slot after reload.
        terminal_workspace = self.root / 'terminal-write-failure'
        terminal_workspace.mkdir()
        self.ns['record_consent'](terminal_workspace, 'yes', 'Owner', '2026-10-22')
        terminal_scope = budget_scope('terminal-write-failure-01')
        terminal_policy = evidence_policy()
        terminal_path = budget_directory(terminal_workspace, terminal_scope) / 'evidence-signal.terminal.json'
        requests_after_terminal_failure, constructions_after_terminal_failure = [], []
        response = SimpleNamespace(model='jev-1.13.0', answers={'judgment': SimpleNamespace(
            type='choice', choice='supports', score='supports', confidence=0.9)})

        def conflicting_terminal_factory(**kwargs):
            constructions_after_terminal_failure.append(kwargs)
            terminal_path.mkdir()
            return SimpleNamespace(system_one=lambda **send_kwargs:
                                   (requests_after_terminal_failure.append(send_kwargs) or response),
                                   close=lambda: None)

        terminal_failure_result = self.call('evidence-signal', terminal_policy, terminal_scope['identity'],
                                            workspace=terminal_workspace,
                                            client_factory=conflicting_terminal_factory)
        self.assertEqual(terminal_failure_result['source'], 'local')
        self.assertEqual((len(constructions_after_terminal_failure), len(requests_after_terminal_failure)), (1, 1))
        terminal_directory = budget_directory(terminal_workspace, terminal_scope)
        self.assertTrue((terminal_directory / 'evidence-signal.reservation.json').is_file())
        reloaded_terminal = load_integration()
        no_repeat = []
        terminal_replay = reloaded_terminal['system_one_use'](
            workspace=terminal_workspace, configured=True, asked=[], use='evidence-signal',
            fragment='Public fixture context', local_judgment=local_for(terminal_policy), sensitivity='public',
            decide=load_recipe(), client_factory=fake_factory('supports',
                before_construct=lambda kwargs: no_repeat.append(('factory', kwargs)),
                on_send=lambda kwargs: no_repeat.append(('send', kwargs))),
            support_policy=terminal_policy, budget_scope=terminal_scope)
        self.assertEqual(terminal_replay['source'], 'local')
        self.assertEqual(no_repeat, [])

        # A truncated terminal remains unknown/consumed through another fresh module load.
        truncated_workspace = self.root / 'truncated-terminal'
        truncated_workspace.mkdir()
        self.ns['record_consent'](truncated_workspace, 'yes', 'Owner', '2026-10-22')
        truncated_scope = budget_scope('truncated-terminal-01')
        truncated_policy = evidence_policy()
        truncated_directory = budget_directory(truncated_workspace, truncated_scope)
        truncated_directory.mkdir(parents=True)
        (truncated_directory / 'scope.json').write_bytes(canonical_bytes(scope_record(truncated_workspace, truncated_scope)))
        (truncated_directory / 'evidence-signal.reservation.json').write_bytes(
            canonical_bytes(reservation_record(truncated_workspace, truncated_scope, 'evidence-signal', truncated_policy)))
        (truncated_directory / 'evidence-signal.terminal.json').write_bytes(b'{"status":')
        truncated_factory_calls, truncated_sends = [], []
        for reload_index in range(2):
            reloaded = load_integration()
            blocked = reloaded['system_one_use'](
                workspace=truncated_workspace, configured=True, asked=[], use='evidence-signal',
                fragment='Public fixture context', local_judgment=local_for(truncated_policy), sensitivity='public',
                decide=load_recipe(), client_factory=fake_factory('supports',
                    before_construct=lambda kwargs: truncated_factory_calls.append((reload_index, kwargs)),
                    on_send=lambda kwargs: truncated_sends.append((reload_index, kwargs))),
                support_policy=truncated_policy, budget_scope=truncated_scope)
            self.assertEqual(blocked['source'], 'local')
        self.assertEqual((truncated_factory_calls, truncated_sends), ([], []))

    def test_concurrent_same_use_reserves_at_most_once(self):
        self.answer('yes')
        identity = 'budget-concurrent-same-use-01'
        scope = budget_scope(identity)
        policy = bounded_policy()
        send_log = self.root / 'sends.log'
        factory_log = self.root / 'factories.log'
        environment = dict(os.environ)
        environment.update({
            'T02_ROOT': str(ROOT), 'T02_WORKSPACE': str(self.workspace),
            'T02_USE': 'bounded-recovery', 'T02_POLICY': json.dumps(policy),
            'T02_SCOPE': json.dumps(scope), 'T02_SEND_LOG': str(send_log),
            'T02_FACTORY_LOG': str(factory_log),
        })
        children = [subprocess.Popen([sys.executable, '-I', '-c', _CHILD_BOOTSTRAP], cwd=ROOT, env=environment,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        observations = [child.communicate(timeout=30) + (child.returncode,) for child in children]
        for stdout, stderr, returncode in observations:
            self.assertEqual(returncode, 0, (stdout, stderr))
            self.assertTrue(stdout.strip())
        if self.sdk_absent():
            for stdout, stderr, returncode in observations:
                absent = json.loads(stdout)
                self.assertEqual((absent['source'], absent['reason']), ('local', 'sdk-unavailable'))
            self.assertFalse(send_log.exists() or factory_log.exists())
            return
        self.assertEqual(send_log.read_text(encoding='utf-8').splitlines(), ['bounded-recovery'])
        self.assertEqual(factory_log.read_text(encoding='utf-8').splitlines(), ['bounded-recovery'])

        # The second independent use consumes the other exclusive slot; neither use can be repeated.
        self.ns = load_integration()
        self.answer('yes')
        evidence = evidence_policy()
        parent_requests = []
        extra = self.call('evidence-signal', evidence, identity,
                          client_factory=fake_factory('supports', on_send=lambda kwargs: parent_requests.append(kwargs)))
        self.assertEqual(extra['source'], 'jev', extra)
        again_recovery = self.call('bounded-recovery', policy, identity,
                                   client_factory=fake_factory('retry-after-correction',
                                       on_send=lambda kwargs: parent_requests.append(kwargs)))
        again_evidence = self.call('evidence-signal', evidence, identity,
                                   client_factory=fake_factory('supports',
                                       on_send=lambda kwargs: parent_requests.append(kwargs)))
        self.assertEqual(again_recovery['source'], 'local')
        self.assertEqual(again_evidence['source'], 'local')
        self.assertEqual(len(parent_requests), 1, 'second use sends once; repeated uses send nothing')
        self.assertLessEqual(len(send_log.read_text(encoding='utf-8').splitlines()) + len(parent_requests), 2)
        self.assertEqual(send_log.read_text(encoding='utf-8').splitlines(), ['bounded-recovery'])
        budget_dir = (self.workspace / 'verification-records/T-ADVICE/judgment-budget'
                      / hashlib.sha256(identity.encode()).hexdigest())
        self.assertTrue((budget_dir / 'bounded-recovery.reservation.json').is_file())
        self.assertTrue((budget_dir / 'evidence-signal.reservation.json').is_file())

    def test_advice_preserves_task_authority_and_original_policies(self):
        old_decide = load_recipe()
        old_responses = {
            'resume-selection': (1.0, 0.2, 0.6),
            'failure-class': ('implementation', 'environment', 0.8),
            'no-progress': (False, True, 0.8),
            'intake-size': ('Focused', 'Direct', 0.8),
        }
        for use in OLD_USES:
            local, judgment, confidence = old_responses[use]
            with self.subTest(original_use=use):
                result = old_decide(state(), use, 'Public original-use fixture', local,
                                    lambda request, judgment=judgment, confidence=confidence: {
                                        'model': 'jev-1.13.0', 'confidence': confidence, 'judgment': judgment})
                self.assertEqual(set(result), RESULT_KEYS)
                self.assertEqual(result['source'], 'jev')
                self.assertEqual(result['judgment'], judgment)

        self.answer('yes')
        policy = bounded_policy()
        attempted = []
        if self.sdk_absent():
            absent = self.call('evidence-signal', evidence_policy(), 'authority-evidence-01',
                               client_factory=fake_factory('supports', confidence=0.99,
                                                           before_construct=lambda kwargs: attempted.append(kwargs)))
            self.assertEqual((absent['source'], absent['reason']), ('local', 'sdk-unavailable'))
            self.assertEqual(attempted, [])
            no_policy = self.ns['system_one_use'](
                workspace=self.workspace, configured=True, asked=[], use='bounded-recovery',
                fragment='Public fixture context', local_judgment={'choice': 'defer', 'confidence': None},
                sensitivity='public', decide=self.decide,
                client_factory=fake_factory('retry-after-correction', before_construct=lambda kwargs: attempted.append(kwargs)))
            self.assertEqual(no_policy['source'], 'local')
            self.assertEqual(attempted, [])
            return
        # A high-confidence but ineligible recommendation falls back exactly to the planner's local value.
        ineligible = self.call('bounded-recovery', policy, 'authority-ineligible-01',
                               client_factory=fake_factory('rerun-read-only', confidence=0.99,
                                                           before_construct=lambda kwargs: attempted.append(kwargs)))
        self.assertEqual(ineligible['source'], 'local')
        self.assertEqual(ineligible['judgment'], local_for(policy))
        self.assertNotIn('acceptance', ineligible)

        # Evidence is only advisory beside a failed mandatory check; no task or lineage file is an acceptance target.
        mandatory = self.workspace / 'mandatory-check.json'
        lineage = self.workspace / 'correction-lineage.json'
        mandatory.write_text('{"status":"failed"}\n', encoding='utf-8')
        lineage.write_text('{"cycles_spent":1}\n', encoding='utf-8')
        before = (mandatory.read_bytes(), lineage.read_bytes())
        evidence = evidence_policy()
        advice = self.call('evidence-signal', evidence, 'authority-evidence-01',
                           client_factory=fake_factory('supports', confidence=0.99))
        self.assertEqual(advice['source'], 'jev', advice)
        self.assertEqual(advice['judgment']['choice'], 'supports')
        self.assertEqual(set(advice), RESULT_KEYS)
        self.assertEqual((mandatory.read_bytes(), lineage.read_bytes()), before)
        self.assertFalse((self.workspace / 'acceptance.json').exists())

        # Without an explicit compiled extension policy, the new optional use stays local and sends nothing.
        no_policy_calls = []
        result = self.ns['system_one_use'](
            workspace=self.workspace, configured=True, asked=[], use='bounded-recovery',
            fragment='Public fixture context', local_judgment={'choice': 'defer', 'confidence': None},
            sensitivity='public', decide=self.decide,
            client_factory=fake_factory('retry-after-correction', before_construct=lambda kwargs: no_policy_calls.append(kwargs)))
        self.assertEqual(result['source'], 'local')
        self.assertEqual(no_policy_calls, [])
