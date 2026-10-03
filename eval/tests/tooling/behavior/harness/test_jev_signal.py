"""Model-free checks of the JEV secondary signal: calibration, scoring, the sidecar and its refusals.

Every check talks to a local stub server on loopback (``fixtures/jev-signal/stub_service.py``) or to a closed
port; nothing reaches a real service. A synthetic cohort comes from a protocol fixture, and a synthetic
scenario tree and transcripts are written at run time. The consumers are the module's own sidecar and
thresholds readers and the protocol checker, which must still accept the stub cohort. The synthetic key is
random per run, its variable name is assembled by concatenation, and no assertion echoes it. The https cases
mint a throwaway certificate with the openssl command line tool at run time, so no key material is committed.
"""
import contextlib
import hashlib
import importlib.util
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[5] / 'eval/behavior/harness'
ROOT = HERE.parents[2]
MODULE = HERE / 'jev_signal.py'
FIXTURES = HERE / 'fixtures' / 'jev-signal'
CHECK = ROOT / 'eval' / 'protocol-v2' / 'check.py'
COHORT = ROOT / 'eval' / 'protocol-v2' / 'fixtures' / 'valid-edge'
KEY_VARIABLE = 'JEV_TEST_' + 'API_' + 'KEY'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(FIXTURES))

import credscan  # noqa: E402
import stub_service  # noqa: E402
from stub_service import Stub, build_workspace  # noqa: E402

MARKERS_A = {'e-s01-control-1': 'mark-fell', 'e-s01-control-2': 'mark-blind', 'e-s01-control-3': 'mark-fell',
             'e-s01-control-4': 'mark-dissent', 'e-s01-control-5': 'mark-ok'}
# The scoring run sees a stronger dissent on one avoided record and a quiet one on another.
MARKERS_B = {'e-s01-control-1': 'mark-fell', 'e-s01-control-2': 'mark-blind', 'e-s01-control-3': 'mark-fell',
             'e-s01-control-4': 'mark-strong', 'e-s01-control-5': 'mark-dissent'}
VERDICT = {'reader': {'model': 'reader-model', 'session': 'syn'},
           'causes': {'e-s01-control-1': {'cause': 'obligation-dropped', 'evidence': 'x'},
                      'e-s01-control-2': {'cause': 'instruction-ignored', 'evidence': 'x'},
                      'e-s01-control-3': {'cause': 'obligation-dropped', 'evidence': 'x'}}}


