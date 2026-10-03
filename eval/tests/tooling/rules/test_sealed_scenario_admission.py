"""A sealed, blind-authored scenario tree is admitted by its committed digest, never by its path.

Guarantee: the committed-text guard exempts workspace-id-shaped tokens inside a scenario's input tree and
its answer-sheet/oracle set only while the working-tree bytes of that tree hash to the digest the scenario
index records for a blind-authored entry. Any edit, digest change, shape change, symlink or non-blind entry
reverts every file of the tree to ordinary scanning, and the initiative-slug scan never relaxes.
Every scenario here is synthetic; no protected scenario content is copied.
"""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'eval/rules'))
from committed_text import ID_PATTERN, scan_committed_text

_spec = importlib.util.spec_from_file_location('check_index', REPO / 'eval/scenario-index/check_index.py')
check_index = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_index)

SID = 's' + '99-synthetic'
VID = 'v1'
WORKSPACE = 'sample-ledger'
SLUG = 'sample-initiative'
TASK, DECISION, QUESTION = 'T' + '-1', 'D' + '-2', 'Q' + '-3'
SCENARIO = 'eval/scenarios/' + SID + '/'
VARIANT = SCENARIO + 'variants/' + VID + '/'
INPUT = VARIANT + 'input/'
DOCS = 'fixture/docs/plans/' + WORKSPACE + '/'


def prose(name):
    return 'Free prose about ' + name + ' mentions ' + TASK + ', ' + DECISION + ' and ' + QUESTION + ' inline.\n'


def sha(data):
    return hashlib.sha256(data).hexdigest()


