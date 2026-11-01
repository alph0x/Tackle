"""Offline public-interface checks using a synthetic Codex executable."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROUTE = Path(__file__).resolve().parents[4] / 'behavior' / 'harness' / 'codex_login_route.py'
FAKE = '''#!{python}
import base64, json, os, pathlib, sys
if sys.argv[1:] == ['--version']:
    print('codex-cli 0.166.0')
    raise SystemExit(0)
home = pathlib.Path(os.environ['CODEX_HOME'])
work = pathlib.Path.cwd()
(work / 'probe-results.txt').write_text('repository_read 1\\nworkspace_read 1\\nlogin_copy_read 1\\noutside_write 1\\nnetwork 6\\nwork_tree_write 0\\nglobal_tmp_write 1\\n')
sessions = home / 'sessions'
sessions.mkdir(parents=True, exist_ok=True)
alias = 'r' + str(0)
entry = '- `' + alias + '` = `' + str(home / 'skills') + '`\\n- tackle: sample (file: ' + alias + '/tackle/SKILL.md)' if (home / 'skills' / 'tackle' / 'SKILL.md').exists() else ''
rows = [{{'type':'response_item','payload':{{'type':'message','role':'developer','content':[{{'type':'input_text','text':entry}}]}}}}, {{'type':'event_msg','payload':{{'type':'token_count','info':{{'total_token_usage':{{'input_tokens':7,'output_tokens':3,'total_tokens':10}}}}}}}}]
rollout = sessions / ('rollout-' + str(len(list(sessions.glob('*.jsonl')))) + '.jsonl')
rollout.write_text(''.join(json.dumps(row) + '\\n' for row in rows))
print(json.dumps({{'type':'observation','argv':sys.argv[1:],'environment':dict(os.environ), 'script':base64.b64encode((work / 'route-probe.sh').read_bytes()).decode() if (work / 'route-probe.sh').exists() else ''}}))
print(json.dumps({{'type':'turn.completed','usage':{{'input_tokens':7,'output_tokens':3}}}}))
'''


class CodexRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'checkout' / 'repo'
        self.repo.mkdir(parents=True)
        self.workspace = self.repo / 'workspace'
        self.workspace.mkdir()
        self.install = self.root / 'install'
        self.install.mkdir()
        (self.install / 'SKILL.md').write_text('A test skill')
        self.fake = self.root / 'codex'
        self.fake.write_text(FAKE.format(python=sys.executable))
        self.fake.chmod(0o700)
        self.login = self.root / 'auth.json'
        self.login.write_text(json.dumps({'tokens': {'access_token':'access-secret-long', 'refresh_token':'refresh-secret-long', 'id_token':'identity-secret-long', 'account_id':'sample-account-id'}}))
        self.config = self.root / 'config.json'
        self.data = {'codex_cli':str(self.fake), 'expected_version':'0.166.0', 'node_dir':'/usr/bin', 'login_file':str(self.login), 'model':'gpt-6.1-sol', 'effort':'high', 'run_root':str(self.root / 'run'), 'state_dir':str(self.root / 'state'), 'child_path':str(self.root)+':/usr/bin:/usr/bin:/bin', 'deny_extra':['/tmp','/private/tmp'], 'caps':{'probe':1000,'development':1000,'heldout':1000}, 'reservation_tokens':100, 'headroom_tokens':100, 'session_seconds':5, 'oracle':{'python':'/usr/bin/python3','seconds':5,'denied_prefixes':[]}, 'launcher':'/usr/bin/true'}
        self.save()

    def make_cohort(self, multi=False):
        variant = self.repo / 'eval' / 'scenarios' / 'sample' / 'variants' / 'v1'
        (variant / 'input').mkdir(parents=True)
        prompts = {'sessions/01.md':b'First task.', 'sessions/02.md':b'Second task.'} if multi else {'task.md':b'Complete the task.'}
        for name, content in prompts.items():
            target = variant / 'input' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        (variant / 'oracle').mkdir()
        (variant / 'oracle' / 'check.py').write_text("import json\nprint(json.dumps({'outcome':'avoided','invalid_reason':None,'scores':{'result':2}}))\n")
        sha = lambda b: hashlib.sha256(b).hexdigest()
        fixture = sha(json.dumps({name:sha(content) for name, content in prompts.items()}, sort_keys=True, separators=(',', ':')).encode())
        manifest = {'schema':'tackle-cohort/1','cohort_id':'sample','hypothesis':'test','primary_metric':'result','decision_rule':'test','n_min':1,'seeds':[1], 'variants':[{'scenario_id':'sample','variant_id':'v1','split':'development','class':'outcome-trap','fixture_sha256':fixture}], 'arms':['control'], 'comparisons':[], 'executor':{'harness':'codex','model':'fake','effort':'high'}, 'judge':{'model_family':'test','blinded':True}, 'artifacts':{'baseline_sha256':'0'*64,'candidate_sha256':'0'*64}, 'oracle_sha256':'1'*64, 'order':[{'episode_id':'one','scenario_id':'sample','variant_id':'v1','arm':'control','seed':1}], 'created_at':'2026-01-01T00:00:00Z'}
        manifest['seal_sha256'] = sha(json.dumps(manifest, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
        cohort = self.root / 'cohort'
        cohort.mkdir()
        (cohort / 'manifest.json').write_text(json.dumps(manifest))
        return cohort

    def run_cohort(self, cohort):
        return self.invoke('run','--config',self.config,'--cohort',cohort,'--repo',self.repo,'--out',self.root / 'run-output','--stage','development','--probe',self.root / 'out')

    def run_with_hook(self, cohort, hook):
        wrapper = self.root / 'inject-finalization.py'
        wrapper.write_text('import os, pathlib, sys\n'
                           + 'sys.path.insert(0, ' + repr(str(ROUTE.parent)) + ')\n'
                           + 'import codex_login_route as route\n'
                           + hook + '\n'
                           + 'sys.exit(route.main())\n')
        args = [sys.executable, '-I', str(wrapper), 'run', '--config', str(self.config),
                '--cohort', str(cohort), '--repo', str(self.repo), '--out', str(self.root / 'run-output'),
                '--stage', 'development', '--probe', str(self.root / 'out')]
        return subprocess.run(args, capture_output=True, text=True)

    def assert_interrupted_record(self, cohort, tokens, overshoot):
        rows = (cohort / 'episodes.jsonl').read_text().splitlines()
        self.assertEqual(len(rows), 1)
        record = json.loads(rows[0])
        self.assertEqual(record['prev_sha256'], '0' * 64)
        self.assertEqual((record['outcome'], record['invalid_reason']), ('error', 'interrupted'))
        metadata = json.loads((self.root / 'run-output' / 'one' / 'episode.json').read_text())
        self.assertEqual((metadata['state'], metadata['reason']), ('incomplete', 'interrupted'))
        self.assertEqual((metadata['tokens'], metadata['overshoot_tokens']), (tokens, overshoot))
        return record

    def save(self):
        self.config.write_text(json.dumps(self.data))

    def invoke(self, *args):
        return subprocess.run([sys.executable, '-I', str(ROUTE), *map(str, args)], capture_output=True, text=True)

    def probe(self, repo=None):
        return self.invoke('probe','--config',self.config,'--repo',repo or self.repo,'--workspace',self.workspace,'--install',self.install,'--out',self.root / 'out')

    def test_usage(self):
        self.assertEqual(self.invoke('probe').returncode, 2)

    def test_invalid_config_refuses(self):
        self.data['unknown'] = 1
        self.save()
        result = self.probe()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('refused:', result.stderr)

    def test_missing_repository_refuses(self):
        result = self.probe(self.root / 'missing')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('refused:', result.stderr)

    def test_probe_uses_fake_and_reports_tokens(self):
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertTrue(observed['passed'])
        self.assertEqual(observed['tokens'], {'method':10, 'control':10})
        self.assertTrue(all(observed['boundaries'].values()))
        self.assertFalse(any((self.root / 'run').iterdir()))

    def test_child_environment_and_arguments(self):
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in (self.root / 'out' / 'method' / 'stdout.jsonl').read_text().splitlines()]
        observation = events[0]
        environment = set(observation['environment']) - {'__CF_USER_TEXT_ENCODING'}
        self.assertEqual(environment, {'PATH','HOME','CODEX_HOME','TMPDIR','LANG','TERM'})
        self.assertNotIn('--ephemeral', observation['argv'])
        self.assertNotIn('--sandbox', observation['argv'])
        self.assertEqual(observation['argv'][-1], '-')

    def test_secret_in_stream_withholds_both_arms(self):
        self.fake.write_text(self.fake.read_text() + "\nprint('access-secret-long')\n")
        result = self.probe()
        self.assertEqual(result.returncode, 1)
        out = self.root / 'out'
        observed = json.loads((out / 'result.json').read_text())
        self.assertTrue(observed['token_scan']['credential_hit'])
        self.assertEqual(observed['sessions']['method']['reason'], 'credential')
        self.assertEqual({p.name for p in out.iterdir()}, {'result.json'})
        self.assertFalse(any((self.root / 'run').iterdir()))

    def test_account_identifier_is_replaced(self):
        self.fake.write_text(self.fake.read_text() + "\nprint('sample-account-id')\n")
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertTrue(observed['token_scan']['account_id_replaced'])
        for path in (self.root / 'out').rglob('*'):
            if path.is_file():
                self.assertNotIn(b'sample-account-id', path.read_bytes())

    def test_missing_token_count_charges_reservation(self):
        source = self.fake.read_text().replace("'info':{'total_token_usage':{'input_tokens':7,'output_tokens':3,'total_tokens':10}}", "'info':None")
        self.fake.write_text(source)
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertEqual(observed['tokens'], {'method':'n/a', 'control':'n/a'})
        rows = json.loads((self.root / 'state' / 'codex-spend.json').read_text())
        self.assertEqual([row['tokens'] for row in rows], [100,100])

    def test_cap_prevents_second_arm(self):
        self.data['caps']['probe'] = 205
        self.save()
        self.fake.write_text(self.fake.read_text().replace("'total_tokens':10", "'total_tokens':110"))
        result = self.probe()
        self.assertEqual(result.returncode, 1)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertEqual(observed['sessions']['control']['reason'], 'cap')

    def test_missing_boundary_cannot_pass(self):
        self.fake.write_text(self.fake.read_text().replace('network 6\\n', ''))
        result = self.probe()
        self.assertEqual(result.returncode, 1)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertFalse(observed['boundaries']['network_denied'])

    def test_control_cohort_is_judged_and_recorded(self):
        launcher = self.root / 'launcher'
        launcher.write_text('#!/bin/sh\nshift 2\nexec "$@"\n')
        launcher.chmod(0o700)
        self.data['launcher'] = str(launcher)
        self.save()
        cohort = self.make_cohort()
        self.assertEqual(self.probe().returncode, 0)
        result = self.run_cohort(cohort)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads((cohort / 'episodes.jsonl').read_text())
        self.assertEqual(record['outcome'], 'avoided')
        self.assertEqual(record['executor']['harness'], 'codex')
        self.assertEqual(record['cost']['tokens_in'], 7)
        self.assertEqual(record['cost']['tokens_out'], 3)
        episode = json.loads((self.root / 'run-output' / 'one' / 'episode.json').read_text())
        oracle = json.loads((self.root / 'run-output' / 'one' / 'oracle.json').read_text())
        self.assertEqual(oracle['outcome'], 'avoided')
        self.assertEqual(episode['tokens'], 10)
        self.assertFalse(any((self.root / 'run').iterdir()))

    def test_tampered_cohort_is_refused(self):
        cohort = self.make_cohort()
        self.assertEqual(self.probe().returncode, 0)
        manifest = cohort / 'manifest.json'
        data = json.loads(manifest.read_text())
        data['hypothesis'] = 'changed'
        manifest.write_text(json.dumps(data))
        result = self.run_cohort(cohort)
        self.assertEqual(result.returncode, 1)
        self.assertIn('refused:', result.stderr)

    def test_running_session_is_cut_at_token_cap(self):
        self.data['caps']['probe'] = 205
        self.save()
        source = self.fake.read_text().replace("'total_tokens':10", "'total_tokens':300")
        self.fake.write_text(source + '\nimport time\ntime.sleep(5)\n')
        result = self.probe()
        self.assertEqual(result.returncode, 1)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        session = observed['sessions']['method']
        self.assertEqual((session['state'], session['reason'], session['overshoot_tokens']), ('incomplete','cap',95))
        self.assertEqual(observed['sessions']['control']['reason'], 'cap')
        self.assertTrue((self.root / 'out' / 'method' / 'rollout.jsonl').exists())

    def test_probe_reservation_refusal_is_reported(self):
        self.data['caps']['probe'] = 199
        self.save()
        result = self.probe()
        self.assertEqual(result.returncode, 1)
        self.assertIn('refused:', result.stderr)

    def test_run_credential_hit_keeps_only_safe_episode_metadata(self):
        cohort = self.make_cohort()
        self.assertEqual(self.probe().returncode, 0)
        self.fake.write_text(self.fake.read_text() + "\nprint('refresh-secret-long', file=sys.stderr)\n")
        result = self.run_cohort(cohort)
        self.assertEqual(result.returncode, 1)
        episode = self.root / 'run-output' / 'one'
        self.assertEqual({path.name for path in episode.iterdir()}, {'episode.json'})
        metadata = json.loads((episode / 'episode.json').read_text())
        self.assertEqual((metadata['state'], metadata['reason']), ('invalid', 'credential'))
        self.assertNotIn('refresh-secret-long', (episode / 'episode.json').read_text())

    def test_probe_retains_seven_boundary_statuses_and_denies_global_tmp(self):
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertTrue(observed['boundaries']['global_tmp_write_denied'])
        for arm in ('method', 'control'):
            statuses = observed['sessions'][arm]['boundary_results']
            self.assertEqual(len(statuses), 7)
            self.assertEqual(statuses['global_tmp_write'], 1)
            events = [json.loads(line) for line in (self.root / 'out' / arm / 'stdout.jsonl').read_text().splitlines()]
            script = base64.b64decode(events[0]['script']).decode()
            self.assertIn('/tmp/route-probe-', script)
            self.assertIn('/private/tmp/route-probe-', script)
            settings = ' '.join(events[0]['argv'])
            self.assertIn('\"/tmp\"=\"deny\"', settings)
            self.assertIn('\"/private/tmp\"=\"deny\"', settings)

    def test_missing_global_boundary_refuses(self):
        self.fake.write_text(self.fake.read_text().replace('global_tmp_write 1\\n', ''))
        result = self.probe()
        self.assertEqual(result.returncode, 1)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertFalse(observed['boundaries']['global_tmp_write_denied'])
        self.assertIsNone(observed['sessions']['method']['boundary_results']['global_tmp_write'])

    def test_credential_probe_withholds_boundary_statuses(self):
        self.fake.write_text(self.fake.read_text() + "\nprint('access-secret-long')\n")
        self.assertEqual(self.probe().returncode, 1)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertNotIn('boundary_results', observed['sessions']['method'])
        self.assertEqual({p.name for p in (self.root / 'out').iterdir()}, {'result.json'})

    def test_batched_token_events_settle_final_observed_total(self):
        self.data['caps']['probe'] = 205
        self.save()
        addition = """