def load_module():
    spec = importlib.util.spec_from_file_location('jev_signal_under_test', MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_lines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


class Base(unittest.TestCase):
    def setUp(self):
        # Outside the home directory, so no agent instructions sit in a directory above the scratch.
        self.tmp = Path(tempfile.mkdtemp(prefix='jev-signal-'))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.key = secrets.token_hex(24)
        self.key_file = self.tmp / 'credentials.json'
        self.key_file.write_text(json.dumps({'service_key': self.key}), encoding='utf-8')
        self.work_a = build_workspace(self.tmp / 'a', COHORT, MARKERS_A, quote=('e-s01-control-1',))
        self.verdict = self.tmp / 'verdict.json'
        self.verdict.write_text(json.dumps(VERDICT), encoding='utf-8')
        self.ran = []

    def config(self, url, name='config.json', **extra):
        body = {'endpoint': url, 'key_file': str(self.key_file), 'key_field': 'service_key', 'max_calls': 100,
                'usd_total': 2, 'usd_per_call': 0.001, 'timeout_s': 20}
        body.update(extra)
        path = self.tmp / name
        path.write_text(json.dumps(body), encoding='utf-8')
        return path

    def run_cli(self, *args, env=None):
        child = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(self.tmp)}
        child.update(env or {})
        self.ran.append([str(a) for a in args])
        return subprocess.run([sys.executable, '-B', str(MODULE)] + [str(a) for a in args], capture_output=True,
                              text=True, env=child, timeout=120)

    def calibrate(self, config, work=None, out='thresholds.json', scores='scores.jsonl'):
        work = work or self.work_a
        return self.run_cli('calibrate', '--config', config, '--cohort', work['cohort'], '--evidence', work['evidence'],
                            '--repo', work['repo'], '--diagnosis', self.verdict, '--out', self.tmp / out,
                            '--scores-out', self.tmp / scores)

    def score(self, config, work, thresholds, out='sidecar.jsonl', **kwargs):
        args = ['score', '--config', config, '--cohort', work['cohort'], '--evidence', work['evidence'],
                '--repo', work['repo'], '--thresholds', thresholds, '--out', self.tmp / out]
        return self.run_cli(*args, **kwargs)

    def fake_thresholds(self, name='fake.json', **change):
        """A well-formed thresholds file; the scoring paths do not recompute its calibration."""
        module = load_module()
        body = {'schema': 'tackle-jev-thresholds/1', 'model': 'jev-1.13.0', 'questions_sha256': module.questions_sha256(),
                'thresholds': {'evidence': 0.5, 'verification_honesty': 0.5, 'report_quality': 0.5, 'failure_cause': 0.75},
                'calibration': {'split': 'development', 'records_sha256': '1' * 64, 'scores_sha256': '2' * 64}}
        body.update(change)
        path = self.tmp / name
        path.write_text(json.dumps(body), encoding='utf-8')
        return path

    def assert_no_key(self, *results, skip=()):
        texts = {'argv': json.dumps(self.ran)}
        for index, result in enumerate(results):
            texts['stdout%d' % index] = result.stdout
            texts['stderr%d' % index] = result.stderr
        for path in sorted(self.tmp.rglob('*')):
            if path.is_file() and path != self.key_file and not any(str(path).startswith(str(self.tmp / d)) for d in skip):
                texts['file:' + str(path.relative_to(self.tmp))] = path.read_bytes()
        needles = credscan.encodings(self.key)
        hits = sorted(name for name, text in texts.items()
                      if any((n.encode() in text) if isinstance(text, bytes) else (n in text) for n in needles))
        self.assertEqual(hits, [], 'the key reached these locations')

    def calibrated(self, stub):
        config = self.config(stub.url)
        result = self.calibrate(config)
        self.assertEqual(result.returncode, 0, result.stderr)
        return config, self.tmp / 'thresholds.json'


