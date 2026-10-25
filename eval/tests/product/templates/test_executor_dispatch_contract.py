"""Public task-package and prepared-operation examples, exercised at their real boundaries."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from test_brief_template import structural_contract_shape  # noqa: E402

INSTALL = ROOT / 'skills/tackle'
TEMPLATE = INSTALL / 'references/task.tmpl.md'
DESIGN = INSTALL / 'references/guides/design-and-contract.md'
DECOMPOSE = INSTALL / 'references/guides/decompose-and-lint.md'
RUN = INSTALL / 'references/guides/run.md'
RUN_CARD = INSTALL / 'references/guides/run-card.md'
BEFORE = b'version=old\n'
AFTER = b'version=new\n'
BEFORE_SHA = '8c6160bb5bcc69379c1cda51ae821f80882e43ba4595ebb87aedeefdd3568da7'
AFTER_SHA = 'f22dd4f7d34eafaefce398dfc8903f787cba8b72ccbffbb57c46f97ab3c3b488'
REVISION = b'fixture-initial\n'
REVISION_SHA = 'f03203f10dbcce35daae7c0d0ac65cc923726a0d52dba2582e9a2a655093cc93'


def _anchor_section(text, anchor):
    lines = text.splitlines(keepends=True)
    explicit = re.compile(r'<a\s+id=["\']' + re.escape(anchor) + r'["\']\s*>\s*</a>', re.I)
    heading_id = re.compile(r'^\s{0,3}#{1,6}\s+.*\{#' + re.escape(anchor) + r'\}\s*$')
    slug_heading = re.compile(r'^\s{0,3}(#{1,6})\s+(.+?)\s*$')
    outside = set()
    fence = None
    fence_length = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip(' ')
        indent = len(line) - len(stripped)
        marker = re.match(r'^(`{3,}|~{3,})', stripped) if indent <= 3 else None
        if fence is None:
            if marker:
                fence, fence_length = marker.group(1)[0], len(marker.group(1))
                continue
            outside.add(i)
            continue
        if marker and marker.group(1)[0] == fence and len(marker.group(1)) >= fence_length:
            if not stripped[len(marker.group(1)):].strip():
                fence, fence_length = None, 0
        # Headings, HTML anchors, and comments inside code examples are body bytes.
    hits = [i for i, line in enumerate(lines) if i in outside and (explicit.search(line) or heading_id.search(line))]
    if not hits:
        for i, line in enumerate(lines):
            if i not in outside:
                continue
            match = slug_heading.match(line)
            if match:
                slug = re.sub(r'[^a-z0-9 -]', '', match.group(2).lower()).strip().replace(' ', '-')
                if slug == anchor:
                    hits.append(i)
    if len(hits) != 1:
        raise AssertionError(f'expected one public fragment {anchor!r}, found {len(hits)}')
    start = hits[0]
    heading = next((i for i in range(start, len(lines)) if i in outside and slug_heading.match(lines[i])), None)
    if heading is None:
        raise AssertionError(f'fragment {anchor!r} has no section heading')
    level = len(slug_heading.match(lines[heading]).group(1))
    end = len(lines)
    for i in range(heading + 1, len(lines)):
        match = slug_heading.match(lines[i])
        if i in outside and match and len(match.group(1)) <= level:
            end = i
            break
    return ''.join(lines[start:end])


def _fences(section):
    lines = section.splitlines()
    found = []
    i = 0
    while i < len(lines):
        opening = re.match(r'^\s{0,3}(`{3,}|~{3,})\s*([^\s`]*)?.*$', lines[i])
        if not opening:
            i += 1
            continue
        marker = opening.group(1)
        language = (opening.group(2) or '').strip().lower()
        body = []
        i += 1
        closing = re.compile(r'^\s{0,3}' + re.escape(marker[0]) + r'{' + str(len(marker)) + r',}\s*$')
        while i < len(lines) and not closing.match(lines[i]):
            body.append(lines[i])
            i += 1
        if i == len(lines):
            raise AssertionError('unclosed public code fence')
        found.append((language, '\n'.join(body) + ('\n' if body else '')))
        i += 1
    return found


def _labeled_read_examples(section=None):
    if section is None:
        section = _anchor_section(DESIGN.read_text(encoding='utf-8'), 'prepared-read-examples')
    result = {}
    for language, body in _fences(section):
        match = re.search(r'(?m)^\s*#\s*fixture-read:\s*(python|awk)\s*$', body, re.I)
        if match:
            label = match.group(1).lower()
            if label in result:
                raise AssertionError(f'duplicate {label} fixture-read example')
            code = body[:match.start()] + body[match.end():]
            result[label] = (language, code.strip() + '\n')
    if set(result) != {'python', 'awk'}:
        raise AssertionError(f'expected uniquely labeled Python and awk public examples; found {sorted(result)}')
    return result


def _prepared_operation_source():
    section = _anchor_section(DESIGN.read_text(encoding='utf-8'), 'prepared-operation-example')
    links = re.findall(r'\]\((\.\./\.\./scripts/prepared_job_example\.py)\)', section)
    if len(links) != 1:
        raise AssertionError(f'expected one public prepared-job script link, found {len(links)}')
    procedure = (DESIGN.parent / links[0]).resolve()
    if procedure != (INSTALL / 'scripts/prepared_job_example.py').resolve():
        raise AssertionError('prepared-job link does not resolve to the shipped example')
    return procedure.read_bytes().decode('utf-8')


def _fixture(root):
    (root / 'owned').mkdir(parents=True)
    (root / 'records').mkdir()
    (root / 'private').mkdir()
    (root / 'owned/revision.txt').write_bytes(REVISION)
    (root / 'owned/config.txt').write_bytes(BEFORE)
    (root / 'private/sentinel.txt').write_bytes(b'leave private bytes unchanged\n')


def _run_job(source, root, env=None):
    procedure = root / 'prepared_job.py'
    procedure.write_text(source, encoding='utf-8')
    child_env = dict(os.environ)
    child_env.pop('TACKLE_EXAMPLE_CHECK_FAIL', None)
    child_env.pop('TACKLE_EXAMPLE_INTERRUPT_AFTER_REPLACE', None)
    if env:
        child_env.update(env)
    return subprocess.run([sys.executable, '-I', str(procedure)], cwd=root, env=child_env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def _snapshot(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}


def _receipt(root):
    return json.loads((root / 'records/example-version-update.json').read_text(encoding='utf-8'))


class ExecutorDispatchContractTests(unittest.TestCase):
    def test_compiled_package_exposes_paths_formula_and_review_ownership(self):
        parser_control = '''## prepared-read-examples

```python
    # fixture-read: python
print("python")
```

~~~awk script
# fixture-read: awk
{ print }
~~~

## Following section
outside the fragment
'''
        control_section = _anchor_section(parser_control, 'prepared-read-examples')
        self.assertNotIn('outside the fragment', control_section)
        self.assertEqual(set(_labeled_read_examples(control_section)), {'python', 'awk'})
        self.assertIn('print("python")', _labeled_read_examples(control_section)['python'][1])
        with self.assertRaisesRegex(AssertionError, 'duplicate|expected uniquely labeled'):
            _labeled_read_examples(control_section.replace('# fixture-read: awk', '# fixture-read: python'))
        with self.assertRaisesRegex(AssertionError, 'expected uniquely labeled'):
            _labeled_read_examples(control_section.replace('# fixture-read: awk\n', ''))

        template = TEMPLATE.read_text(encoding='utf-8')
        self.assertTrue(structural_contract_shape(template), 'the existing compiled-brief shape remains usable')
        compact = ' '.join(template.split())
        missing = [token for token in ('Execution context', 'repository', 'checkout', 'workspace', 'records', 'cwd')
                   if token.lower() not in compact.lower()]
        self.assertEqual(missing, [], f'template context is missing fields: {missing}')

        design = DESIGN.read_text(encoding='utf-8')
        decompose = DECOMPOSE.read_text(encoding='utf-8')
        run = RUN.read_text(encoding='utf-8')
        for phrase in ('five passing of six', '83.333', 'complete successful child records',
                       'Python', 'awk', 'actual read consumers', 'named reviewer judgment'):
            self.assertIn(phrase.lower(), design.lower(), f'design recipe must state {phrase}')
        self.assertIn('design-and-contract.md', decompose)
        self.assertIn('preparation defect', run.lower())

        # The examples are extracted from their stable public fragment and run in a fresh cwd.
        examples = _labeled_read_examples()
        awk = shutil.which('awk')
        self.assertIsNotNone(awk, 'environment: awk is required for the declared consumer fixture')
        with tempfile.TemporaryDirectory(prefix='tackle-read-fixture-') as temporary:
            checkout = Path(temporary) / 'checkout'
            workspace = Path(temporary) / 'workspace'
            checkout.mkdir()
            workspace.mkdir()
            self.assertNotEqual(checkout.resolve(), workspace.resolve())
            fixture = checkout
            public_file = fixture / 'public/input.txt'
            public_file.parent.mkdir()
            public_file.write_bytes(b'read-ok\n')
            self.assertFalse(fixture.resolve().is_relative_to(ROOT.resolve()))

            python_language, python_code = examples['python']
            self.assertIn('public/input.txt', python_code)
            ast.parse(python_code)
            python_result = subprocess.run([sys.executable, '-I', '-c', python_code], cwd=fixture,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual((python_result.returncode, python_result.stdout), (0, b'read-ok\n'), python_result.stderr)
            public_file.write_bytes(b'read-next\n')
            python_again = subprocess.run([sys.executable, '-I', '-c', python_code], cwd=fixture,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual((python_again.returncode, python_again.stdout), (0, b'read-next\n'), python_again.stderr)

            awk_language, awk_code = examples['awk']
            awk_file = fixture / 'public/awk-program.awk'
            awk_file.write_text(awk_code, encoding='utf-8')
            awk_result = subprocess.run([awk, '-f', str(awk_file), 'public/input.txt'], cwd=fixture,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual((awk_result.returncode, awk_result.stdout), (0, b'read-next\n'), awk_result.stderr)
            self.assertEqual(awk_result.args[-1], 'public/input.txt')
            public_file.write_bytes(b'read-later\n')
            awk_again = subprocess.run([awk, '-f', str(awk_file), 'public/input.txt'], cwd=fixture,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual((awk_again.returncode, awk_again.stdout), (0, b'read-later\n'), awk_again.stderr)
            missing_input = subprocess.run([awk, '-f', str(awk_file), 'public/missing.txt'], cwd=fixture,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertNotEqual(missing_input.returncode, 0, 'missing actual input must fail')

    def test_prepared_job_example_preserves_effect_and_replay_boundaries(self):
        source = _prepared_operation_source()
        self.assertEqual(hashlib.sha256(BEFORE).hexdigest(), BEFORE_SHA)
        self.assertEqual(hashlib.sha256(AFTER).hexdigest(), AFTER_SHA)
        self.assertEqual(hashlib.sha256(REVISION).hexdigest(), REVISION_SHA)

        def fresh():
            temporary = tempfile.TemporaryDirectory(prefix='tackle-prepared-job-')
            self.addCleanup(temporary.cleanup)
            root = Path(temporary.name)
            _fixture(root)
            return root

        def assert_sentinels(root, before):
            after = _snapshot(root)
            for rel in ('owned/revision.txt', 'private/sentinel.txt'):
                self.assertEqual(after.get(rel), before.get(rel), rel)
            self.assertEqual(after.get('owned/config.txt'), AFTER if after.get('records/example-version-update.json') else before.get('owned/config.txt'))

        # Pristine application has exact bytes, hashes, receipt identity, and no unrelated effects.
        root = fresh()
        before = _snapshot(root)
        result = _run_job(source, root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((root / 'owned/config.txt').read_bytes(), AFTER)
        receipt = _receipt(root)
        self.assertEqual(receipt.get('operation_id'), 'example-version-update/1')
        self.assertEqual(receipt.get('revision'), 'fixture-initial')
        self.assertEqual(receipt.get('before_sha256'), BEFORE_SHA)
        self.assertEqual(receipt.get('after_sha256'), AFTER_SHA)
        self.assertEqual(receipt.get('apply_status'), 'applied')
        self.assertEqual(receipt.get('check_status'), 'passed')
        assert_sentinels(root, before)

        # A changed revision, missing anchor, or duplicate anchor stops before mutation.
        for name, revision, config in (
            ('revision-drift', b'fixture-drift\n', BEFORE),
            ('zero-anchor', REVISION, b'version=other\n'),
            ('duplicate-anchor', REVISION, b'version=old\nversion=old\n'),
        ):
            with self.subTest(case=name):
                root = fresh()
                (root / 'owned/revision.txt').write_bytes(revision)
                (root / 'owned/config.txt').write_bytes(config)
                before = _snapshot(root)
                result = _run_job(source, root)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(_snapshot(root).get('owned/config.txt'), before['owned/config.txt'])
                self.assertEqual(_snapshot(root).get('private/sentinel.txt'), before['private/sentinel.txt'])

        # A static receipt-parent alias must refuse before any target or exterior write.
        root = fresh()
        exterior_temporary = tempfile.TemporaryDirectory(prefix='tackle-prepared-exterior-')
        self.addCleanup(exterior_temporary.cleanup)
        exterior = Path(exterior_temporary.name)
        (exterior / 'sentinel.txt').write_bytes(b'exterior bytes remain unchanged\n')
        exterior_before = {str(path.relative_to(exterior)): path.read_bytes()
                           for path in exterior.rglob('*') if path.is_file()}
        (root / 'records').rmdir()
        (root / 'records').symlink_to(exterior, target_is_directory=True)
        before_alias = _snapshot(root)
        unsafe_parent = _run_job(source, root)
        self.assertNotEqual(unsafe_parent.returncode, 0, unsafe_parent.stdout)
        for rel in ('owned/config.txt', 'owned/revision.txt', 'private/sentinel.txt'):
            self.assertEqual((root / rel).read_bytes(), before_alias[rel], rel)
        exterior_after = {str(path.relative_to(exterior)): path.read_bytes()
                          for path in exterior.rglob('*') if path.is_file()}
        self.assertEqual(exterior_after, exterior_before)
        self.assertEqual(sorted(path.name for path in exterior.iterdir()), ['sentinel.txt'])
        self.assertTrue((root / 'records').is_symlink())

        # Full poststate is recognized before the consumed old anchor and preserves check evidence.
        root = fresh()
        first = _run_job(source, root)
        self.assertEqual(first.returncode, 0, first.stderr)
        saved_receipt = (root / 'records/example-version-update.json').read_bytes()
        saved_target = (root / 'owned/config.txt').stat()
        saved_target_bytes = (root / 'owned/config.txt').read_bytes()
        before_second = _snapshot(root)
        second = _run_job(source, root)
        self.assertEqual(second.returncode, 0, second.stderr)
        target_after = (root / 'owned/config.txt').stat()
        self.assertEqual((root / 'owned/config.txt').read_bytes(), saved_target_bytes)
        self.assertEqual((target_after.st_ino, target_after.st_mtime_ns),
                         (saved_target.st_ino, saved_target.st_mtime_ns), 'replay must not rewrite the target')
        receipt = _receipt(root)
        receipt_after = (root / 'records/example-version-update.json').read_bytes()
        if receipt_after == saved_receipt:
            output_records = []
            for line in second.stdout.splitlines():
                try:
                    parsed = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if isinstance(parsed, dict):
                    output_records.append(parsed)
            self.assertTrue(any(item.get('apply_status') == 'already-applied' for item in output_records),
                            'byte-identical receipt needs a structured already-applied result')
            self.assertEqual(receipt.get('check_status'), 'passed')
        else:
            self.assertEqual(receipt.get('apply_status'), 'already-applied')
            first_receipt = json.loads(saved_receipt.decode('utf-8'))
            comparable = dict(receipt)
            comparable.pop('apply_status', None)
            first_comparable = dict(first_receipt)
            first_comparable.pop('apply_status', None)
            self.assertEqual(comparable, first_comparable, 'only replay apply status may change')
            self.assertEqual(receipt.get('check_status'), 'passed')
        self.assertEqual(_snapshot(root).get('private/sentinel.txt'), before_second['private/sentinel.txt'])

        # Interrupted post-replacement state is reconciled with check-only; a concurrent edit then stops.
        root = fresh()
        before_interrupt = _snapshot(root)
        interrupted = _run_job(source, root, {'TACKLE_EXAMPLE_INTERRUPT_AFTER_REPLACE': '1'})
        self.assertNotEqual(interrupted.returncode, 0, interrupted.stdout)
        self.assertEqual((root / 'owned/config.txt').read_bytes(), AFTER)
        self.assertTrue((root / 'records/example-version-update.json').is_file())
        resume = _run_job(source, root)
        self.assertEqual(resume.returncode, 0, resume.stderr)
        resumed_receipt = _receipt(root)
        self.assertEqual(resumed_receipt.get('apply_status'), 'already-applied')
        self.assertEqual(resumed_receipt.get('check_status'), 'passed')
        self.assertEqual(_snapshot(root).get('private/sentinel.txt'), before_interrupt['private/sentinel.txt'])

        root = fresh()
        interrupted = _run_job(source, root, {'TACKLE_EXAMPLE_INTERRUPT_AFTER_REPLACE': '1'})
        self.assertNotEqual(interrupted.returncode, 0, interrupted.stdout)
        concurrent = AFTER + b'# concurrent owner bytes\n'
        (root / 'owned/config.txt').write_bytes(concurrent)
        conflict = _run_job(source, root)
        self.assertNotEqual(conflict.returncode, 0, conflict.stdout)
        self.assertEqual((root / 'owned/config.txt').read_bytes(), concurrent)

        # A child that prints PASS but exits 1 remains a failed required check.
        root = fresh()
        failing_child = _run_job(source, root, {'TACKLE_EXAMPLE_CHECK_FAIL': '1'})
        self.assertNotEqual(failing_child.returncode, 0, 'child exit must propagate through any wrapper')
        self.assertIn(b'PASS', failing_child.stdout)
        self.assertEqual((root / 'owned/config.txt').read_bytes(), AFTER)
        failed_receipt = _receipt(root)
        self.assertEqual(failed_receipt.get('check_status'), 'failed')
        self.assertNotIn('accepted', failed_receipt)

        for check_state in ('failed', 'unknown', None):
            with self.subTest(replay_check=check_state):
                replay_root = fresh()
                failed_once = _run_job(source, replay_root, {'TACKLE_EXAMPLE_CHECK_FAIL': '1'})
                self.assertNotEqual(failed_once.returncode, 0, failed_once.stdout)
                path = replay_root / 'records/example-version-update.json'
                replay_receipt = json.loads(path.read_text(encoding='utf-8'))
                if check_state is None:
                    replay_receipt.pop('check_status', None)
                else:
                    replay_receipt['check_status'] = check_state
                path.write_text(json.dumps(replay_receipt, sort_keys=True) + '\n', encoding='utf-8')
                target_before = (replay_root / 'owned/config.txt').read_bytes()
                result = _run_job(source, replay_root)
                self.assertEqual((replay_root / 'owned/config.txt').read_bytes(), target_before)
                after = _receipt(replay_root)
                self.assertNotEqual(after.get('check_status'), 'passed')
                self.assertNotIn('accepted', after)
                for line in result.stdout.splitlines():
                    try:
                        observation = json.loads(line)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                    if isinstance(observation, dict):
                        self.assertNotEqual(observation.get('check_status'), 'passed')
                        self.assertNotIn('accepted', observation)

        # The direct equivalent remains valid when it produces the exact target and child-check result.
        root = fresh()
        (root / 'owned/config.txt').write_bytes(AFTER)
        equivalent = subprocess.run(
            [sys.executable, '-I', '-c',
             'import pathlib,sys; sys.exit(0 if pathlib.Path("owned/config.txt").read_bytes()==bytes.fromhex("76657273696f6e3d6e65770a") else 1)'],
            cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual((equivalent.returncode, (root / 'owned/config.txt').read_bytes()), (0, AFTER), equivalent.stderr)

    def test_handback_clock_rule_preserves_observed_and_unknown_values(self):
        card = RUN_CARD.read_text(encoding='utf-8')
        run = RUN.read_text(encoding='utf-8')
        close = card.split('8. **Close.**', 1)[1].split('\n## State transitions', 1)[0]
        for phrase in ('finishAt', 'Run ID', 'observed', 'n/a', 'validation end'):
            self.assertIn(phrase.lower(), close.lower(), f'Close must cover {phrase}')
        detail = run.lower()
        self.assertIn('finishat', detail)
        self.assertIn('n/a with reason', detail)
        self.assertIn('validation end cannot substitute', detail)
        self.assertNotIn('estimated clock', close.lower())
