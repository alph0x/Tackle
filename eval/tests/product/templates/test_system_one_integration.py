"""I1-I8: the shipped state script, scripts/system_one_state.py, its concrete faults and valid neighbors.

Consent fixtures exercise real files; SDK present uses the official serializer with fictitious
auth/MockTransport through a caller-built client factory. Absent SDK or absent factory exercises the
local fallback. The scoped recorded acceptance requires SDK present; this is not live evidence.
History/route faults target actual consumers, never a copied decision algorithm. The configuration
signal is a presence check the agent performs under the guide; no detection program ships.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from test_system_one_functional import load_recipe

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / 'skills/tackle/scripts/system_one_state.py'
GUIDE = ROOT / 'skills/tackle/references/guides/system-one.md'
CLASSES = {'implementation', 'missing or ambiguous requirement', 'incomplete output',
           'required edge case', 'dependency or integration', 'contradictory spec',
           'validator', 'environment', 'capability', 'undetermined'}


def script_source():
    return SCRIPT.read_text()


def load_integration(source=None):
    if source is None:
        spec = importlib.util.spec_from_file_location('system_one_state', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return vars(module)
    ns = {'__name__': 'system_one_integration'}
    exec(compile(source, str(SCRIPT), 'exec'), ns)
    return ns


class SystemOneIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        self.ns = load_integration()
        self.decide = load_recipe()

    def answer(self, value='yes'):
        return self.ns['record_consent'](self.workspace, value, 'Owner', '2026-10-06')

    def call(self, use='failure-class', local='implementation', **kwargs):
        args = dict(workspace=self.workspace, configured=True, asked=[], use=use,
                    fragment='Public fixture context', local_judgment=local,
                    sensitivity='public', decide=self.decide)
        args.update(kwargs)
        return self.ns['system_one_use'](**args)

    def factory(self, model='jev-1.13.0', confidence=0.8, judgment='implementation', answer_type='choice'):
        self.constructed = []
        self.sent = []
        answer = SimpleNamespace(type=answer_type, choice=judgment, score=judgment,
                                 confidence=confidence)
        def send(**kwargs):
            self.sent.append(kwargs)
            return SimpleNamespace(model=model, answers={'judgment': answer})
        def factory(**kwargs):
            self.constructed.append(kwargs)
            return SimpleNamespace(system_one=send, close=lambda: None)
        return factory

    def test_configuration_signal_is_presence_only_without_a_home_probe(self):
        guide=' '.join(GUIDE.read_text().split())
        self.assertIn('A configuration signal is the host offering the `typesafe-ai` skill, the presence of the '
                      '`TYPESAFE_API_KEY` environment variable, or the case-insensitive phrase `TypeSafe System One` '
                      'in project-root AGENTS/CLAUDE or selected-workspace AGENTS. Check presence only and probe no home folder.',guide)
        self.assertIn('A configuration signal cannot grant consent.',guide)
        self.assertNotRegex(script_source(),r'(?:os\.environ|getenv|Path\.home|expanduser|HOME|TYPESAFE_API_KEY)')

    def test_consent_real_readback_metadata_and_idempotence(self):
        original = '# workspace\nOwner content\n'
        (self.workspace/'AGENTS.md').write_text(original)
        for value in ['yes','no']:
            with self.subTest(answer=value):
                (self.workspace/'AGENTS.md').write_text(original)
                meta = self.answer(value)
                content = (self.workspace/'AGENTS.md').read_bytes()
                self.assertTrue(content.startswith(original.encode()))
                self.assertEqual(self.answer(value), meta)
                self.assertEqual(content, (self.workspace/'AGENTS.md').read_bytes())
                fresh = load_integration()
                state, seen = fresh['load_state'](self.workspace, True, [])
                self.assertEqual(state['consent'], {'workspace': str(self.workspace.resolve()), 'answer': value})
                self.assertEqual(seen, {'answer': value, 'date': '2026-10-06', 'actor': 'Owner'})
                self.assertEqual(meta, seen)

    def test_consent_conflicts_malformed_and_neighbor_workspace(self):
        self.answer()
        content = (self.workspace/'AGENTS.md').read_bytes()
        with self.assertRaises(ValueError): self.answer('no')
        self.assertEqual((self.workspace/'AGENTS.md').read_bytes(), content)
        other = self.root/'other'
        other.mkdir()
        state, meta = self.ns['load_state'](other, True, [])
        self.assertIsNone(state['consent']);self.assertIsNone(meta)
        for text in ['System One consent: yes\n',
                     'System One consent: maybe · date=2026-10-06 · actor="Owner"\n',
                     'System One consent: yes · date=2026-99-01 · actor="Owner"\n',
                     content.decode()+content.decode()]:
            with self.subTest(malformed=text):
                (self.workspace/'AGENTS.md').write_text(text)
                with self.assertRaises(ValueError): self.ns['load_state'](self.workspace, True, [])
                with self.assertRaises(ValueError): self.answer()
        (self.workspace/'AGENTS.md').unlink()
        (self.workspace/'AGENTS.md').symlink_to(other/'AGENTS.md')
        with self.assertRaises(ValueError): self.answer()
        (self.workspace/'AGENTS.md').unlink()
        os.mkfifo(self.workspace/'AGENTS.md')
        with self.assertRaises(ValueError): self.answer()

    def test_one_pending_question_and_readonly_status(self):
        prepare = self.ns['prepare_consent']
        before = list(self.workspace.iterdir())
        out = prepare(self.workspace, True, [], 'STATUS', self.decide)
        self.assertIsNone(out['question']);self.assertEqual(list(self.workspace.iterdir()), before)
        (self.workspace/'questions.md').write_text('# Questions\nUnrelated open question\n')
        out = prepare(self.workspace, True, [], 'RUN', self.decide)
        self.assertIsNotNone(out['question'])
        pending = (self.workspace/'questions.md').read_bytes()
        self.assertIn(b'Unrelated open question', pending)
        for asked in [out['state']['asked'], []]:
            second = prepare(self.workspace, True, asked, 'PLAN', self.decide)
            self.assertIsNone(second['question'])
            self.assertEqual((self.workspace/'questions.md').read_bytes(), pending)
        self.answer('no')
        self.assertNotIn('[system-one-consent]', (self.workspace/'questions.md').read_text())
        self.assertIn('Unrelated open question', (self.workspace/'questions.md').read_text())
        self.assertIsNone(prepare(self.workspace, True, [], 'RUN', self.decide)['question'])
        (self.workspace/'AGENTS.md').write_text('System One consent: malformed\n')
        for mode in ['STATUS','RUN','PLAN']:
            self.assertEqual(prepare(self.workspace,True,[],mode,self.decide)['reason'],'malformed-consent')
        broken=self.root/'broken-consent'
        broken.mkdir()
        (broken/'AGENTS.md').write_text('System One consent: malformed\n')
        suppressed=prepare(broken,True,[],'STATUS',self.decide)
        self.assertIsNone(suppressed['question'])
        self.assertEqual(suppressed['state']['asked'],[], 'A suppressed prompt was never asked')
        (broken/'AGENTS.md').write_text('# Repaired unanswered workspace\n')
        first=prepare(broken,True,suppressed['state']['asked'],'RUN',self.decide)
        self.assertIsNotNone(first['question'])
        self.assertIn('[system-one-consent]',(broken/'questions.md').read_text())

    def test_no_consent_or_public_admission_no_construction_or_send(self):
        factory = self.factory()
        self.assertEqual(self.call(client_factory=factory)['reason'], 'consent-unanswered')
        self.assertEqual(self.constructed, [])
        self.answer('no')
        self.assertEqual(self.call(client_factory=factory)['reason'], 'consent-no')
        self.assertEqual(self.constructed, [])
        (self.workspace/'AGENTS.md').unlink();self.answer()
        for sensitivity in ['private','secret','sealed','answer-sheet','unknown',None]:
            with self.subTest(sensitivity=sensitivity):
                self.assertEqual(self.call(sensitivity=sensitivity, client_factory=factory)['reason'], 'fragment-not-public')
                self.assertEqual(self.constructed, [])
        self.assertEqual(self.call(configured=False, client_factory=factory)['reason'],'not-configured')
        self.assertEqual(self.constructed, [])
        if importlib.util.find_spec('typesafe_sdk'):
            self.assertEqual(self.call(client_factory=factory)['source'], 'jev')
            self.assertEqual(len(self.constructed),1);self.assertEqual(len(self.sent),1)

    def test_no_client_factory_stays_local_without_import_or_send(self):
        self.answer()
        with patch.dict(sys.modules, {'typesafe_sdk': None}):
            out = self.call()
        self.assertEqual(out['source'], 'local')
        self.assertEqual(out['judgment'], 'implementation')
        self.assertEqual(out['reason'], 'client-unavailable', 'an import attempt would report sdk-unavailable')
        self.assertIsNone(out['model'])
        factory = self.factory()
        with patch.dict(sys.modules, {'typesafe_sdk': None}):
            self.assertEqual(self.call(client_factory=factory)['reason'], 'sdk-unavailable')
        self.assertEqual(self.constructed, [])
        self.assertNotIn('make_client', self.ns)

    def test_official_sdk_wire_for_all_four_uses(self):
        if importlib.util.find_spec('typesafe_sdk') is None:
            self.assertNotEqual(os.environ.get('TACKLE_TYPESAFE_SDK_REQUIRED'), '1', 'Scoped acceptance requires official SDK')
            self.answer()
            self.assertEqual(self.call(client_factory=self.factory())['reason'],'sdk-unavailable')
            return
        import httpx2
        from typesafe_sdk import TypeSafeClient
        self.answer()
        for use,local,judgment,kind,confidence in [
            ('resume-selection',1.0,0.2,'score',0.6),
            ('failure-class','implementation','environment','choice',0.8),
            ('no-progress',False,'same','choice',0.8),
            ('intake-size','Focused','Direct','choice',0.8)]:
            with self.subTest(use=use):
                seen=[];options=[]
                def handle(request):
                    seen.append(request)
                    answer={'type':kind,'confidence':confidence}
                    if kind=='score':answer.update(score=judgment,legend={'0':'irrelevant','1':'needed'},probabilities={'0':0.8,'1':0.2})
                    else:answer.update(choice=judgment,probabilities={judgment:1.0})
                    return httpx2.Response(200,json={'model':'jev-1.13.0','usage':{'input_tokens':1,'output_tokens':1},'answers':{'judgment':answer}})
                def factory(**kwargs):
                    options.append(kwargs)
                    return TypeSafeClient(api_key='fictitious-test-key',transport=httpx2.MockTransport(handle),**kwargs)
                out=self.call(use=use,local=local,client_factory=factory)
                self.assertEqual(out['source'],'jev',out)
                self.assertEqual(out['judgment'],True if use=='no-progress' else judgment)
                self.assertEqual(out['confidence'],confidence)
                self.assertEqual(out['model'],'jev-1.13.0')
                self.assertEqual(len(seen),1)
                request=seen[0];wire=json.loads(request.content)
                self.assertEqual(str(request.url),'https://api.typesafe.ai/v1/systemone')
                self.assertEqual(request.method,'POST')
                self.assertEqual(request.headers['authorization'],'Bearer fictitious-test-key')
                self.assertEqual(set(wire),{'model','state','questions'})
                self.assertEqual(wire['model'],'jev-1.13.0')
                self.assertEqual(wire['state'],{'fragment':'Public fixture context'})
                self.assertEqual(wire['questions']['judgment']['type'],kind)
                if use=='failure-class': self.assertEqual(set(wire['questions']['judgment']['criteria']),CLASSES)
                self.assertEqual(options[0]['retry'].max_retries,0)
                self.assertEqual(options[0]['timeout'],10.0)
                self.assertEqual(set(options[0]),{'model','timeout','retry'})
                print('SYSTEM_ONE_MOCK_CAPTURE='+json.dumps({'use':use,'method':request.method,
                    'url':str(request.url),'body':wire,'response':{'model':out['model'],
                    'judgment':out['judgment'],'confidence':out['confidence']},
                    'auth':'actual Bearer fictitious-test-key asserted; no real credentials',
                    'retry':options[0]['retry'].max_retries,'timeout':options[0]['timeout']}))

    def test_adapter_domains_model_confidence_errors_and_boundaries(self):
        if importlib.util.find_spec('typesafe_sdk') is None: return
        self.answer()
        for change,reason in [({'model':'other'},'wrong-model'),({'confidence':0.799},'low-confidence'),
                             ({'confidence':True},'transport-failure'),({'confidence':float('nan')},'transport-failure'),
                             ({'judgment':'blame-owner'},'transport-failure'),({'answer_type':'noul'},'transport-failure')]:
            with self.subTest(change=change):
                factory=self.factory(**change)
                out=self.call(client_factory=factory)
                self.assertEqual(out['source'],'local');self.assertEqual(out['judgment'],'implementation')
                self.assertEqual(out['reason'],reason)
                self.assertEqual(len(self.sent),1)
        def fail(**kwargs): raise OSError('fictitious unavailable transport')
        self.assertEqual(self.call(client_factory=fail)['reason'],'transport-failure')
        for fatal in [KeyboardInterrupt,SystemExit]:
            def abort(**kwargs):raise fatal()
            with self.assertRaises(fatal):self.call(client_factory=abort)
            def send_abort(**kwargs):raise fatal()
            def close_failure():raise OSError('fictitious cleanup failure')
            def factory_cleanup(**kwargs):return SimpleNamespace(system_one=send_abort,close=close_failure)
            with self.assertRaises(fatal):self.call(client_factory=factory_cleanup)
        for use,local,judgment,kind,conf in [('resume-selection',1.0,0.2,'score',0.6),('no-progress',False,'different','choice',0.8),('intake-size','Focused','Direct','choice',0.8)]:
            out=self.call(use=use,local=local,client_factory=self.factory(judgment=judgment,answer_type=kind,confidence=conf))
            self.assertEqual(out['source'],'jev',out)

    def test_real_sdk_error_one_attempt(self):
        if importlib.util.find_spec('typesafe_sdk') is None:return
        import httpx2
        from typesafe_sdk import TypeSafeClient
        self.answer();seen=[]
        def handle(request):seen.append(request);return httpx2.Response(503,json={'error':'unavailable'})
        def factory(**kwargs):return TypeSafeClient(api_key='fictitious-test-key',transport=httpx2.MockTransport(handle),**kwargs)
        self.assertEqual(self.call(client_factory=factory)['source'],'local')
        self.assertEqual(len(seen),1)

    def test_history_retains_protected_entries_and_rejects_outside_bound(self):
        entries=[{'id':'spent','fragment':'public count','sensitivity':'public','spent_count':1,'open_obligations':[]},
                 {'id':'open','fragment':'public obligation','sensitivity':'public','spent_count':0,'open_obligations':['O-01']},
                 {'id':'irrelevant','fragment':'old unrelated public context','sensitivity':'public','spent_count':0,'open_obligations':[]}]
        signals=[]
        def score(entry):signals.append(entry['id']);return {'judgment':0.2,'source':'jev','model':'jev-1.13.0','confidence':0.6}
        select=self.ns['select_history']
        kept=select(entries,set(e['id'] for e in entries),score)
        self.assertEqual([e['id'] for e in kept],['spent','open'])
        self.assertEqual(signals,['irrelevant'])
        signals.clear()
        with self.assertRaises(ValueError):select(entries,{'spent','open'},score)
        self.assertEqual(signals,[])
        for source,confidence,model in [('local',0.6,'jev-1.13.0'),('jev',0.59,'jev-1.13.0'),('jev',0.6,'other')]:
            self.assertEqual(select(entries,{'spent','open','irrelevant'},lambda e:dict(judgment=0.2,source=source,model=model,confidence=confidence)),entries)
        self.assertEqual(select(entries,{'spent','open','irrelevant'},lambda e:dict(judgment=0.5,source='jev',model='jev-1.13.0',confidence=0.6)),entries)

    def test_history_fault_oracle_and_valid_alternative(self):
        source=script_source()
        self.assertIn('entry["spent_count"] > 0 or entry["open_obligations"]',source)
        mutant=source.replace('entry["spent_count"] > 0 or entry["open_obligations"]','False',1)
        entry={'id':'spent','fragment':'public count','sensitivity':'public','spent_count':1,'open_obligations':[]}
        score=lambda e:dict(judgment=0.2,source='jev',model='jev-1.13.0',confidence=0.6)
        def retention_oracle(consumer):
            self.assertEqual(consumer([entry],{'spent'},score),[entry])
        retention_oracle(self.ns['select_history'])
        with self.assertRaises(AssertionError):
            retention_oracle(load_integration(mutant)['select_history'])

    def test_route_and_no_progress_consumers_preserve_mandatory_precedence(self):
        route=self.ns['intake_route']
        signal={'judgment':'Direct','source':'jev','reason':'accepted','model':'jev-1.13.0','confidence':0.8}
        for flags in [(2,False,False,False),(1,True,False,False),(1,False,True,False),(1,False,False,True)]:
            self.assertEqual(route('Focused',signal,*flags),'Coordinated')
        self.assertEqual(route('Coordinated',signal,1,False,False,False),'Coordinated',
                         'High uncertainty/multiple tracks can require Full without the four flags')
        self.assertEqual(route('Focused',signal,1,False,False,False),'Focused',
                         'Security-sensitive scope is not eligible for Direct')
        self.assertEqual(route('Direct',signal,1,False,False,False),'Direct')
        self.assertEqual(route('Direct',dict(signal,judgment='Focused'),1,False,False,False),'Focused')
        self.assertEqual(route('Focused',{'judgment':'Direct','source':'local'},1,False,False,False),'Focused')
        self.assertTrue(self.ns['no_progress_same'](True,dict(signal,judgment=False)))
        self.assertTrue(self.ns['no_progress_same'](False,dict(signal,judgment=True)))
        self.assertFalse(self.ns['no_progress_same'](False,{'judgment':True,'source':'local'}))
        for patch_value in [{'confidence':0.79},{'confidence':True},{'model':'other'},{'reason':'malformed-response'}]:
            invalid=dict(signal,**patch_value)
            self.assertEqual(route('Focused',invalid,1,False,False,False),'Focused')
            self.assertFalse(self.ns['no_progress_same'](False,dict(invalid,judgment=True)))

    def test_intake_checks_for_a_signal_on_every_route_before_sizing(self):
        intake=' '.join((ROOT/'skills/tackle/references/guides/intake-and-gate.md').read_text().split())
        section=intake.split('## System One check (every route)',1)[1].split(' ## ',1)[0]
        for phrase in ['Before sizing, check once per workspace for a System One configuration signal',
                       'check presence only',
                       'When there is a signal, a selected workspace and no recorded answer, ask the System One question in PLAN or RUN, then record it.',
                       'ask right after the scaffold creates it.',
                       'in the exact form that [the state script](../../scripts/system_one_state.py) reads:',
                       '`System One consent: yes · date=YYYY-MM-DD · actor="name"`, with `no` for a refusal.',
                       'Without a signal, record nothing and continue.']:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase,section)
        self.assertLess(intake.index('## System One check (every route)'),intake.index('# Step 2'))
        card=(ROOT/'skills/tackle/references/guides/plan-card.md').read_text()
        self.assertIn('[System One check](intake-and-gate.md#system-one-check)',card)
        run=' '.join((ROOT/'skills/tackle/references/guides/run.md').read_text().split())
        self.assertIn('gets the [System One check](intake-and-gate.md#system-one-check) when RUN starts.',run)

    def test_each_call_and_fallback_becomes_one_sidecar_record(self):
        guide=' '.join((ROOT/'skills/tackle/references/guides/system-one.md').read_text().split())
        for phrase in ['After a configuration signal, record each call and each local fallback as one [sidecar](usage-observability.md) record',
                       '`collector: system-one`',"Use `scope: role` and the calling role's Run ID as `run_id`",
                       'without a Run ID, use `scope: session` and `run_id: n/a`',
                       'A Direct request has no workspace and writes no record.',
                       '`requests` is 1 when a request was sent and 0 when the fallback came before any send.',
                       'when the response reports them, token counts','adopted decision or fallback reason',
                       'With a recorded `yes`, consult System One at every point where one of the four uses applies:',
                       'each failure classification, each no-progress comparison, each cold-resume history choice and each intake sizing.',
                       'Each consult keeps the thresholds and fallbacks above.',
                       'A point with no admitted public fragment is a skipped point.',
                       'Record a skipped point with its reason.',
                       'Read-only STATUS makes no call and writes no record.',
                       'A missing sidecar or a failed record write never fails the task.']:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase,guide)

    def test_actual_source_hooks_no_network_rule_and_artifact(self):
        entry=(ROOT/'skills/tackle/SKILL.md').read_text()
        self.assertLessEqual(len(entry.split()),1100)
        self.assertEqual(len(re.findall(r'^\d+\. \*\*',entry,re.M)),11)
        for file in ['status','run','intake-and-gate','migrate']:
            self.assertIn('system-one.md',(ROOT/f'skills/tackle/references/guides/{file}.md').read_text())
        ledger=json.loads((ROOT/'eval/rules/ledger.json').read_text())
        rel=next(r for r in ledger['rules'] if r['rule_id']=='R-REL-01')
        def no_network_rule(statement):
            return (statement.startswith('Ordinary invocation performs no network access or') and 'installation mutation' in statement
                    and "goes through the host's `typesafe-ai` skill" in statement and "only with the workspace's recorded consent" in statement
                    and 'exception' not in statement)
        self.assertTrue(no_network_rule(rel['statement']))
        self.assertFalse(no_network_rule(rel['statement'].replace("only with the workspace's recorded consent",'when configured')))
        self.assertFalse(no_network_rule(rel['statement'] + ' The only exception is network access by Tackle.'))
        self.assertIn(rel['statement'],' '.join(entry.split()))
        self.assertNotIn('only exception is network access',entry)
        self.assertEqual(rel['class'],'safety-invariant');self.assertTrue(rel['hot_path'])
        self.assertIn('SDK handles authentication',GUIDE.read_text())
        self.assertNotRegex(script_source(),r'(?:verify\s*=\s*False|os\.environ|\.env|print\(|logging\.|base_url|api\.typesafe)')


if __name__=='__main__':unittest.main()