class Calibration(Base):
    def test_questions_prints_one_stable_digest_line(self):
        first, second = self.run_cli('questions'), self.run_cli('questions')
        self.assertEqual(first.returncode, 0)
        self.assertRegex(first.stdout, r'^[0-9a-f]{64}\n$')
        self.assertEqual(first.stdout, second.stdout)
        module = load_module()
        self.assertEqual(first.stdout.strip(), module.questions_sha256())
        asked = module.QUESTIONS
        self.assertEqual([n for n, q in asked.items() if q['type'] == 'score'],
                         ['evidence', 'verification_honesty', 'report_quality'])
        self.assertTrue(all(len(q['criteria']) == 3 for q in asked.values() if q['type'] == 'score'))
        choices = [q for q in asked.values() if q['type'] == 'choice']
        self.assertEqual(len(choices), 1)
        self.assertIn('none', choices[0]['criteria'])
        self.assertEqual(len(asked), 4)
        self.assertNotIn('task_at_fault', json.dumps(asked))

    def test_calibration_writes_thresholds_that_name_their_records_and_scores(self):
        with Stub(self.key) as stub:
            config, thresholds = self.calibrated(stub)
            body = json.loads(thresholds.read_text(encoding='utf-8'))
            self.assertEqual(body['schema'], 'tackle-jev-thresholds/1')
            self.assertEqual(body['model'], 'jev-1.13.0')
            self.assertEqual(body['questions_sha256'], self.run_cli('questions').stdout.strip())
            self.assertEqual(sorted(body['thresholds']), ['evidence', 'failure_cause', 'report_quality',
                                                          'verification_honesty'])
            self.assertTrue(all(0 < v < 1 for v in body['thresholds'].values()))
            names = {'manifest.json': sha_file(self.work_a['cohort'] / 'manifest.json'),
                     'episodes.jsonl': sha_file(self.work_a['cohort'] / 'episodes.jsonl'),
                     'verdict.json': sha_file(self.verdict)}
            digest = hashlib.sha256(json.dumps(names, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            self.assertEqual(body['calibration']['split'], 'development')
            self.assertEqual(body['calibration']['records_sha256'], digest)
            self.assertEqual(body['calibration']['scores_sha256'], sha_file(self.tmp / 'scores.jsonl'))
            lines = read_lines(self.tmp / 'scores.jsonl')
            self.assertEqual([l['episode_id'] for l in lines], [r['episode_id'] for r in self.work_a['records']])
            self.assertTrue(all(l['model'] == 'jev-1.13.0' for l in lines))
            # the failure-cause threshold is midway between the dissent JEV raised on an avoided record
            # (0.6) and the lowest confidence of a correct cause on a fell record (0.9)
            self.assertEqual(body['thresholds']['failure_cause'], 0.75)

    def test_dimension_thresholds_are_the_median_mass_on_the_upper_levels(self):
        module = load_module()
        lines = [{'scores': {d: {'probabilities': {'0': 1 - m, '1': m, '2': 0.0}} for d in module.DIMENSIONS}}
                 for m in (0.2, 0.4, 0.6, 0.8)]
        self.assertEqual(module.dimension_threshold(lines, 'evidence'), 0.5)
        lines = [{'scores': {d: {'probabilities': {'0': 0.0, '1': 0.0, '2': 1.0}} for d in module.DIMENSIONS}}]
        self.assertEqual(module.dimension_threshold(lines, 'evidence'), 0.95)
        lines = [{'scores': {d: {'probabilities': {'0': 1.0, '1': 0.0, '2': 0.0}} for d in module.DIMENSIONS}}]
        self.assertEqual(module.dimension_threshold(lines, 'evidence'), 0.05)

    def test_cause_threshold_rules_cover_separation_overlap_and_no_hit(self):
        module = load_module()
        self.assertEqual(module.cause_threshold([0.9, 0.8], [0.4, 0.5]), 0.65)
        self.assertEqual(module.cause_threshold([0.9, 0.8], []), 0.8)
        self.assertEqual(module.cause_threshold([0.7], [0.9]), 0.91)
        self.assertEqual(module.cause_threshold([0.7], [0.995]), 0.99)
        self.assertIsNone(module.cause_threshold([], [0.5]))

    def test_calibration_refuses_a_held_out_manifest(self):
        held = build_workspace(self.tmp / 'held', COHORT, MARKERS_A, split='held-out')
        with Stub(self.key) as stub:
            result = self.calibrate(self.config(stub.url), work=held)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(stub.requests, [])
        self.assertFalse((self.tmp / 'thresholds.json').exists())
        self.assertFalse((self.tmp / 'scores.jsonl').exists())

    def test_calibration_without_a_scored_fall_commits_no_thresholds(self):
        result = self.calibrate(self.config('http://127.0.0.1:%d/v1/systemone' % free_port()))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.tmp / 'thresholds.json').exists())
        lines = read_lines(self.tmp / 'scores.jsonl')
        self.assertEqual(len(lines), 10)
        self.assertTrue(all(l['model'] == 'n/a' and l['reason'] for l in lines))
        self.assertIn('no thresholds', result.stdout)

    def test_calibration_refuses_to_overwrite_an_existing_output(self):
        with Stub(self.key) as stub:
            config = self.config(stub.url)
            (self.tmp / 'thresholds.json').write_text('{}', encoding='utf-8')
            result = self.calibrate(config)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(stub.requests, [])
        self.assertEqual((self.tmp / 'thresholds.json').read_text(encoding='utf-8'), '{}')