class SealedScenarioAdmissionTests(unittest.TestCase):
    def git(self, root, *args):
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        result = subprocess.run(['git', '-C', str(root)] + list(args), capture_output=True, text=True, env=env, check=False)
        if result.returncode:
            self.fail('fixture git command failed: git ' + ' '.join(args))
        return result

    def repository(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve() / 'repo'
        root.mkdir()
        self.git(root, 'init', '-q', '-b', 'main')
        self.git(root, 'config', 'user.name', 'Tackle fixture')
        self.git(root, 'config', 'user.email', 'tackle-fixture@example.invalid')
        (root / 'README.md').write_text('base\n', encoding='utf-8')
        self.git(root, 'add', '-A')
        self.git(root, 'commit', '-q', '-m', 'base')
        return root, self.git(root, 'rev-parse', 'HEAD').stdout.strip()

    def write(self, root, relative, text):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def scan(self, root, base, slug=SLUG):
        return scan_committed_text(root, base, slug)

    def input_mapping(self, root, variant_path=None):
        base = root / (variant_path or INPUT.rstrip('/'))
        mapping = {}
        for path in sorted(base.rglob('*')):
            if path.is_file():
                relative = path.relative_to(base).as_posix()
                mapping[relative] = sha(path.read_bytes())
        return mapping

    def oracle_mapping(self, root, scenario=SID):
        base = root / ('eval/scenarios/' + scenario)
        mapping = {}
        for path in sorted(base.rglob('*')):
            relative = path.relative_to(base).as_posix()
            parts = relative.split('/')
            wanted = (relative == 'GROUND-TRUTH.md' or
                      (len(parts) == 3 and parts[0] == 'variants' and parts[2] == 'GROUND-TRUTH.md') or
                      (len(parts) > 3 and parts[0] == 'variants' and parts[2] == 'oracle'))
            if path.is_file() and wanted:
                mapping[relative] = sha(path.read_bytes())
        return mapping

    def entry(self, root, scenario=SID, variant=VID, blind=True, stageable=True, split='development',
              path=None, fixture_digest=True, oracle_digest=True):
        record = {
            'variant_id': variant, 'split': split,
            'path': path if path is not None else 'eval/scenarios/' + scenario + '/variants/' + variant + '/input',
            'prompts': ['task.md'], 'fixture': 'fixture', 'stageable': stageable,
            'fixture_sha256': None, 'control_exposure': {'install': False, 'fragments': []}}
        if fixture_digest is True:
            record['fixture_sha256'] = check_index.mapping_digest(self.input_mapping(
                root, 'eval/scenarios/' + scenario + '/variants/' + variant + '/input'))
        elif fixture_digest is not False:
            record['fixture_sha256'] = fixture_digest
        result = {'scenario_id': scenario, 'class': 'outcome-trap', 'harm': 'synthetic harm', 'covers': [],
                  'authored': {'actors': ['synthetic-author'], 'blind': blind}, 'variants': [record]}
        if oracle_digest is True:
            result['oracle_sha256'] = check_index.mapping_digest(self.oracle_mapping(root, scenario))
        elif oracle_digest is not False:
            result['oracle_sha256'] = oracle_digest
        return result

    def index(self, root, *entries):
        document = {'schema': 'tackle-scenario-index/1', 'scenarios': list(entries)}
        self.write(root, 'eval/scenarios/INDEX.json', json.dumps(document, indent=1) + '\n')

    def sealed(self, **options):
        """A synthetic sealed scenario: staged, indexed with matching digests, base commit before it."""
        root, base = self.repository()
        self.write(root, INPUT + 'task.md', prose('the task'))
        for document in ('plan', 'history', 'task-board', 'resource-usage'):
            self.write(root, INPUT + DOCS + document + '.md', prose(document))
        self.write(root, INPUT + DOCS + 'reports/' + TASK + '-report.md', prose('a report'))
        self.write(root, SCENARIO + 'GROUND-TRUTH.md', prose('the scenario sheet'))
        self.write(root, VARIANT + 'GROUND-TRUTH.md', prose('the variant sheet'))
        self.write(root, VARIANT + 'oracle/check.py', '# ' + prose('the check'))
        self.write(root, VARIANT + 'oracle/data.json', json.dumps({'note': prose('data')}) + '\n')
        self.write(root, VARIANT + 'oracle/selftest/fell/final/docs/plans/' + WORKSPACE + '/plan.md', prose('a final tree'))
        self.index(root, self.entry(root, **options))
        self.git(root, 'add', '-A')
        return root, base

    def reindex(self, root, **options):
        self.index(root, self.entry(root, **options))
        self.git(root, 'add', '-A')

    def paths(self, findings, kind='workspace-id'):
        return {item.path for item in findings if item.kind == kind}

    def tiers(self, findings):
        found = self.paths(findings)
        return {'input': {p for p in found if p.startswith(INPUT)},
                'oracle': {p for p in found if p.startswith(VARIANT + 'oracle/') or p.endswith('GROUND-TRUTH.md')}}

    def assertTierFindings(self, findings, input_has, oracle_has):
        tiers = self.tiers(findings)
        self.assertEqual(bool(tiers['input']), input_has, sorted(tiers['input'])[:3])
        self.assertEqual(bool(tiers['oracle']), oracle_has, sorted(tiers['oracle'])[:3])

    def test_sealed_scenario_input_is_admitted_by_digest(self):
        root, base = self.sealed()
        self.assertTrue(ID_PATTERN.search(prose('x')), 'the synthetic fixture must carry ID-shaped tokens')
        self.assertEqual(self.scan(root, base), [])

    def test_sealed_scenario_oracle_and_sheets_are_admitted_by_digest(self):
        root, base = self.sealed()
        findings = self.scan(root, base)
        self.assertEqual(self.tiers(findings), {'input': set(), 'oracle': set()})
        tracked = self.git(root, 'ls-files').stdout.split('\n')
        for relative in (VARIANT + 'oracle/check.py', VARIANT + 'oracle/data.json', VARIANT + 'GROUND-TRUTH.md',
                         SCENARIO + 'GROUND-TRUTH.md',
                         VARIANT + 'oracle/selftest/fell/final/docs/plans/' + WORKSPACE + '/plan.md'):
            self.assertIn(relative, tracked)
            self.assertNotIn(relative, self.paths(findings))

    def test_sealed_admission_coexists_with_typed_scenario_roles(self):
        root, base = self.repository()
        scenario, variant, workspace = 's65-migration-replay', 'v1', 'loyalty-cents'
        prefix = 'eval/scenarios/' + scenario + '/variants/' + variant + '/'
        documents = prefix + 'input/fixture/docs/plans/' + workspace + '/'
        board = ('| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
                 '| ' + TASK + ' | Synthetic work | tasks/' + TASK + '-' + workspace + '.md | none | In progress | — |\n')
        self.write(root, prefix + 'input/task.md', 'Do the synthetic work.\n')
        self.write(root, documents + 'task-board.md', board)
        self.write(root, documents + 'history.md', '- In flight: ' + TASK + ', synthetic work underway\n')
        self.write(root, documents + 'tasks/' + TASK + '-' + workspace + '.md', '# Task ' + TASK + ' — Synthetic work\n')
        self.write(root, prefix + 'GROUND-TRUTH.md', 'A sheet without any token.\n')
        hidden = prefix + 'hidden/test_b_board_history.py'
        self.write(root, hidden, '# ' + prose('a hidden check'))

        def index(with_digest):
            record = self.entry(root, scenario, variant, fixture_digest=with_digest, oracle_digest=False)
            if with_digest is False:
                del record['variants'][0]['fixture_sha256']
            self.index(root, record)
            self.git(root, 'add', '-A')

        index(False)  # an index without digests fails closed: the typed roles alone admit the board files
        findings = self.scan(root, base)
        self.assertEqual({p for p in self.paths(findings) if p.startswith(prefix + 'input/')}, set())
        self.assertIn(hidden, self.paths(findings))
        extra = documents + 'notes.md'
        self.write(root, extra, prose('free notes'))
        index(False)
        self.assertIn(extra, self.paths(self.scan(root, base)))
        index(True)  # the matching digest admits the input tree, including the untyped file
        findings = self.scan(root, base)
        self.assertEqual({p for p in self.paths(findings) if p.startswith(prefix + 'input/')}, set())
        self.assertIn(hidden, self.paths(findings))  # hidden/ never depended on the input digest

    def test_edited_fixture_loses_the_whole_input_admission(self):
        root, base = self.sealed()
        edited = INPUT + DOCS + 'history.md'
        with open(root / edited, 'a', encoding='utf-8') as handle:
            handle.write(prose('an edit'))
        self.git(root, 'add', edited)
        findings = self.scan(root, base)
        self.assertIn(edited, self.paths(findings))
        self.assertIn(INPUT + DOCS + 'plan.md', self.paths(findings))  # an untouched file of the same tree
        self.assertTierFindings(findings, True, False)

    def test_unstaged_fixture_edit_is_not_admitted(self):
        root, base = self.sealed()
        edited = INPUT + DOCS + 'history.md'
        with open(root / edited, 'a', encoding='utf-8') as handle:
            handle.write(prose('an unstaged edit'))
        findings = self.scan(root, base)
        self.assertIn(edited, self.paths(findings))
        self.assertIn(INPUT + DOCS + 'plan.md', self.paths(findings))

    def test_changed_index_digest_removes_admission(self):
        root, base = self.sealed()
        digest = check_index.mapping_digest(self.input_mapping(root))
        flipped = digest[:-1] + ('0' if digest[-1] != '0' else '1')
        self.reindex(root, fixture_digest=flipped)
        findings = self.scan(root, base)
        self.assertIn(INPUT + DOCS + 'plan.md', self.paths(findings))
        self.assertTierFindings(findings, True, False)

    def test_missing_or_null_digest_fails_closed(self):
        root, base = self.sealed()
        self.reindex(root, fixture_digest=False)
        self.assertTierFindings(self.scan(root, base), True, False)
        record = self.entry(root)
        del record['variants'][0]['fixture_sha256']
        self.index(root, record)
        self.git(root, 'add', '-A')
        self.assertTierFindings(self.scan(root, base), True, False)
        self.reindex(root, stageable=False)
        self.assertTierFindings(self.scan(root, base), True, False)

    def test_non_blind_entry_is_not_admitted(self):
        root, base = self.sealed()
        self.reindex(root, blind=False)
        self.assertTierFindings(self.scan(root, base), True, True)

    def test_index_path_must_be_the_variant_input_root(self):
        root, base = self.sealed()
        other = INPUT.replace('/' + VID + '/', '/v2/').rstrip('/')
        copied = root / other
        for source in sorted((root / INPUT).rglob('*')):
            if source.is_file():
                self.write(root, other + '/' + source.relative_to(root / INPUT).as_posix(), source.read_text(encoding='utf-8'))
        for path in (other, SCENARIO.rstrip('/'), 'docs/notes'):
            with self.subTest(path=path):
                self.reindex(root, path=path)
                self.assertIn(INPUT + DOCS + 'plan.md', self.paths(self.scan(root, base)))
        self.assertTrue(copied.is_dir())

    def test_sealed_bytes_outside_the_scenario_tree_are_findings(self):
        root, base = self.sealed()
        plan = (root / (INPUT + DOCS + 'plan.md')).read_text(encoding='utf-8')
        elsewhere = 'docs/notes/plan.md'
        other = 'eval/scenarios/s98-unindexed/variants/v1/input/fixture/plan.md'
        self.write(root, elsewhere, plan)
        self.write(root, other, plan)
        self.git(root, 'add', '-A')
        found = self.paths(self.scan(root, base))
        self.assertLessEqual({elsewhere, other}, found)
        self.assertNotIn(INPUT + DOCS + 'plan.md', found)

    def test_oracle_tamper_loses_the_oracle_tier_only(self):
        root, base = self.sealed()
        check = VARIANT + 'oracle/check.py'
        original = (root / check).read_text(encoding='utf-8')
        with open(root / check, 'a', encoding='utf-8') as handle:
            handle.write('# ' + prose('tamper'))
        self.git(root, 'add', check)
        findings = self.scan(root, base)
        self.assertTierFindings(findings, False, True)
        self.assertLessEqual({VARIANT + 'oracle/data.json', VARIANT + 'GROUND-TRUTH.md', SCENARIO + 'GROUND-TRUTH.md'},
                             self.paths(findings))
        self.write(root, check, original)
        self.git(root, 'add', check)
        self.assertEqual(self.scan(root, base), [])
        sheet = SCENARIO + 'GROUND-TRUTH.md'
        with open(root / sheet, 'a', encoding='utf-8') as handle:
            handle.write(prose('a sheet edit'))
        self.git(root, 'add', sheet)
        findings = self.scan(root, base)
        self.assertTierFindings(findings, False, True)
        self.assertIn(VARIANT + 'oracle/check.py', self.paths(findings))

    def test_null_oracle_digest_with_an_oracle_directory_is_not_admitted(self):
        root, base = self.sealed()
        self.reindex(root, oracle_digest=None)
        self.assertTierFindings(self.scan(root, base), False, True)

    def test_symlink_in_a_sealed_tree_blocks_admission(self):
        root, base = self.sealed()
        target = root / (INPUT + DOCS + 'history.md')
        target.unlink()
        target.symlink_to('plan.md')
        self.reindex(root)
        findings = self.scan(root, base)
        self.assertIn(INPUT + DOCS + 'plan.md', self.paths(findings))

    def test_initiative_slug_inside_a_sealed_fixture_is_still_a_finding(self):
        root, base = self.sealed()
        line = INPUT + DOCS + 'plan.md'
        with open(root / line, 'a', encoding='utf-8') as handle:
            handle.write('Notes for ' + SLUG + ' without any identifier.\n')
        self.reindex(root)  # the recorded digest now matches the edited tree
        findings = self.scan(root, base)
        self.assertEqual([(item.path, item.kind) for item in findings], [(line, 'initiative-slug')])

    def test_run_id_shaped_actor_strings_are_findings(self):
        root, base = self.sealed()
        actor = '2026-10-01-s1/' + 'T' + '-02/trap-author/1'
        record = self.entry(root)
        record['authored']['actors'] = [actor]
        self.index(root, record)
        self.write(root, SCENARIO + 'authored.json', json.dumps({'actors': [actor], 'blind': True}) + '\n')
        self.git(root, 'add', '-A')
        found = self.paths(self.scan(root, base))
        self.assertLessEqual({'eval/scenarios/INDEX.json', SCENARIO + 'authored.json'}, found)

    def test_unreadable_index_fails_closed(self):
        root, base = self.sealed()
        self.write(root, 'eval/scenarios/INDEX.json', '{"schema": "tackle-scenario-index/1", "scenarios": [')
        self.git(root, 'add', '-A')
        findings = self.scan(root, base)
        self.assertTierFindings(findings, True, True)


if __name__ == '__main__':
    unittest.main()