import time
with rollout.open('a') as stream:
    for amount in (100, 300, 900):
        stream.write(json.dumps({'type':'event_msg','payload':{'type':'token_count','info':{'total_token_usage':{'input_tokens':amount,'output_tokens':0,'total_tokens':amount}}}}) + '\\n')
        stream.flush()
time.sleep(5)
"""
        self.fake.write_text(self.fake.read_text() + addition)
        result = self.probe()
        self.assertEqual(result.returncode, 1)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertEqual(observed['tokens']['method'], 900)
        self.assertEqual(observed['sessions']['method']['overshoot_tokens'], 695)
        rows = json.loads((self.root / 'state' / 'codex-spend.json').read_text())
        self.assertEqual(rows[0]['tokens'], 900)

    def test_cohort_record_credential_is_refused_before_session(self):
        cohort = self.make_cohort()
        manifest = cohort / 'manifest.json'
        data = json.loads(manifest.read_text())
        data['cohort_id'] = 'refresh-secret-long'
        del data['seal_sha256']
        data['seal_sha256'] = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        manifest.write_text(json.dumps(data))
        self.assertEqual(self.probe().returncode, 0)
        result = self.run_cohort(cohort)
        self.assertEqual(result.returncode, 1)
        self.assertIn('refused:', result.stderr)
        self.assertFalse((cohort / 'episodes.jsonl').exists())
        self.assertFalse((self.root / 'run-output').exists())

    def test_signals_finalize_each_episode_window(self):
        for window in ('session', 'settlement', 'retention', 'copy', 'oracle'):
            for signum in (2, 15):
                with self.subTest(window=window, signum=signum):
                    case = CodexRouteTests('test_usage')
                    case.setUp()
                    try:
                        launcher = case.root / 'launcher'
                        launcher.write_text('#!/bin/sh\nshift 2\nexec \"$@\"\n')
                        launcher.chmod(0o700)
                        case.data['launcher'] = str(launcher)
                        case.save()
                        cohort = case.make_cohort()
                        self.assertEqual(case.probe().returncode, 0)
                        target = {'session':('route.RolloutTail','read'), 'settlement':('route.Ledger','settle'),
                                  'retention':('route','retain_session'), 'copy':('route','clean_tree'),
                                  'oracle':('route.sub','judge')}[window]
                        wrapper = case.root / 'inject.py'
                        wrapper.write_text(
                            'import os, sys\n'
                            + 'sys.path.insert(0, ' + repr(str(ROUTE.parent)) + ')\n'
                            + 'import codex_login_route as route\n'
                            + 'owner = ' + target[0] + '\n'
                            + 'original = getattr(owner, ' + repr(target[1]) + ')\n'
                            + 'fired = False\n'
                            + 'def injected(*args, **kwargs):\n'
                            + '    global fired\n'
                            + '    if not fired:\n'
                            + '        fired = True\n'
                            + '        os.kill(os.getpid(), ' + str(signum) + ')\n'
                            + '    return original(*args, **kwargs)\n'
                            + 'setattr(owner, ' + repr(target[1]) + ', injected)\n'
                            + 'sys.exit(route.main())\n')
                        args = [sys.executable, '-I', str(wrapper), 'run', '--config', str(case.config),
                                '--cohort', str(cohort), '--repo', str(case.repo), '--out', str(case.root / 'run-output'),
                                '--stage', 'development', '--probe', str(case.root / 'out')]
                        result = subprocess.run(args, capture_output=True, text=True)
                        self.assertEqual(result.returncode, 130, result.stderr)
                        records = (cohort / 'episodes.jsonl').read_text().splitlines()
                        self.assertEqual(len(records), 1)
                        record = json.loads(records[0])
                        self.assertEqual((record['outcome'], record['invalid_reason']), ('error','interrupted'))
                        metadata = json.loads((case.root / 'run-output' / 'one' / 'episode.json').read_text())
                        self.assertEqual((metadata['state'], metadata['reason']), ('incomplete','interrupted'))
                        rows = json.loads((case.root / 'state' / 'codex-spend.json').read_text())
                        settled = [row for row in rows if row['stage'] == 'development']
                        self.assertEqual(len(settled), 1)
                        self.assertTrue(settled[0]['settled'])
                        if window != 'session':
                            self.assertEqual(metadata['tokens'], 10)
                            self.assertEqual(settled[0]['tokens'], 10)
                        self.assertFalse(any((case.root / 'run').iterdir()))
                    finally:
                        case.doCleanups()

    def test_global_probe_detects_and_cleans_escaped_file(self):
        first, second = self.root / 'temporary-a', self.root / 'temporary-b'
        first.mkdir()
        second.mkdir()
        self.fake.write_text(self.fake.read_text() + """