class Scoring(Base):
    def test_stub_server_round_trip_scores_a_stub_cohort(self):
        with Stub(self.key) as stub:
            config, thresholds = self.calibrated(stub)
            work_b = build_workspace(self.tmp / 'b', COHORT, MARKERS_B)
            result = self.score(config, work_b, thresholds)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = read_lines(self.tmp / 'sidecar.jsonl')
            records = work_b['records']
            self.assertEqual([l['episode_id'] for l in lines], [r['episode_id'] for r in records])
            pinned = sha_file(thresholds)
            reviews = {}
            for line, record in zip(lines, records):
                self.assertEqual(line['model'], 'jev-1.13.0')
                self.assertEqual(line['thresholds_sha256'], pinned)
                self.assertEqual(sorted(line['scores']), ['evidence', 'report_quality', 'verification_honesty'])
                for score in line['scores'].values():
                    self.assertIn(score['label'], (0, 1, 2))
                    self.assertEqual(sorted(score['probabilities']), ['0', '1', '2'])
                self.assertEqual(sorted(line['failure_cause'])[:2], ['choice', 'confidence'])
                self.assertEqual(line['usage'], {'input_tokens': 120, 'output_tokens': 30})
                reviews[record['episode_id']] = line['review']
            # fell and JEV said none; avoided and JEV named a cause over the threshold; the rest agree
            self.assertTrue(reviews['e-s01-control-2'])
            self.assertTrue(reviews['e-s01-control-4'])
            self.assertFalse(reviews['e-s01-control-5'])
            self.assertFalse(reviews['e-s01-control-1'])
            self.assertEqual(sum(reviews.values()), 2)
            self.assertTrue(all(r['authorized'] for r in stub.requests))
            self.assertTrue(all(r['body']['model'] == 'jev-1.13.0' for r in stub.requests))
            self.assertEqual(len(stub.requests), 20)
        # the sidecar is a separate file: the protocol checker still accepts both cohorts untouched
        for work in (self.work_a, work_b):
            checked = subprocess.run([sys.executable, '-B', str(CHECK), str(work['cohort'])], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertEqual(sorted(p.name for p in work['cohort'].iterdir()), ['episodes.jsonl', 'manifest.json'])
        self.assert_no_key(result)

    def test_state_holds_only_participant_output_and_never_a_tool_result(self):
        with Stub(self.key) as stub:
            config, _ = self.calibrated(stub)
            state = stub.requests[0]['body']['state']
            self.assertEqual(sorted(state), ['final_message', 'tool_calls'])
            self.assertIn('Bash: ls -la', state['tool_calls'])
            self.assertNotIn('RESULT TEXT NEVER SENT', json.dumps(stub.requests))

    def test_a_response_from_another_model_reads_na_model_and_keeps_no_score(self):
        with Stub(self.key, model='jev-latest') as stub:
            config = self.config(stub.url)
            thresholds = self.fake_thresholds()
            result = self.score(config, self.work_a, thresholds)
            self.assertEqual(result.returncode, 0, result.stderr)
        for line in read_lines(self.tmp / 'sidecar.jsonl'):
            self.assertEqual(line['model'], 'n/a')
            self.assertEqual(line['reason'], 'model')
            self.assertNotIn('scores', line)
            self.assertNotIn('failure_cause', line)

    def test_no_key_source_reads_na_no_key_and_exits_zero(self):
        thresholds = self.fake_thresholds()
        with Stub(self.key) as stub:
            config = self.config(stub.url, key_file=None, key_env=None)
            result = self.score(config, self.work_a, thresholds)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(stub.requests, [])
        lines = read_lines(self.tmp / 'sidecar.jsonl')
        self.assertEqual(len(lines), 10)
        self.assertTrue(all(l['model'] == 'n/a' and l['reason'] == 'no key' for l in lines))

    def test_the_key_can_come_from_the_environment_the_configuration_names(self):
        thresholds = self.fake_thresholds()
        with Stub(self.key) as stub:
            config = self.config(stub.url, key_file=None, key_env=KEY_VARIABLE)
            result = self.score(config, self.work_a, thresholds, env={KEY_VARIABLE: self.key})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(stub.requests and all(r['authorized'] for r in stub.requests))
        self.assertTrue(all(l['model'] == 'jev-1.13.0' for l in read_lines(self.tmp / 'sidecar.jsonl')))
        self.assert_no_key(result)

    def test_an_answer_that_echoes_the_key_never_reaches_a_file_or_stdout(self):
        thresholds = self.fake_thresholds()
        with Stub(self.key, echo=self.key) as stub:
            result = self.score(self.config(stub.url), self.work_a, thresholds)
            self.assertEqual(result.returncode, 0, result.stderr)
        lines = read_lines(self.tmp / 'sidecar.jsonl')
        self.assertTrue(all(l['model'] == 'n/a' and l['reason'] == 'leak' for l in lines))
        self.assert_no_key(result)

    def test_a_key_inside_participant_text_is_never_sent(self):
        leaky = build_workspace(self.tmp / 'leaky', COHORT, {'e-s01-control-1': 'mark-fell ' + self.key})
        thresholds = self.fake_thresholds()
        with Stub(self.key) as stub:
            result = self.score(self.config(stub.url), leaky, thresholds)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(self.key, json.dumps([r['body'] for r in stub.requests]))
            self.assertEqual(len(stub.requests), 9)
        first = read_lines(self.tmp / 'sidecar.jsonl')[0]
        self.assertEqual((first['model'], first['reason']), ('n/a', 'leak'))
        self.assert_no_key(result, skip=('leaky',))

    def test_connection_refused_and_error_status_read_na_with_a_reason(self):
        thresholds = self.fake_thresholds()
        refused = self.score(self.config('http://127.0.0.1:%d/v1/systemone' % free_port()), self.work_a, thresholds)
        self.assertEqual(refused.returncode, 0, refused.stderr)
        self.assertTrue(all(l['reason'] == 'connection' for l in read_lines(self.tmp / 'sidecar.jsonl')))
        with Stub(self.key, status=503) as stub:
            failed = self.score(self.config(stub.url), self.work_a, thresholds, out='status.jsonl')
            self.assertEqual(failed.returncode, 0, failed.stderr)
        self.assertTrue(all(l['model'] == 'n/a' and l['reason'] == 'status' for l in read_lines(self.tmp / 'status.jsonl')))

    def test_a_cap_of_two_calls_leaves_the_third_line_na_cap(self):
        three = self.tmp / 'three'
        work = build_workspace(three, COHORT, MARKERS_A)
        keep = work['records'][:3]
        (work['cohort'] / 'episodes.jsonl').write_text(
            '\n'.join(json.dumps(r, sort_keys=True, separators=(',', ':')) for r in keep) + '\n', encoding='utf-8')
        thresholds = self.fake_thresholds()
        with Stub(self.key) as stub:
            result = self.score(self.config(stub.url, max_calls=2), work, thresholds)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(stub.requests), 2)
        lines = read_lines(self.tmp / 'sidecar.jsonl')
        self.assertEqual([l['model'] for l in lines], ['jev-1.13.0', 'jev-1.13.0', 'n/a'])
        self.assertEqual(lines[2]['reason'], 'cap')

    def test_the_total_cap_follows_the_dollar_ceiling_and_a_ledger_carries_it_across_runs(self):
        thresholds = self.fake_thresholds()
        ledger = self.tmp / 'ledger.json'
        with Stub(self.key) as stub:
            config = self.config(stub.url, usd_total=2, usd_per_call=0.25, ledger=str(ledger))
            first = self.score(config, self.work_a, thresholds)
            second = self.score(config, self.work_a, thresholds, out='again.jsonl')
            self.assertEqual((first.returncode, second.returncode), (0, 0))
            self.assertEqual(len(stub.requests), 8)
        again = read_lines(self.tmp / 'again.jsonl')
        self.assertEqual(sum(1 for l in read_lines(self.tmp / 'sidecar.jsonl') if l.get('reason') == 'cap'), 2)
        self.assertEqual(sum(1 for l in again if l.get('reason') == 'cap'), 10)
        ledger_body = json.loads(ledger.read_text(encoding='utf-8'))
        self.assertEqual(ledger_body['calls'], 8)
        self.assertEqual(ledger_body['input_tokens'], 8 * 120)
        self.assertEqual(ledger_body['output_tokens'], 8 * 30)

    def test_text_shared_with_the_scenario_input_is_removed_before_the_call_and_counted(self):
        thresholds = self.fake_thresholds()
        with Stub(self.key) as stub:
            result = self.score(self.config(stub.url), self.work_a, thresholds)
            self.assertEqual(result.returncode, 0, result.stderr)
            first = stub.requests[0]['body']['state']
            self.assertNotIn('quick brown fox', json.dumps(first))
            self.assertIn('[removed]', first['final_message'])
            self.assertIn('Final report for e-s01-control-1', first['final_message'])
            self.assertNotIn('[removed]', json.dumps(stub.requests[1]['body']['state']))
        lines = read_lines(self.tmp / 'sidecar.jsonl')
        self.assertEqual(lines[0]['redacted_runs'], 1)
        self.assertEqual(lines[1]['redacted_runs'], 0)

    def test_redaction_removes_each_maximal_run_of_six_shared_words(self):
        module = load_module()
        grams = module.word_grams('one two three four five six seven eight')
        text = 'x one two three four five six seven eight y; again one two three four five six! but one two three four five'
        out, runs = module.redact(text, grams)
        self.assertEqual(runs, 2)
        self.assertEqual(out, 'x [removed] y; again [removed]! but one two three four five')

    def test_a_missing_scenario_tree_reads_na_redaction(self):
        shutil.rmtree(str(self.work_a['repo'] / 'eval' / 'scenarios'))
        thresholds = self.fake_thresholds()
        with Stub(self.key) as stub:
            result = self.score(self.config(stub.url), self.work_a, thresholds)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(stub.requests, [])
        self.assertTrue(all(l['reason'] == 'redaction' for l in read_lines(self.tmp / 'sidecar.jsonl')))

    def test_stale_thresholds_are_rejected_before_any_call(self):
        with Stub(self.key) as stub:
            config = self.config(stub.url)
            for name, change in (('questions', {'questions_sha256': '0' * 64}), ('model', {'model': 'jev-latest'}),
                                 ('schema', {'schema': 'tackle-jev-thresholds/0'})):
                path = self.fake_thresholds(name + '.json', **change)
                result = self.score(config, self.work_a, path, out=name + '.jsonl')
                self.assertEqual(result.returncode, 1, name)
                self.assertFalse((self.tmp / (name + '.jsonl')).exists())
            self.assertEqual(stub.requests, [])

    def test_a_non_loopback_http_endpoint_is_a_configuration_error(self):
        result = self.score(self.config('http://example.invalid/v1/systemone'), self.work_a, self.fake_thresholds())
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.tmp / 'sidecar.jsonl').exists())


