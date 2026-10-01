"""Exercise the real added-line consumer over isolated Git repositories."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'eval/rules'))
from committed_text import (CommittedTextScanError, Finding, ID_PATTERN, format_findings,
                            scan_committed_text)


def source_line(relative, digest):
    for raw in (REPO / relative).read_bytes().splitlines():
        if hashlib.sha256(raw).hexdigest() == digest:
            line = raw.decode('utf-8', 'surrogateescape')
            if not ID_PATTERN.search(line):
                raise AssertionError('sealed fingerprint has no ID token: ' + relative)
            return line
    raise AssertionError('sealed source fingerprint missing: ' + relative)


class CommittedTextTests(unittest.TestCase):
    def repository(self, tracked=()):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name).resolve() / 'repo'
        root.mkdir()
        self.git(root, 'init', '-q', '-b', 'main')
        self.git(root, 'config', 'user.name', 'Tackle fixture')
        self.git(root, 'config', 'user.email', 'tackle-fixture@example.invalid')
        (root / 'README.md').write_text('base\n', encoding='utf-8')
        for relative in tracked:
            self.write(root, relative, 'base\n')
        self.git(root, 'add', '-A')
        self.git(root, 'commit', '-q', '-m', 'base')
        base = self.git(root, 'rev-parse', 'HEAD').stdout.strip()
        self.addCleanup(temporary.cleanup)
        return root, base

    def git(self, root, *args):
        env = dict(os.environ)
        env['GIT_CONFIG_NOSYSTEM'] = '1'
        env['GIT_CONFIG_GLOBAL'] = os.devnull
        result = subprocess.run(['git', '-C', str(root)] + list(args), capture_output=True,
                                text=True, env=env, check=False)
        if result.returncode:
            self.fail('fixture git command failed: git ' + ' '.join(args))
        return result

    def write(self, root, relative, text):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def scan(self, root, base, slug='sample-workspace'):
        return scan_committed_text(root, base, slug)

    def test_every_class_case_hyphen_and_width_is_rejected(self):
        root, base = self.repository()
        tokens = []
        for upper in 'PTDQRCMF':
            for letter in (upper, upper.lower()):
                for hyphen in ('', '-'):
                    for width in range(1, 4):
                        tokens.append(letter + hyphen + ('7' * width))
        self.write(root, 'outside-brief/matrix.txt', ''.join(item + '\n' for item in tokens))
        self.git(root, 'add', 'outside-brief/matrix.txt')

        findings = self.scan(root, base)
        self.assertEqual(len(tokens), 96)
        self.assertEqual({item.token for item in findings}, set(tokens))
        self.assertEqual({item.path for item in findings}, {'outside-brief/matrix.txt'})

    def test_identifier_boundaries_and_valid_domain_text_are_accepted(self):
        root, base = self.repository()
        standalone = 'P' + '-1'
        long_value = 'P' + '1234'
        timestamp = '2026-09-29' + 'T' + '00:00:00'
        embedded = 'prefix' + standalone + 'suffix'
        underscore = '_' + standalone + '_'
        identifier = 'T' + '03_AWK_INVOCATIONS'
        text = '\n'.join([
            embedded, underscore, 'x' + standalone, standalone + 'x',
            long_value, timestamp, identifier, 'R-EVID-01', 'R-COMM-03',
        ]) + '\n'
        self.write(root, 'valid.txt', text)
        self.git(root, 'add', 'valid.txt')
        self.assertEqual(self.scan(root, base), [])

    def test_slug_match_requires_the_complete_slug_boundary(self):
        root, base = self.repository()
        slug = 'tackle' + '-9.0.1'
        extended = 'tackle' + '-9.0.10'
        text = 'ordinary ' + slug + '.\n' + 'x' + slug + '\n' + extended + '\n'
        self.write(root, 'slug.txt', text)
        self.git(root, 'add', 'slug.txt')
        findings = self.scan(root, base, slug)
        self.assertEqual([(item.kind, item.token) for item in findings], [('initiative-slug', slug)])

    def test_diff_includes_committed_staged_unstaged_and_out_of_scope_additions(self):
        root, base = self.repository(('committed.txt', 'staged.txt', 'unstaged.txt',
                                      'outside-brief/tracked.txt'))
        committed_id = 'D' + '-3'
        staged_id = 'F' + '14'
        unstaged_id = 'Q' + '-1'
        outside_id = 'C' + '2'
        untracked_id = 'M' + '1'
        self.write(root, 'committed.txt', committed_id + '\n')
        self.git(root, 'add', 'committed.txt')
        self.git(root, 'commit', '-q', '-m', 'later committed addition')
        self.write(root, 'staged.txt', staged_id + '\n')
        self.write(root, 'outside-brief/tracked.txt', outside_id + '\n')
        self.git(root, 'add', 'staged.txt', 'outside-brief/tracked.txt')
        self.write(root, 'unstaged.txt', unstaged_id + '\n')
        self.write(root, 'untracked.txt', untracked_id + '\n')

        findings = self.scan(root, base)
        self.assertEqual({item.token for item in findings},
                         {committed_id, staged_id, unstaged_id, outside_id})
        self.assertNotIn('untracked.txt', {item.path for item in findings})

    def test_git_base_failure_is_an_error(self):
        root, _ = self.repository()
        with self.assertRaisesRegex(CommittedTextScanError, 'git diff failed'):
            self.scan(root, 'missing-base')

    def test_typed_values_pass_but_same_ids_in_prose_fail(self):
        root, base = self.repository()
        case_id = 'c' + '1'
        upper_case_id = 'C' + '1'
        event_id = 't' + '1'
        request_id = 'r' + '2'
        board_id = 'P' + '-1'
        decision_id = 'D' + '-1'
        milestone_id = 'M' + '1'
        dependency_id = 'd' + '1'
        context_id = 'c' + '1'
        samples = {
            'eval/rules/fixtures/build.py': (
                "def build_gate(out):\n" +
                "    bases['" + case_id + "-add-x'] = gate_repo(\n" +
                "        out, '" + case_id + "-add-x', base, candidate)"),
            'eval/tests/tooling/rules/test_ledger.py': (
                "def probe(self):\n" +
                "    result = gate(self.root('" + case_id + "-add-x'), GATE_BASES['" +
                case_id + "-add-x'])"),
            'eval/tests/tooling/behavior/judges/resume/test_fixtures.py': (
                "        ('" + event_id + "', 'Read', {'file_path': BOARD}),"),
            'eval/tests/tooling/behavior/harness/test_subagent.py': (
                "            tool_row('tu2', 'Bash', {'command': 'echo'}, request_id='" +
                request_id + "'), result_row('tu2')"),
            'eval/tests/tooling/maintaining/field-report/test_unclosed_fence.py': (
                '| ' + board_id + ' | Draft |'),
            'eval/tests/tooling/validation-integrity/test_fields.py': (
                '"tasks/T-A.md": "## Acceptance <!-- SEALED: ' + decision_id + ' -->\\n"'),
            'eval/tests/product/lint/rows/test_workspace_shapes.py': (
                "        self.write('decisions.md', '## " + decision_id + " — approved\\n')"),
            'eval/status/benchmark.py': (
                '    scope = {"tasks": ["T-A"], "requirements": ["RA"], "milestone": "' + milestone_id + '"}'),
            'eval/tests/product/status/test_context.py': (
                '        self.scope = {"tasks": ["T-A"], "requirements": ["RA"], "milestone": "' +
                milestone_id + '"}'),
            'eval/tests/product/templates/test_template_drift.py': (
                "                                                          dict(contract='" + context_id +
                "', source='s1', configuration='cfg1', dependencies='" + dependency_id + "',"),
        }
        for relative, line in samples.items():
            self.write(root, relative, line + '\n')
        self.write(root, 'eval/rules/fixtures/build.py',
                   samples['eval/rules/fixtures/build.py'] +
                   "\n    bases['" + upper_case_id + "-add-x'] = gate_repo(\n" +
                   "        out, '" + upper_case_id + "-add-x', base, candidate)\n")
        self.write(root, 'eval/tests/tooling/rules/test_ledger.py',
                   samples['eval/tests/tooling/rules/test_ledger.py'] +
                   "\n    result = gate(self.root('" + case_id + "-add-x'), GATE_BASES['" +
                   case_id + "-add-x'],\n                  'cohort')\n" +
                   "    result = gate(self.root('" + upper_case_id + "-add-x'), GATE_BASES['" +
                   upper_case_id + "-add-x'],\n                  'cohort')\n")
        self.git(root, 'add', '-A')
        self.assertEqual(self.scan(root, base), [])

        for relative, line in samples.items():
            self.write(root, relative, line + '\n# nearby prose ' + case_id + '\n')
        findings = self.scan(root, base)
        self.assertEqual({item.path for item in findings}, set(samples))

    def test_typed_exemptions_require_exact_executable_producers(self):
        root, base = self.repository()
        case_a, case_b = 'c' + '1', 'c' + '2'
        case_upper = 'C' + '1'
        outside_id, incomplete_id = 'c' + '4', 'c' + '5'
        event_id, request_id = 't' + '1', 'r' + '2'
        milestone_id, contract_id, dependency_id = 'm' + '1', 'c' + '3', 'd' + '4'
        board_id = 'p' + '-1'
        cases = {
            'eval/rules/fixtures/build.py': (
                "def build_gate(out):\n" +
                "    bases['" + case_a + "-add-x'] = gate_repo(out, '" + case_b + "-add-x', base, candidate)\n" +
                "    bases['" + case_upper + "-add-x'] = gate_repo(out, '" + case_a + "-add-x', base, candidate)\n" +
                "    bases['" + case_a + "-add-x'] = gate_repo(\n" +
                "        out, '" + case_b + "-add-x', base, candidate)\n" +
                "    bases['" + case_upper + "-add-x'] = gate_repo(\n" +
                "        out, '" + case_a + "-add-x', base, candidate)\n" +
                "    bases['" + case_a + "-add-x'] = gate_repo(\n" +
                "        out, '" + case_a + "-add-x', '" + outside_id + "-outside-add-x')"),
            'eval/tests/tooling/rules/test_ledger.py': (
                "def probe(self):\n" +
                "    result = gate(self.root('" + case_a + "-add-x'), GATE_BASES['" +
                case_b + "-add-x'])\n" +
                "    result = gate(self.root('" + case_upper + "-add-x'), GATE_BASES['" +
                case_a + "-add-x'])\n" +
                "    result = gate(self.root('" + case_a + "-add-x'), GATE_BASES['" +
                case_b + "-add-x'],\n                  'cohort')\n" +
                "    result = gate(self.root('" + case_upper + "-add-x'), GATE_BASES['" +
                case_a + "-add-x'],\n                  'cohort')\n" +
                "    result = gate(self.root('" + case_a + "-add-x'), GATE_BASES['" +
                case_a + "-add-x'], '" + outside_id + "-outside-add-x')"),
            'eval/tests/tooling/behavior/judges/resume/test_fixtures.py': (
                "        # ('" + event_id + "', 'Read', {'file_path': BOARD})"),
            'eval/tests/tooling/behavior/harness/test_subagent.py': (
                "            # request_id='" + request_id + "'"),
            'eval/status/benchmark.py': (
                '    # scope = {"tasks": ["T-A"], "requirements": ["RA"], "milestone": "' + milestone_id + '"}'),
            'eval/tests/product/status/test_context.py': (
                '        # self.scope = {"tasks": ["T-A"], "requirements": ["RA"], "milestone": "' +
                milestone_id + '"}'),
            'eval/tests/product/templates/test_template_drift.py': (
                "                                                          # dict(contract='" + contract_id +
                "', source='s1', configuration='cfg1', dependencies='" +
                dependency_id + "',"),
            'eval/tests/tooling/behavior/judges/resume/test_fixtures.py:invalid': (
                "        ('" + event_id + "', 'Read', {'file_path': BOARD}) prose " + board_id),
        }
        paths = {}
        for key, line in cases.items():
            relative = key.split(':', 1)[0]
            paths.setdefault(relative, []).append(line)
        for relative, lines in paths.items():
            self.write(root, relative, '\n'.join(lines) + '\n')
        self.git(root, 'add', '-A')

        findings = self.scan(root, base)
        self.assertEqual({item.path for item in findings}, set(paths))
        self.assertEqual({item.token for item in findings},
                         {case_a, case_b, case_upper, event_id, request_id, milestone_id,
                          contract_id, dependency_id, board_id, outside_id})

        from types import SimpleNamespace
        import committed_text as scanner
        probe_id, stale_id = 'c' + '1', 'c' + '2'
        source = ("def build_gate(out):\n" +
                  "    bases['" + probe_id + "-add-x'] = gate_repo(\n" +
                  "        out, '" + probe_id + "-add-x', base, candidate)\n")
        source_lines = source.splitlines()
        mapped = scanner._build_gate_typed_spans(source)
        stale_text = "        out, '" + stale_id + "-add-x', base, candidate)"
        stale = SimpleNamespace(line=3, text=stale_text,
                                digest=scanner._sha_line(stale_text))
        exact_text = source_lines[2]
        exact = SimpleNamespace(line=3, text=exact_text,
                                digest=scanner._sha_line(exact_text))
        self.assertEqual(scanner._build_gate_spans_for_added_line(
            stale, source_lines, mapped), ())
        self.assertEqual(scanner._build_gate_spans_for_added_line(
            exact, source_lines, mapped), mapped[3])

        ledger_source = ("def probe(self):\n" +
                         "    result = gate(self.root('" + probe_id + "-add-x'), GATE_BASES['" +
                         probe_id + "-add-x'],\n                  'cohort')\n")
        ledger_lines = ledger_source.splitlines()
        ledger_mapped = scanner._ledger_gate_typed_spans(ledger_source)
        ledger_exact_text = ledger_lines[1]
        ledger_stale_text = ledger_exact_text.replace(probe_id, stale_id, 1)
        ledger_stale = SimpleNamespace(line=2, text=ledger_stale_text,
                                       digest=scanner._sha_line(ledger_stale_text))
        ledger_exact = SimpleNamespace(line=2, text=ledger_exact_text,
                                       digest=scanner._sha_line(ledger_exact_text))
        self.assertEqual(scanner._build_gate_spans_for_added_line(
            ledger_stale, ledger_lines, ledger_mapped), ())
        self.assertEqual(scanner._build_gate_spans_for_added_line(
            ledger_exact, ledger_lines, ledger_mapped), ledger_mapped[2])

        self.write(root, 'eval/rules/fixtures/build.py',
                   "def build_gate(out):\n" +
                   "    bases['" + incomplete_id + "-add-x'] = gate_repo(\n")
        findings = self.scan(root, base)
        self.assertEqual({item.token for item in findings
                          if item.path == 'eval/rules/fixtures/build.py'}, {incomplete_id})

        self.write(root, 'eval/tests/tooling/rules/test_ledger.py',
                   "def probe(self):\n" +
                   "    result = gate(self.root('" + incomplete_id + "-add-x'),\n")
        findings = self.scan(root, base)
        self.assertEqual({item.token for item in findings
                          if item.path == 'eval/tests/tooling/rules/test_ledger.py'}, {incomplete_id})

        document_targets = {
            'eval/tests/tooling/maintaining/field-report/test_unclosed_fence.py': {32, 33, 38, 39, 58},
            'eval/tests/product/lint/rows/test_workspace_shapes.py': {181},
            'eval/tests/tooling/validation-integrity/test_fields.py': {119, 121},
        }
        document_root, document_base = self.repository()
        originals = {relative: (REPO / relative).read_text(encoding='utf-8')
                     for relative in document_targets}
        for relative, source in originals.items():
            self.write(document_root, relative, source)
        self.git(document_root, 'add', '-A')
        document_findings = self.scan(document_root, document_base)
        self.assertFalse([(item.path, item.line) for item in document_findings
                          if item.line in document_targets.get(item.path, ())])

        document_path = 'eval/tests/tooling/validation-integrity/test_fields.py'
        doc_lines = originals[document_path].splitlines()
        doc_spans = scanner._document_fixture_typed_spans(document_path, originals[document_path])
        exact_line = doc_lines[118]
        exact_document = SimpleNamespace(line=119, text=exact_line,
                                         digest=scanner._sha_line(exact_line))
        other_decision = 'D' + '-3'
        stale_line = exact_line + ' # ' + other_decision
        stale_document = SimpleNamespace(line=119, text=stale_line,
                                         digest=scanner._sha_line(stale_line))
        self.assertEqual(scanner._build_gate_spans_for_added_line(
            exact_document, doc_lines, doc_spans), doc_spans[119])
        self.assertEqual(scanner._build_gate_spans_for_added_line(
            stale_document, doc_lines, doc_spans), ())

        def has_finding(relative, line, token):
            return any(item.path == relative and item.line == line and item.token == token
                       for item in self.scan(document_root, document_base))

        fence_path = 'eval/tests/tooling/maintaining/field-report/test_unclosed_fence.py'
        board_other = 'P' + '-3'
        lines = originals[fence_path].splitlines()
        lines[31] += ' # nearby prose ' + board_other
        self.write(document_root, fence_path, '\n'.join(lines) + '\n')
        self.assertTrue(has_finding(fence_path, 32, board_other))
        self.write(document_root, fence_path, originals[fence_path])
        self.write(document_root, fence_path, originals[fence_path].replace(
            'self.field_report.detect_bucket', 'self.field_report.other'))
        self.assertTrue(has_finding(fence_path, 32, 'P' + '-1'))
        self.write(document_root, fence_path, originals[fence_path].replace(
            'self.field_report.count_tasks', 'self.field_report.other'))
        self.assertTrue(has_finding(fence_path, 38, 'T' + '-1'))
        self.write(document_root, fence_path, originals[fence_path].replace(
            'self.field_report.detect_bucket', 'self.detect_bucket'))
        self.assertTrue(has_finding(fence_path, 32, 'P' + '-1'))
        self.write(document_root, fence_path, originals[fence_path].replace(
            'self.field_report.count_tasks', 'self.count_tasks'))
        self.assertTrue(has_finding(fence_path, 38, 'T' + '-1'))
        self.write(document_root, fence_path, originals[fence_path])
        open_fence = r'an example that never closes its fence\n'
        closed_fence = r'an example that never closes its fence\n```\n'
        self.write(document_root, fence_path,
                   originals[fence_path].replace(open_fence, closed_fence, 1))
        self.assertTrue(has_finding(fence_path, 32, 'P' + '-1'))
        self.write(document_root, fence_path, originals[fence_path].replace(
            "'task-board.md': valid_four", "'task-board.md': other", 1))
        self.assertTrue(has_finding(fence_path, 58, 'T' + '-1'))
        self.write(document_root, fence_path, originals[fence_path])

        workspace_path = 'eval/tests/product/lint/rows/test_workspace_shapes.py'
        self.write(document_root, workspace_path, originals[workspace_path].replace(
            'self.assert_pass(7)', 'self.assert_blocked(7)', 1))
        self.assertTrue(has_finding(workspace_path, 181, 'D' + '-1'))
        self.write(document_root, workspace_path, originals[workspace_path])

        seal_id = 'D' + '-1'
        self.write(document_root, document_path, originals[document_path].replace(
            '"missing seal: ' + seal_id + '"', '"missing seal: ' + other_decision + '"', 1))
        self.assertTrue(has_finding(document_path, 119, 'D' + '-2'))
        self.assertTrue(has_finding(document_path, 121, other_decision))
        self.write(document_root, document_path, originals[document_path])

        fixture_root, fixture_base = self.repository()
        fixture_prefixes = [
            'eval/lint/rows/fixtures/' + name + '/docs/plans/demo/'
            for name in ('pass-full', 'pass-full-5')
        ]
        fixture_sources = {}
        for prefix in fixture_prefixes:
            for name in ('task-board.md', 'resource-usage.md', 'history.md'):
                relative = prefix + name
                fixture_sources[relative] = (REPO / relative).read_text(encoding='utf-8')
                self.write(fixture_root, relative, fixture_sources[relative])
        consumer_path = 'eval/tests/product/lint/rows/test_lint_rows.py'
        self.write(fixture_root, consumer_path, (REPO / consumer_path).read_text(encoding='utf-8'))
        self.git(fixture_root, 'add', '-A')

        def fixture_ids(prefix):
            board = fixture_sources[prefix + 'task-board.md']
            return next(item.group('token') for line in board.splitlines() if 'Complete' in line
                        for item in ID_PATTERN.finditer(line))

        for prefix in fixture_prefixes:
            token = fixture_ids(prefix)
            for name in ('resource-usage.md', 'history.md'):
                relative = prefix + name
                findings = [item for item in self.scan(fixture_root, fixture_base)
                            if item.path == relative and item.token == token]
                expected = []
                self.assertEqual([(item.line, item.kind) for item in findings],
                                 [(line, 'workspace-id') for line in expected])

        for prefix in fixture_prefixes:
            ledger_path = prefix + 'resource-usage.md'
            original_ledger = fixture_sources[ledger_path]
            run_id = next(line.strip('|').split('|')[0].strip()
                          for line in original_ledger.splitlines() if '| finish |' in line)
            self.assertFalse(any(item.path == ledger_path and item.token == run_id
                                 for item in self.scan(fixture_root, fixture_base)))
            changed_id = 'r' + '2'
            self.write(fixture_root, ledger_path, original_ledger.replace(
                '| ' + run_id + ' |', '| ' + changed_id + ' |'))
            self.assertFalse(any(item.path == ledger_path and item.token == changed_id
                                 for item in self.scan(fixture_root, fixture_base)))
            self.write(fixture_root, ledger_path, original_ledger)
            self.write(fixture_root, ledger_path, original_ledger.replace(
                '| ' + run_id + ' | finish |', '| ' + changed_id + ' | finish |', 1))
            self.assertTrue(any(item.path == ledger_path and item.token == changed_id
                                for item in self.scan(fixture_root, fixture_base)))
            self.write(fixture_root, ledger_path, original_ledger)

        prefix = fixture_prefixes[0]
        task_id = fixture_ids(prefix)
        other_id = fixture_ids(fixture_prefixes[1])
        ledger_path = prefix + 'resource-usage.md'
        history_path = prefix + 'history.md'
        ledger = fixture_sources[ledger_path]
        trace = fixture_sources[history_path]
        self.write(fixture_root, ledger_path, ledger.replace(
            'reports/' + task_id + '-report.md', 'reports/' + other_id + '-report.md'))
        self.assertTrue(any(item.path == ledger_path and item.token == task_id
                            for item in self.scan(fixture_root, fixture_base)))
        self.write(fixture_root, ledger_path, ledger)
        appended_trace = trace + '\nNeighboring prose ' + task_id + '\n'
        appended_line = len(appended_trace.splitlines())
        self.write(fixture_root, history_path, appended_trace)
        self.assertTrue(any(item.path == history_path and item.line == appended_line and
                            item.token == task_id for item in self.scan(fixture_root, fixture_base)))
        self.write(fixture_root, history_path, trace)
        self.write(fixture_root, ledger_path,
                   ledger.replace('history.md#cycle-alpha', 'history.md#unlinked-event'))
        self.assertTrue(any(item.path == ledger_path and item.token == task_id
                            for item in self.scan(fixture_root, fixture_base)))
        self.write(fixture_root, ledger_path, ledger)
        self.write(fixture_root, history_path,
                   trace.replace('Task ID: ' + task_id, 'Task ID: ' + other_id))
        self.assertTrue(any(item.path == ledger_path and item.token == task_id
                            for item in self.scan(fixture_root, fixture_base)))
        self.write(fixture_root, history_path, trace)
        self.write(fixture_root, history_path, trace.replace(
            '- Work marked complete.', '- ' + task_id + ' complete.', 1))
        self.assertTrue(any(item.path == history_path and item.line == 9 and
                            item.token == task_id for item in self.scan(fixture_root, fixture_base)))
        self.write(fixture_root, history_path, trace)

        source_lines, mapped = scanner._lifecycle_fixture_typed_spans(fixture_root, ledger_path)
        actual_text = source_lines[-1]
        actual = SimpleNamespace(line=len(source_lines), text=actual_text,
                                 digest=scanner._sha_line(actual_text))
        stale_text = actual_text + ' # neighboring prose ' + other_id
        stale = SimpleNamespace(line=len(source_lines), text=stale_text,
                                digest=scanner._sha_line(stale_text))
        self.assertEqual(scanner._build_gate_spans_for_added_line(stale, source_lines, mapped), ())
        self.assertEqual(scanner._build_gate_spans_for_added_line(
            actual, source_lines, mapped), mapped[len(source_lines)])

        consumer = (REPO / consumer_path).read_text(encoding='utf-8')
        for detached in (
            consumer.replace('for fixture, base in PASSES:', 'for fixture, base in ():', 1),
            consumer.replace("self.assertEqual(verdict, 'PASS'", "self.assertEqual(verdict, 'FAIL'", 1),
            consumer.replace("('pass-full', None)", "('pass-full', 'other-base')", 1),
        ):
            self.write(fixture_root, consumer_path, detached)
            self.assertTrue(any(item.path == ledger_path and item.token == task_id
                                for item in self.scan(fixture_root, fixture_base)))
        self.write(fixture_root, consumer_path, consumer)

        lite = 'eval/lint/rows/fixtures/pass-lite/docs/plans/demo/'
        negative = 'eval/lint/rows/fixtures/fail-16-unsupported-lite/docs/plans/demo/resource-usage.md'
        for name in ('plan.md', 'resource-usage.md', 'history.md'):
            relative = lite + name
            self.write(fixture_root, relative, (REPO / relative).read_text(encoding='utf-8'))
        self.write(fixture_root, negative, (REPO / negative).read_text(encoding='utf-8'))
        self.git(fixture_root, 'add', '-A')
        lite_ledger = (REPO / (lite + 'resource-usage.md')).read_text(encoding='utf-8')
        lite_history = (REPO / (lite + 'history.md')).read_text(encoding='utf-8')
        lite_task = next(line.strip('|').split('|')[2].strip()
                         for line in lite_ledger.splitlines() if '| finish |' in line)
        for relative in (lite + 'resource-usage.md', lite + 'history.md', negative):
            findings = [item for item in self.scan(fixture_root, fixture_base)
                        if item.path == relative and item.token == lite_task]
            expected = []
            self.assertEqual([(item.line, item.kind) for item in findings],
                             [(line, 'workspace-id') for line in expected])
        self.write(fixture_root, lite + 'resource-usage.md', lite_ledger.replace(
            'reports/' + lite_task + '-report.md', 'reports/' + other_id + '-report.md'))
        self.assertTrue(any(item.path == lite + 'resource-usage.md' and item.token == lite_task
                            for item in self.scan(fixture_root, fixture_base)))
        self.write(fixture_root, lite + 'resource-usage.md', lite_ledger)
        self.write(fixture_root, lite + 'history.md',
                   lite_history.replace('Task ID: ' + lite_task, 'Task ID: ' + other_id, 1))
        self.assertTrue(any(item.path == lite + 'resource-usage.md' and item.token == lite_task
                            for item in self.scan(fixture_root, fixture_base)))
        self.write(fixture_root, lite + 'history.md', lite_history)
        self.write(fixture_root, lite + 'history.md', lite_history.replace(
            '- Work marked complete.', '- ' + lite_task + ' complete.', 1))
        self.assertTrue(any(item.path == lite + 'history.md' and item.line == 9 and
                            item.token == lite_task for item in self.scan(fixture_root, fixture_base)))
        self.write(fixture_root, lite + 'history.md', lite_history)
        self.write(fixture_root, consumer_path,
                   consumer.replace("('pass-lite', None)", "('pass-lite', 'other-base')", 1))
        self.assertTrue(any(item.path == lite + 'resource-usage.md' and item.token == lite_task
                            for item in self.scan(fixture_root, fixture_base)))
        self.write(fixture_root, consumer_path, consumer)
        self.write(fixture_root, lite + 'resource-usage.md', lite_ledger)

        coverage_path = 'eval/tests/product/lessons/test_coverage_table.py'
        coverage_fixture_path = 'eval/lessons/fixtures/coverage-lifecycle.md'
        coverage_source = (REPO / coverage_path).read_text(encoding='utf-8')
        coverage_fixture = (REPO / coverage_fixture_path).read_text(encoding='utf-8')
        self.write(fixture_root, coverage_path, coverage_source)
        self.write(fixture_root, coverage_fixture_path, coverage_fixture)
        self.git(fixture_root, 'add', '-A')
        first_finish = next(line for line in coverage_fixture.splitlines()
                            if 'Worker/01 | finish |' in line)
        coverage_task = first_finish.strip('|').split('|')[2].strip()
        coverage_line = next(number for number, line in enumerate(coverage_source.splitlines(), 1)
                             if "first_finish.replace('| " + coverage_task + " |'" in line)
        def coverage_findings(token):
            return [item for item in self.scan(fixture_root, fixture_base)
                    if item.path == coverage_path and item.line == coverage_line and item.token == token]
        self.assertEqual(coverage_findings(coverage_task), [])
        self.write(fixture_root, coverage_path, coverage_source.replace(
            "['tokens 3/5 (60%)', 'duration 1/5 (20%)']",
            "['tokens 3/5 (60%)', 'duration 2/5 (40%)']", 1))
        self.assertTrue(coverage_findings(coverage_task))
        self.write(fixture_root, coverage_path, coverage_source)
        oracle = ("                self.assertEqual(child.stdout.splitlines(),\n"
                  "                                 ['tokens 3/5 (60%)', 'duration 1/5 (20%)'])")
        self.assertEqual(coverage_source.count(oracle), 1)
        loop_anchor = '        for text in variants:'
        self.assertEqual(coverage_source.count(loop_anchor), 1)
        for detached in (
            coverage_source.replace(loop_anchor, '        variants = ()\n' + loop_anchor, 1),
            coverage_source.replace(loop_anchor,
                '        variants = list(variants)\n        variants.clear()\n' + loop_anchor, 1),
            coverage_source.replace(oracle, '                continue\n' + oracle, 1),
            coverage_source.replace(oracle,
                '                if False:\n' + oracle.replace('                self.',
                    '                    self.').replace('                                 [',
                    '                                     ['), 1),
        ):
            compile(detached, coverage_path, 'exec')
            self.write(fixture_root, coverage_path, detached)
            self.assertTrue(coverage_findings(coverage_task))
        self.write(fixture_root, coverage_path, coverage_source)

        alternate_source = coverage_source.replace("'| " + coverage_task + " |'",
                                                   "'| " + other_id + " |'", 1)
        alternate_fixture = coverage_fixture.replace('| ' + coverage_task + ' |',
                                                     '| ' + other_id + ' |')
        self.write(fixture_root, coverage_path, alternate_source)
        self.write(fixture_root, coverage_fixture_path, alternate_fixture)
        self.assertEqual(coverage_findings(other_id), [])
        self.write(fixture_root, coverage_path, coverage_source)
        self.assertTrue(coverage_findings(coverage_task))
        self.write(fixture_root, coverage_fixture_path, coverage_fixture)
        self.assertEqual(coverage_findings(coverage_task), [])

        # The indexed scenario model is a typed consumer, including reference overlays.
        # Build synthetic content; no protected scenario body is copied into this test.
        scenario_root, scenario_base = self.repository()
        task_id = 'T' + '-1'
        changed_id = 'T' + '-2'
        metric = 'p' + str(99)
        local_name = 'm' + str(2)
        scenario = 's65-migration-replay'
        variant = 'h1'
        prefix = 'eval/scenarios/' + scenario + '/variants/' + variant + '/'
        workspace = 'catalog-pricing'
        documents = prefix + 'input/fixture/docs/plans/' + workspace + '/'
        reference = prefix + 'reference/a/docs/plans/' + workspace + '/'
        board = ('| Task | What | Brief | Depends on | Status | Verification |\n'
                 '|---|---|---|---|---|---|\n'
                 '| ' + task_id + ' | Synthetic work | tasks/' + task_id + '-' + workspace +
                 '.md | none | In progress | — |\n')
        history = '- In flight: ' + task_id + ', synthetic work underway\n'
        task = '# Task ' + task_id + ' — Synthetic work\n'
        self.write(scenario_root, 'eval/scenarios/INDEX.json', json.dumps({'scenarios': [{
            'scenario_id': scenario, 'variants': [{'variant_id': variant, 'path': prefix + 'input',
                                                   'fixture': 'fixture', 'stageable': True}]}]}) + '\n')
        self.write(scenario_root, documents + 'task-board.md', board)
        self.write(scenario_root, documents + 'history.md', history)
        self.write(scenario_root, documents + 'tasks/' + task_id + '-' + workspace + '.md', task)
        self.write(scenario_root, reference + 'task-board.md', board.replace('In progress', 'Complete'))
        self.write(scenario_root, reference + 'history.md', history)
        self.write(scenario_root, prefix + 'GROUND-TRUTH.md',
                   '- `task-board.md`: the `' + task_id + '` row has a final Status cell.\n')
        staged = '# History\n' + history
        hidden = (
            'import unittest\n'
            'STAGED_HISTORY = ' + repr(staged) + '\n'
            'HISTORY = ' + repr('# History\n- In flight: ') + ' + "T" + ' +
            repr(task_id[1:] + ', synthetic work underway\n current') + '\n'
            'def newest(text):\n'
            '    if text.startswith(STAGED_HISTORY):\n'
            '        return text[len(STAGED_HISTORY):]\n'
            '    return text\n'
            'def middle(text):\n'
            '    return newest(text)\n'
            'def board_status_token(text):\n'
            '    for line in text.splitlines():\n'
            '        if line.strip().startswith("| ' + task_id + '"):\n'
            '            cells = [cell.strip() for cell in line.strip("|").split("|")]\n'
            '            return cells[4] if len(cells) > 4 else None\n'
            '    return None\n'
            'def parse_field(rest):\n'
            '    ' + local_name + ' = _COLON_RE.match(rest)\n'
            '    if not ' + local_name + ':\n'
            '        return None\n'
            '    tail = rest[' + local_name + '.end():]\n'
            '    ' + local_name + ' = _MARKUP_RE.match(tail)\n'
            '    if ' + local_name + ':\n'
            '        return tail[' + local_name + '.end():]\n'
            '    return tail\n'
            'class SyntheticTests(unittest.TestCase):\n'
            '    def test_history(self):\n'
            '        self.assertEqual(middle(HISTORY), " current")\n')
        hidden_path = prefix + 'hidden/test_b_board_history.py'
        self.write(scenario_root, hidden_path, hidden)
        alert_prefix = 'eval/scenarios/s66-notice-replay/variants/h1/'
        self.write(scenario_root, 'eval/scenarios/INDEX.json', json.dumps({'scenarios': [
            {'scenario_id': scenario, 'variants': [{'variant_id': variant, 'path': prefix + 'input',
                                                    'fixture': 'fixture', 'stageable': True}]},
            {'scenario_id': 's66-notice-replay', 'variants': [{'variant_id': 'h1',
                'path': alert_prefix + 'input', 'fixture': 'fixture', 'stageable': True}]}]}) + '\n')
        alert_docs = alert_prefix + 'input/fixture/docs/plans/status-alerts/'
        alert_board = board.replace(workspace, 'status-alerts')
        self.write(scenario_root, alert_docs + 'task-board.md', alert_board)
        alert_path = alert_prefix + 'input/fixture/alerts.json'
        alert_text = ('{\n  "alerts": [\n    {"id": "latency-spike",\n'
                      '     "message": "' + metric + ' latency monitor sample."\n    }\n  ]\n}\n')
        self.write(scenario_root, alert_path, alert_text)
        self.git(scenario_root, 'add', '-A')
        self.assertEqual(self.scan(scenario_root, scenario_base), [])

        def has_scenario_finding(relative, token):
            return any(item.path == relative and item.token == token
                       for item in self.scan(scenario_root, scenario_base))

        self.write(scenario_root, hidden_path,
                   hidden.replace('self.assertEqual(middle(HISTORY), " current")',
                                  'self.assertEqual(middle("current"), "current")'))
        self.assertFalse(has_scenario_finding(hidden_path, task_id))
        self.write(scenario_root, hidden_path,
                   hidden.replace('def newest(text):\n    if',
                                  'def newest(text):\n    return text\n    if'))
        self.assertTrue(has_scenario_finding(hidden_path, task_id))
        self.write(scenario_root, hidden_path,
                   hidden.replace('def test_history(self):\n        self.assertEqual',
                                  'def test_history(self):\n        return\n        self.assertEqual'))
        self.assertTrue(has_scenario_finding(hidden_path, task_id))
        self.write(scenario_root, hidden_path, hidden)

        board_path = documents + 'task-board.md'
        self.write(scenario_root, board_path, board + '# nearby prose ' + task_id + '\n')
        self.assertTrue(has_scenario_finding(board_path, task_id))
        self.write(scenario_root, board_path, board.replace('| ' + task_id + ' |',
                                                          '| ' + changed_id + ' |', 1))
        self.assertTrue(has_scenario_finding(board_path, changed_id))
        self.write(scenario_root, board_path, board)
        alternate = documents.replace(workspace, 'other-workspace') + 'task-board.md'
        self.write(scenario_root, alternate, board)
        self.git(scenario_root, 'add', alternate)
        self.assertTrue(has_scenario_finding(alternate, task_id))
        self.write(scenario_root, hidden_path, hidden.replace('self.assertEqual(middle(HISTORY), " current")',
                                                              'self.assertEqual(" current", " current")'))
        self.assertTrue(has_scenario_finding(hidden_path, task_id))
        self.write(scenario_root, hidden_path, hidden.replace('self.assertEqual(middle(HISTORY), " current")',
                                                              'middle(HISTORY); self.assertTrue(True)'))
        self.assertTrue(has_scenario_finding(hidden_path, task_id))
        self.write(scenario_root, hidden_path, hidden.replace('self.assertEqual(middle(HISTORY), " current")',
                                                              'self.assertTrue(True, middle(HISTORY))'))
        self.assertTrue(has_scenario_finding(hidden_path, task_id))
        loop_middle = ('def middle(text):\n'
                       '    result = []\n'
                       '    for item in [newest(text)]:\n'
                       '        result.append(item)\n'
                       '    return result[0]\n')
        self.write(scenario_root, hidden_path,
                   hidden.replace('def middle(text):\n    return newest(text)\n', loop_middle))
        self.assertFalse(has_scenario_finding(hidden_path, task_id))
        self.write(scenario_root, hidden_path, hidden)
        mixed_alert = json.loads(alert_text)
        mixed_alert['alerts'].append({'id': 'background-note', 'message': 'ordinary neighbor'})
        self.write(scenario_root, alert_path, json.dumps(mixed_alert, indent=2) + '\n')
        self.assertFalse(has_scenario_finding(alert_path, metric))
        zero_match = json.loads(json.dumps(mixed_alert))
        zero_match['alerts'][0]['id'] = 'background-note'
        self.write(scenario_root, alert_path, json.dumps(zero_match, indent=2) + '\n')
        self.assertTrue(has_scenario_finding(alert_path, metric))
        duplicate_match = json.loads(json.dumps(mixed_alert))
        duplicate_match['alerts'].append(dict(duplicate_match['alerts'][0]))
        self.write(scenario_root, alert_path, json.dumps(duplicate_match, indent=2) + '\n')
        self.assertTrue(has_scenario_finding(alert_path, metric))
        self.write(scenario_root, alert_path, alert_text.replace('"message"', '"notes"'))
        self.assertTrue(has_scenario_finding(alert_path, metric))
        for percentile in ('p' + str(95), 'p' + str(90)):
            self.write(scenario_root, alert_path, alert_text.replace(metric, percentile))
            self.assertFalse(has_scenario_finding(alert_path, percentile))
        self.write(scenario_root, alert_path,
                   alert_text.replace('latency monitor sample.',
                                      'latency monitor sample; ' + changed_id + '.'))
        self.assertTrue(has_scenario_finding(alert_path, changed_id))
        self.write(scenario_root, alert_path, alert_text.replace(metric, changed_id))
        self.assertTrue(has_scenario_finding(alert_path, changed_id))

    def test_formatted_findings_redact_matched_tokens(self):
        token = 'D' + '-1'
        path = 'eval/scenarios/synthetic/fixture.json'
        finding = Finding(path, 8, 'workspace-id', token, 'a' * 64)
        formatted = format_findings([finding])
        self.assertTrue(path + ':8: workspace-id' in formatted, 'formatted metadata omitted the safe path')
        self.assertTrue('sha256=' + 'a' * 64 in formatted, 'formatted metadata omitted the safe fingerprint')
        with self.assertRaises(AssertionError) as failure:
            self.assertEqual([finding], [], formatted)
        diagnostic = str(failure.exception)
        self.assertTrue(path in diagnostic, 'unittest diagnostic omitted the safe path')
        self.assertTrue('sha256=' + 'a' * 64 in diagnostic, 'unittest diagnostic omitted the safe fingerprint')
        if token in diagnostic:
            self.fail('unittest diagnostic echoed a protected token')

    def test_exact_historical_lines_are_path_and_fingerprint_bound(self):
        root, base = self.repository()
        records = [
            ('eval/cohorts/2026-09-candidate/manifest.json',
             'e49ff8f5adecd24af51e5ce4ea91c045726b19f7cd141d57773ea9cf09f5cf7b'),
            ('eval/cohorts/2026-09-candidate/smoke/manifest.json',
             'e49ff8f5adecd24af51e5ce4ea91c045726b19f7cd141d57773ea9cf09f5cf7b'),
            ('eval/run/card/README.md',
             '8fb8abed6fccd018a1106273a691fdf3b1490c1520b19fa70aba1d0a3262d3e4'),
            ('eval/tests/product/install/inventory/test_install.py',
             'b14cb937e6c531be4452c8f2ac3fd4653be15e2f8fc764e49bea5efbfaed2383'),
            ('eval/tests/tooling/rules/test_ledger.py',
             '5db5a1b03950ab39b133b0f73f3091448219619f9f603dee194fe1a1f634d802'),
            ('eval/tests/tooling/validation-integrity/test_dependency_and_scope_parsing.py',
             '4b8bc58493e73c9f8659f0ccceb625f888f088906fc50a262867671d41e96829'),
        ]
        for relative, digest in records:
            self.write(root, relative, source_line(relative, digest) + '\n')
        self.git(root, 'add', '-A')
        self.assertEqual(self.scan(root, base), [])

        changed_manifest = self.write(root, records[0][0],
                                      source_line(records[0][0], records[0][1]).replace('decision_rule', 'other_rule') + '\n')
        findings = self.scan(root, base)
        self.assertIn(records[0][0], {item.path for item in findings})
        self.assertTrue(changed_manifest.is_file())

    def test_inherited_note_without_historical_git_proof_is_rejected(self):
        root, base = self.repository()
        digest = '3896f92f66de37480f7b52a44d13fd8038016a2a151c67ca6e56a025d745bbb0'
        relative = 'skills/tackle/references/guides/lint-spec.md'
        historical = subprocess.run(
            ['git', '-C', str(REPO), 'show', 'v9.0.0:references/guides/lint-spec.md'],
            capture_output=True, check=True, timeout=120).stdout
        self.assertEqual(hashlib.sha256(historical).hexdigest(),
                         '5aeab0c7be0715b8b3f61e9490a4809139b8beac9d4919c9643eade49f8a3b93')
        matching = [raw for raw in historical.splitlines()
                    if hashlib.sha256(raw).hexdigest() == digest]
        self.assertEqual(len(matching), 1)
        line = matching[0].decode('utf-8', 'surrogateescape')
        self.assertTrue(ID_PATTERN.search(line))
        self.write(root, relative, line + '\n')
        self.git(root, 'add', relative)
        findings = self.scan(root, base)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].path, relative)
        self.assertEqual(findings[0].kind, 'workspace-id')


if __name__ == '__main__':
    unittest.main()