import re
paths = re.findall(r'\\(echo x > ([^)]+)\\)', (work / 'route-probe.sh').read_text())
pathlib.Path(paths[0]).write_text('escaped')
""")
        wrapper = self.root / 'redirect.py'
        wrapper.write_text(
            'import pathlib, sys\n'
            + 'sys.path.insert(0, ' + repr(str(ROUTE.parent)) + ')\n'
            + 'import codex_login_route as route\n'
            + 'original = pathlib.Path\n'
            + 'def redirected(value):\n'
            + '    return original({' + repr('/tmp') + ':' + repr(str(first)) + ', '
            + repr('/private/tmp') + ':' + repr(str(second)) + '}.get(str(value), value))\n'
            + 'route.Path = redirected\n'
            + 'sys.exit(route.main())\n')
        result = subprocess.run([sys.executable, '-I', str(wrapper), 'probe', '--config', str(self.config),
                                 '--repo', str(self.repo), '--workspace', str(self.workspace),
                                 '--install', str(self.install), '--out', str(self.root / 'out')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertFalse(observed['boundaries']['global_tmp_write_denied'])
        self.assertFalse(list(first.iterdir()))
        self.assertFalse(list(second.iterdir()))

    def test_unobserved_record_is_scanned_at_append(self):
        self.data['caps']['development'] = 199
        self.save()
        cohort = self.make_cohort()
        self.assertEqual(self.probe().returncode, 0)
        wrapper = self.root / 'inject.py'
        wrapper.write_text(
            'import sys\n'
            + 'sys.path.insert(0, ' + repr(str(ROUTE.parent)) + ')\n'
            + 'import codex_login_route as route\n'
            + 'original = route.record_base\n'
            + 'calls = 0\n'
            + 'def injected(*args):\n'
            + '    global calls\n'
            + '    calls += 1\n'
            + '    line = original(*args)\n'
            + '    if calls > 1: line[\"judge\"][\"model_family\"] = \"refresh-secret-long\"\n'
            + '    return line\n'
            + 'route.record_base = injected\n'
            + 'sys.exit(route.main())\n')
        result = subprocess.run([sys.executable, '-I', str(wrapper), 'run', '--config', str(self.config),
                                 '--cohort', str(cohort), '--repo', str(self.repo), '--out', str(self.root / 'run-output'),
                                 '--stage', 'development', '--probe', str(self.root / 'out')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        path = cohort / 'episodes.jsonl'
        self.assertFalse(path.exists() and 'refresh-secret-long' in path.read_text())
        metadata = json.loads((self.root / 'run-output' / 'one' / 'episode.json').read_text())
        self.assertEqual(metadata['reason'], 'credential')

    def test_unobserved_record_replaces_account_identifier(self):
        self.data['caps']['development'] = 199
        self.save()
        cohort = self.make_cohort()
        manifest = cohort / 'manifest.json'
        data = json.loads(manifest.read_text())
        data['judge']['model_family'] = 'sample-account-id'
        del data['seal_sha256']
        data['seal_sha256'] = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        manifest.write_text(json.dumps(data))
        self.assertEqual(self.probe().returncode, 0)
        result = self.run_cohort(cohort)
        self.assertEqual(result.returncode, 0, result.stderr)
        raw = (cohort / 'episodes.jsonl').read_text()
        self.assertNotIn('sample-account-id', raw)
        self.assertEqual(json.loads(raw)['judge']['model_family'], '<account-id>')

    def test_control_credential_withholds_both_boundary_maps(self):
        self.fake.write_text(self.fake.read_text() + "\nif not (home / 'skills' / 'tackle').exists(): print('access-secret-long')\n")
        self.assertEqual(self.probe().returncode, 1)
        observed = json.loads((self.root / 'out' / 'result.json').read_text())
        self.assertTrue(observed['token_scan']['credential_hit'])
        self.assertNotIn('boundary_results', observed['sessions']['method'])
        self.assertNotIn('boundary_results', observed['sessions']['control'])

    def test_interrupted_durable_append_has_one_chained_record(self):
        for window in ('fsync', 'append'):
            for signum in (2, 15):
                with self.subTest(window=window, signum=signum):
                    case = CodexRouteTests('test_usage')
                    case.setUp()
                    try:
                        launcher = case.root / 'launcher'
                        launcher.write_text('#!/bin/sh\nshift 2\nexec "$@"\n')
                        launcher.chmod(0o700)
                        case.data['launcher'] = str(launcher)
                        case.save()
                        cohort = case.make_cohort()
                        self.assertEqual(case.probe().returncode, 0)
                        owner, name = ('route.sub.os', 'fsync') if window == 'fsync' else ('route.sub', 'append_record')
                        hook = (
                            'owner = ' + owner + '\n'
                            + 'original = getattr(owner, ' + repr(name) + ')\n'
                            + 'fired = False\n'
                            + 'def injected(*args, **kwargs):\n'
                            + '    global fired\n'
                            + '    value = original(*args, **kwargs)\n'
                            + '    if not fired:\n'
                            + '        fired = True\n'
                            + '        os.kill(os.getpid(), ' + str(signum) + ')\n'
                            + '    return value\n'
                            + 'setattr(owner, ' + repr(name) + ', injected)')
                        result = case.run_with_hook(cohort, hook)
                        self.assertEqual(result.returncode, 130, result.stderr)
                        record = case.assert_interrupted_record(cohort, 10, 0)
                        self.assertEqual((record['cost']['tokens_in'], record['cost']['tokens_out']), (7, 3))
                        self.assertEqual({p.name for p in cohort.iterdir()}, {'manifest.json', 'episodes.jsonl'})
                    finally:
                        case.doCleanups()

    def test_multi_session_cleanup_and_return_keep_settled_usage(self):
        for window in ('cleanup', 'return'):
            for signum in (2, 15):
                with self.subTest(window=window, signum=signum):
                    case = CodexRouteTests('test_usage')
                    case.setUp()
                    try:
                        cohort = case.make_cohort(multi=True)
                        self.assertEqual(case.probe().returncode, 0)
                        if window == 'cleanup':
                            hook = (
                                'original = pathlib.Path.unlink\n'
                                + 'calls = 0\n'
                                + 'def injected(path, *args, **kwargs):\n'
                                + '    global calls\n'
                                + '    if path.name == "auth.json":\n'
                                + '        calls += 1\n'
                                + '        if calls == 2: os.kill(os.getpid(), ' + str(signum) + ')\n'
                                + '    return original(path, *args, **kwargs)\n'
                                + 'pathlib.Path.unlink = injected')
                        else:
                            hook = (
                                'original = route.launch\n'
                                + 'calls = 0\n'
                                + 'def injected(*args, **kwargs):\n'
                                + '    global calls\n'
                                + '    value = original(*args, **kwargs)\n'
                                + '    calls += 1\n'
                                + '    if calls == 2: os.kill(os.getpid(), ' + str(signum) + ')\n'
                                + '    return value\n'
                                + 'route.launch = injected')
                        result = case.run_with_hook(cohort, hook)
                        self.assertEqual(result.returncode, 130, result.stderr)
                        record = case.assert_interrupted_record(cohort, 20, 0)
                        self.assertEqual((record['cost']['tokens_in'], record['cost']['tokens_out']), (14, 6))
                        metadata = json.loads((case.root / 'run-output' / 'one' / 'episode.json').read_text())
                        self.assertEqual(metadata['turn_completed_tokens'], 20)
                        ledger = json.loads((case.root / 'state' / 'codex-spend.json').read_text())
                        rows = [row for row in ledger if row['stage'] == 'development']
                        self.assertEqual([row['tokens'] for row in rows], [10, 10])
                        self.assertTrue(all(row['settled'] for row in rows))
                    finally:
                        case.doCleanups()

    def test_interrupted_over_cap_session_preserves_final_excess(self):
        for window in ('settlement', 'retention', 'copy'):
            for signum in (2, 15):
                with self.subTest(window=window, signum=signum):
                    case = CodexRouteTests('test_usage')
                    case.setUp()
                    try:
                        case.data['caps']['development'] = 215
                        case.save()
                        cohort = case.make_cohort()
                        self.assertEqual(case.probe().returncode, 0)
                        source = case.fake.read_text().replace("'total_tokens':10", "'total_tokens':300")
                        case.fake.write_text(source + '\nimport time\ntime.sleep(5)\n')
                        ledger_path = case.root / 'state' / 'codex-spend.json'
                        ledger = json.loads(ledger_path.read_text())
                        ledger.append({'stage':'development', 'tokens':7, 'settled':True})
                        ledger_path.write_text(json.dumps(ledger))
                        owner, name = {'settlement':('route.Ledger','settle'), 'retention':('route','retain_session'),
                                       'copy':('route','clean_tree')}[window]
                        hook = (
                            'owner = ' + owner + '\n'
                            + 'original = getattr(owner, ' + repr(name) + ')\n'
                            + 'fired = False\n'
                            + 'def injected(*args, **kwargs):\n'
                            + '    global fired\n'
                            + '    if not fired:\n'
                            + '        fired = True\n'
                            + '        os.kill(os.getpid(), ' + str(signum) + ')\n'
                            + '    return original(*args, **kwargs)\n'
                            + 'setattr(owner, ' + repr(name) + ', injected)')
                        result = case.run_with_hook(cohort, hook)
                        self.assertEqual(result.returncode, 130, result.stderr)
                        record = case.assert_interrupted_record(cohort, 300, 92)
                        self.assertEqual((record['cost']['tokens_in'], record['cost']['tokens_out']), (7, 3))
                        rows = [row for row in json.loads(ledger_path.read_text()) if row['stage'] == 'development']
                        self.assertEqual([row['tokens'] for row in rows], [7, 300])
                        self.assertTrue(all(row['settled'] for row in rows))
                    finally:
                        case.doCleanups()

    def test_interrupted_append_preserves_existing_chain_prefix(self):
        for signum in (2, 15):
            with self.subTest(signum=signum):
                case = CodexRouteTests('test_usage')
                case.setUp()
                try:
                    launcher = case.root / 'launcher'
                    launcher.write_text('#!/bin/sh\nshift 2\nexec "$@"\n')
                    launcher.chmod(0o700)
                    case.data['launcher'] = str(launcher)
                    case.save()
                    cohort = case.make_cohort()
                    manifest = cohort / 'manifest.json'
                    data = json.loads(manifest.read_text())
                    data['order'].append(dict(data['order'][0], episode_id='two'))
                    del data['seal_sha256']
                    data['seal_sha256'] = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
                    manifest.write_text(json.dumps(data))
                    self.assertEqual(case.probe().returncode, 0)
                    hook = (
                        'original = route.sub.append_record\n'
                        + 'calls = 0\n'
                        + 'def injected(*args, **kwargs):\n'
                        + '    global calls\n'
                        + '    value = original(*args, **kwargs)\n'
                        + '    calls += 1\n'
                        + '    if calls == 2: os.kill(os.getpid(), ' + str(signum) + ')\n'
                        + '    return value\n'
                        + 'route.sub.append_record = injected')
                    result = case.run_with_hook(cohort, hook)
                    self.assertEqual(result.returncode, 130, result.stderr)
                    lines = (cohort / 'episodes.jsonl').read_bytes().splitlines()
                    self.assertEqual(len(lines), 2)
                    first, second = map(json.loads, lines)
                    self.assertEqual(first['episode_id'], 'one')
                    self.assertEqual((second['episode_id'], second['outcome'], second['invalid_reason']), ('two', 'error', 'interrupted'))
                    self.assertEqual(second['prev_sha256'], hashlib.sha256(lines[0]).hexdigest())
                    metadata = json.loads((case.root / 'run-output' / 'two' / 'episode.json').read_text())
                    self.assertEqual((metadata['state'], metadata['reason'], metadata['tokens']), ('incomplete', 'interrupted', 10))
                finally:
                    case.doCleanups()

    def test_reconciles_durable_line_without_memory_acknowledgement(self):
        launcher = self.root / 'launcher'
        launcher.write_text('#!/bin/sh\nshift 2\nexec "$@"\n')
        launcher.chmod(0o700)
        self.data['launcher'] = str(launcher)
        self.save()
        cohort = self.make_cohort()
        self.assertEqual(self.probe().returncode, 0)
        hook = (
            'original = route.sub.os.fsync\n'
            + 'fired = False\n'
            + 'def injected(descriptor):\n'
            + '    global fired\n'
            + '    original(descriptor)\n'
            + '    if not fired:\n'
            + '        fired = True\n'
            + '        raise KeyboardInterrupt()\n'
            + 'route.sub.os.fsync = injected')
        result = self.run_with_hook(cohort, hook)
        self.assertEqual(result.returncode, 130, result.stderr)
        record = self.assert_interrupted_record(cohort, 10, 0)
        self.assertEqual((record['cost']['tokens_in'], record['cost']['tokens_out']), (7, 3))
        self.assertEqual({p.name for p in cohort.iterdir()}, {'manifest.json', 'episodes.jsonl'})