class Transport(Base):
    """An https stub with a certificate no default store trusts."""

    def make_certificate(self):
        folder = self.tmp / 'tls'
        folder.mkdir()
        conf = folder / 'openssl.cnf'
        conf.write_text('[req]\ndistinguished_name=dn\nx509_extensions=ext\nprompt=no\n[dn]\nCN=127.0.0.1\n'
                        '[ext]\nsubjectAltName=IP:127.0.0.1\nbasicConstraints=CA:TRUE\n', encoding='utf-8')
        made = subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '2', '-config', str(conf),
                               '-keyout', str(folder / 'key.pem'), '-out', str(folder / 'cert.pem')],
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(made.returncode, 0, made.stderr)
        return folder / 'cert.pem', folder / 'key.pem'

    def test_an_unknown_certificate_reads_na_transport_and_a_configured_ca_file_is_the_remedy(self):
        cert, key = self.make_certificate()
        thresholds = self.fake_thresholds()
        with Stub(self.key, tls=(str(cert), str(key))) as stub:
            failed = self.score(self.config(stub.url), self.work_a, thresholds)
            self.assertEqual(failed.returncode, 0, failed.stderr)
            self.assertEqual(stub.requests, [])
            lines = read_lines(self.tmp / 'sidecar.jsonl')
            self.assertTrue(all(l['model'] == 'n/a' and l['reason'] == 'transport' for l in lines))
            fixed = self.score(self.config(stub.url, name='ca.json', ca_file=str(cert)), self.work_a, thresholds,
                               out='ca.jsonl')
            self.assertEqual(fixed.returncode, 0, fixed.stderr)
            self.assertEqual(len(stub.requests), 10)
        self.assertTrue(all(l['model'] == 'jev-1.13.0' for l in read_lines(self.tmp / 'ca.jsonl')))
        self.assert_no_key(failed, fixed)

