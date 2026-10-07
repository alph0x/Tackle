"""I1-I8: extracted integration consumers, concrete faults and valid neighbors.

Detection/consent fixtures exercise real shell/files; SDK present uses the official
serializer with fictitious auth/MockTransport. Absent SDK exercises the local
fallback. The scoped recorded acceptance requires SDK present; this is not live evidence.
History/route faults target actual consumers, never a copied decision algorithm.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from test_system_one_functional import load_recipe

ROOT = Path(__file__).resolve().parents[4]
RECIPE = ROOT / 'skills/tackle/references/recipes/system-one.md'
CLASSES = {'implementation', 'missing or ambiguous requirement', 'incomplete output',
           'required edge case', 'dependency or integration', 'contradictory spec',
           'validator', 'environment', 'capability', 'undetermined'}


def block(anchor, language):
    text = RECIPE.read_text()
    marker = f'<a id="{anchor}"></a>\n```{language}\n'
    assert text.count(marker) == 1
    return text.split(marker)[1].split('\n```')[0]


def load_integration(source=None):
    text = block('system-one-integration', 'py') if source is None else source
    ns = {'__name__': 'system_one_integration'}
    exec(compile(text, str(RECIPE), 'exec'), ns)
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

    def detect(self, setup=None):
        project = self.root / 'project'
        project.mkdir(exist_ok=True)
        home = self.root / 'home'
        home.mkdir(exist_ok=True)
        bindir = self.root / 'bin'
        bindir.mkdir(exist_ok=True)
        python = bindir / 'python3'
        python.write_text('#!/bin/sh\nexec '+str(Path(sys.executable))+' -S "$@"\n')
        python.chmod(0o755)
        env = {'PATH': str(bindir)+':/usr/bin:/bin', 'HOME': str(home), 'PYTHONPATH': ''}
        if setup:
            setup(project, home, env)
        p = subprocess.run(['/bin/sh', '-c', block('system-one-detection', 'sh'),
                            'system-one', str(self.workspace)], cwd=project,
                           env=env, capture_output=True, timeout=5)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stderr, b'')
        self.assertRegex(p.stdout.decode(), r'^system-one: (?:none|detected [a-z,]+)\n$')
        return p.stdout.decode()

    def test_detection_presence_and_all_four_signals(self):
        self.assertEqual(self.detect(), 'system-one: none\n')
        for value in ['', 'fictitious-credential-never-print']:
            with self.subTest(environment=value):
                out = self.detect(lambda p,h,e: e.update({'TYPESAFE_API_KEY':value}))
                self.assertIn('environment', out)
                self.assertNotIn('fictitious-credential', out)
        with self.subTest(skill=True):
            self.assertIn('skill', self.detect(lambda p,h,e: (h/'.agents/skills/typesafe-ai').mkdir(parents=True)))
        with self.subTest(SDK=True):
            sdk = self.root/'fake-sdk/typesafe_sdk'
            sdk.mkdir(parents=True)
            (sdk/'__init__.py').write_text('raise RuntimeError("must not import SDK")')
            self.assertIn('sdk', self.detect(lambda p,h,e: e.update(PYTHONPATH=str(sdk.parent))))
        for name in ['AGENTS.md', 'CLAUDE.md']:
            for phrase in ['TypeSafe System One', 'tYpEsAfE sYsTeM oNe']:
                with self.subTest(file=name, phrase=phrase):
                    self.assertIn('instructions', self.detect(lambda p,h,e: (p/name).write_text(phrase)))
                    (self.root/'project'/name).unlink()
        (self.workspace/'AGENTS.md').write_text('TypeSafe System One')
        self.assertIn('instructions', self.detect())

    def test_detection_refuses_nonregular_partial_and_other_inputs(self):
        for phrase in ['TypeSafe', 'System One', 'TypeSafe System Ones', 'OtherSystem One']:
            with self.subTest(phrase=phrase):
                self.assertEqual(self.detect(lambda p,h,e: (p/'AGENTS.md').write_text(phrase)), 'system-one: none\n')
        (self.root/'project/AGENTS.md').unlink()
        self.assertEqual(self.detect(lambda p,h,e: (p/'.env').write_text('TYPESAFE_API_KEY' + '=' + 'fictitious')), 'system-one: none\n')
        outside = self.root/'outside'
        outside.write_text('TypeSafe System One')
        (self.root/'project/AGENTS.md').symlink_to(outside)
        self.assertEqual(self.detect(), 'system-one: none\n')
        (self.root/'project/AGENTS.md').unlink()
        os.mkfifo(self.root/'project/CLAUDE.md')
        self.assertEqual(self.detect(), 'system-one: none\n')
        source = block('system-one-detection','sh')
        self.assertNotRegex(source, r'(?i)curl|wget|requests|\.env|printenv|echo.*TYPESAFE_API_KEY')

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

    def test_official_sdk_wire_for_all_four_uses(self):
        if importlib.util.find_spec('typesafe_sdk') is None:
            self.assertNotEqual(os.environ.get('TACKLE_TYPESAFE_SDK_REQUIRED'), '1', 'Scoped acceptance requires official SDK')
            self.answer()
            self.assertEqual(self.call()['reason'],'sdk-unavailable')
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
                self.assertEqual(options[0]['base_url'],'https://api.typesafe.ai')
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

    def test_real_sdk_error_one_attempt_and_default_certificate_verification(self):
        if importlib.util.find_spec('typesafe_sdk') is None:return
        import httpx2
        from typesafe_sdk import TypeSafeClient
        self.answer();seen=[]
        def handle(request):seen.append(request);return httpx2.Response(503,json={'error':'unavailable'})
        def factory(**kwargs):return TypeSafeClient(api_key='fictitious-test-key',transport=httpx2.MockTransport(handle),**kwargs)
        self.assertEqual(self.call(client_factory=factory)['source'],'local')
        self.assertEqual(len(seen),1)
        with patch.dict(os.environ, {'TYPESAFE_API_KEY':'fictitious-test-key'},clear=True):
            client=self.ns['make_client']()
            try:
                context=client._http_client._transport._pool._ssl_context
                self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
                self.assertTrue(context.check_hostname)
            finally:client.close()

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
        source=block('system-one-integration','py')
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

    def test_actual_source_hooks_network_exception_and_artifact(self):
        entry=(ROOT/'skills/tackle/SKILL.md').read_text()
        self.assertLessEqual(len(entry.split()),1100)
        self.assertEqual(len(re.findall(r'^\d+\. \*\*',entry,re.M)),11)
        for file in ['status','run','intake-and-gate','migrate']:
            self.assertIn('system-one.md',(ROOT/f'skills/tackle/references/guides/{file}.md').read_text())
        ledger=json.loads((ROOT/'eval/rules/ledger.json').read_text())
        rel=next(r for r in ledger['rules'] if r['rule_id']=='R-REL-01')
        def consent_exception(statement):
            return statement.startswith('Ordinary invocation performs no network access or') and 'consented System One call' in statement and 'installation mutation' in statement
        self.assertTrue(consent_exception(rel['statement']))
        self.assertFalse(consent_exception(rel['statement'].replace('consented System One call','configured System One call')))
        self.assertIn('consented System One call',entry)
        self.assertEqual(rel['class'],'safety-invariant');self.assertTrue(rel['hot_path'])
        self.assertIn('SDK handles authentication',RECIPE.read_text())
        self.assertNotRegex(block('system-one-integration','py'),r'(?:verify\s*=\s*False|os\.environ|\.env|print\(|logging\.)')


if __name__=='__main__':unittest.main()