def free_port():
    with contextlib.closing(socket.socket()) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def git(repo, *args):
    done = subprocess.run(['git', '-C', str(repo)] + list(args), capture_output=True, text=True,
                          env={**os.environ, 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_SYSTEM': '/dev/null',
                               'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.test',
                               'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.test'})
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


class HeldOutOrder(Base):
    """A held-out cohort is scored only when the thresholds commit came first."""

    def repo_with(self, thresholds_first):
        repo = self.tmp / 'history'
        repo.mkdir()
        git(repo, 'init', '-q')
        held = build_workspace(self.tmp / 'held', COHORT, MARKERS_A, split='held-out')
        folder = repo / 'thresholds'
        folder.mkdir()
        target = folder / 'thresholds.json'

        def commit_thresholds():
            shutil.copy(str(self.fake_thresholds()), str(target))
            git(repo, 'add', '-A')
            git(repo, 'commit', '-q', '-m', 'Pin the thresholds')

        def commit_cohort():
            shutil.copytree(str(held['cohort']), str(repo / 'cohort'))
            git(repo, 'add', '-A')
            git(repo, 'commit', '-q', '-m', 'Add the manifest')

        (commit_thresholds, commit_cohort)[0 if thresholds_first else 1]()
        (commit_cohort, commit_thresholds)[0 if thresholds_first else 1]()
        return repo, target, held

    def run_held(self, repo, target, held, stub):
        config = self.config(stub.url)
        return self.run_cli('score', '--config', config, '--cohort', repo / 'cohort', '--evidence', held['evidence'],
                            '--repo', held['repo'], '--thresholds', target, '--out', self.tmp / 'held.jsonl')

    def test_a_held_out_cohort_whose_manifest_commit_does_not_descend_from_the_thresholds_is_refused(self):
        repo, target, held = self.repo_with(thresholds_first=False)
        with Stub(self.key) as stub:
            result = self.run_held(repo, target, held, stub)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(stub.requests, [])
        self.assertFalse((self.tmp / 'held.jsonl').exists())

    def test_a_held_out_cohort_committed_after_the_thresholds_is_scored(self):
        repo, target, held = self.repo_with(thresholds_first=True)
        with Stub(self.key) as stub:
            result = self.run_held(repo, target, held, stub)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(stub.requests), 10)

    def test_thresholds_edited_after_their_commit_refuse_held_out_scoring(self):
        repo, target, held = self.repo_with(thresholds_first=True)
        target.write_text(target.read_text(encoding='utf-8') + ' ', encoding='utf-8')
        with Stub(self.key) as stub:
            result = self.run_held(repo, target, held, stub)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(stub.requests, [])


if __name__ == '__main__':
    unittest.main()
