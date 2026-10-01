"""Scan the repository-wide tracked diff for workspace-shaped IDs and its initiative slug."""

from dataclasses import dataclass, field
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


ID_PATTERN = re.compile(
    r'(?<![A-Za-z0-9_])(?P<token>[PTDQRCMF]-?[0-9]{1,3})(?![A-Za-z0-9_])', re.IGNORECASE)
_CASE_ID = r'[PTDQRCMF]-?[0-9]{1,3}'
_HUNK = re.compile(r'^@@ .*?\+(\d+)(?:,(\d+))? @@')
_PREFLIGHT_BASE = '8b12ba7f11595adbbd13e06c1871e741155c6004'
_OLD_LINT_SPEC = 'references/guides/lint-spec.md'
_NEW_LINT_SPEC = 'skills/tackle/references/guides/lint-spec.md'
_INHERITED_LINE = '3896f92f66de37480f7b52a44d13fd8038016a2a151c67ca6e56a025d745bbb0'
_SEALED_COHORT_LINES = {
    'eval/cohorts/2026-09-candidate/manifest.json',
    'eval/cohorts/2026-09-candidate/smoke/manifest.json',
}
_STATIC_LINE_HASHES = {
    'eval/run/card/README.md': {'8fb8abed6fccd018a1106273a691fdf3b1490c1520b19fa70aba1d0a3262d3e4'},
    'eval/tests/product/install/inventory/test_install.py': {
        'b14cb937e6c531be4452c8f2ac3fd4653be15e2f8fc764e49bea5efbfaed2383'},
    'eval/tests/tooling/rules/test_ledger.py': {
        '5db5a1b03950ab39b133b0f73f3091448219619f9f603dee194fe1a1f634d802'},
    'eval/tests/tooling/validation-integrity/test_dependency_and_scope_parsing.py': {
        '4b8bc58493e73c9f8659f0ccceb625f888f088906fc50a262867671d41e96829'},
}
_SEALED_LINE_HASH = 'e49ff8f5adecd24af51e5ce4ea91c045726b19f7cd141d57773ea9cf09f5cf7b'


class CommittedTextScanError(RuntimeError):
    """The repository diff could not be inspected reliably."""


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str
    token: str = field(repr=False)
    line_sha256: str


@dataclass(frozen=True)
class _AddedLine:
    path: str
    line: int
    digest: str
    text: str = field(repr=False)


def _sha_line(text):
    return hashlib.sha256(text.encode('utf-8', 'surrogateescape')).hexdigest()


def _git_diff(repo, base_revision):
    command = ['git', '-C', str(repo), 'diff', base_revision, '--unified=0']
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                                errors='surrogateescape', check=False)
    except OSError as error:
        raise CommittedTextScanError('git diff could not run') from error
    if result.returncode != 0:
        raise CommittedTextScanError('git diff failed with exit %s' % result.returncode)
    return result.stdout


def _added_lines(diff):
    result = []
    path = None
    line_number = None
    for raw in diff.splitlines():
        if raw.startswith('+++ '):
            header = raw[4:]
            path = None if header == '/dev/null' else header[2:] if header.startswith('b/') else header
            line_number = None
            continue
        if raw.startswith('@@'):
            match = _HUNK.match(raw)
            line_number = int(match.group(1)) if match else None
            continue
        if raw.startswith('+') and not raw.startswith('+++'):
            if path is not None and line_number is not None:
                text = raw[1:]
                result.append(_AddedLine(path, line_number, _sha_line(text), text))
                line_number += 1
        elif raw.startswith(' ') and line_number is not None:
            line_number += 1
    return result


def _group_span(match, name):
    start, end = match.span(name)
    return start, end


def _python_statement(text):
    indentation = len(text) - len(text.lstrip(' \t'))
    source = 'if True:\n' + text if indentation else text
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    if indentation:
        if (len(tree.body) == 1 and isinstance(tree.body[0], ast.If) and
                len(tree.body[0].body) == 1):
            return tree.body[0].body[0]
        return None
    return tree.body[0] if len(tree.body) == 1 else None


def _string_id_span(text, node):
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return None
    source = text.encode('utf-8')
    start_byte, end_byte = node.col_offset, node.end_col_offset
    try:
        raw = source[start_byte:end_byte].decode('utf-8')
        start = len(source[:start_byte].decode('utf-8'))
    except UnicodeDecodeError:
        return None
    match = re.fullmatch(r"(?P<q>['\"])(?P<token>" + _CASE_ID + r")(?:-[^'\"]*)?(?P=q)", raw, re.I)
    if not match:
        return None
    return start + match.start('token'), start + match.end('token')


def _name(node, expected):
    return isinstance(node, ast.Name) and node.id == expected


def _attribute(node, owner, name):
    return (isinstance(node, ast.Attribute) and node.attr == name and
            isinstance(node.value, ast.Name) and node.value.id == owner)


def _build_gate_typed_spans(source):
    """Map exact linked IDs from complete gate fixture assignments by source line."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return {}
    lines = source.splitlines()
    spans_by_line = {}
    for statement in ast.walk(tree):
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target, call = statement.targets[0], statement.value
        if (not isinstance(target, ast.Subscript) or not _name(target.value, 'bases') or
                not isinstance(call, ast.Call) or not _name(call.func, 'gate_repo') or
                len(call.args) < 2 or not _name(call.args[0], 'out')):
            continue
        key, argument = target.slice, call.args[1]
        if (not isinstance(key, ast.Constant) or not isinstance(key.value, str) or
                not isinstance(argument, ast.Constant) or not isinstance(argument.value, str) or
                key.value != argument.value):
            continue
        if not (1 <= key.lineno <= len(lines) and 1 <= argument.lineno <= len(lines)):
            continue
        spans = (_string_id_span(lines[key.lineno - 1], key),
                 _string_id_span(lines[argument.lineno - 1], argument))
        if not all(spans):
            continue
        spans_by_line.setdefault(key.lineno, []).append(spans[0])
        spans_by_line.setdefault(argument.lineno, []).append(spans[1])
    return {line: tuple(spans) for line, spans in spans_by_line.items()}


def _ledger_gate_typed_spans(source):
    """Map exact same-key gate fixture calls by complete source line."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return {}
    lines = source.splitlines()
    spans_by_line = {}
    for statement in ast.walk(tree):
        if (not isinstance(statement, ast.Assign) or len(statement.targets) != 1 or
                not _name(statement.targets[0], 'result') or
                not isinstance(statement.value, ast.Call) or
                not _name(statement.value.func, 'gate') or len(statement.value.args) < 2):
            continue
        root_call, lookup = statement.value.args[:2]
        if (not isinstance(root_call, ast.Call) or
                not _attribute(root_call.func, 'self', 'root') or len(root_call.args) != 1 or
                not isinstance(root_call.args[0], ast.Constant) or
                not isinstance(root_call.args[0].value, str) or
                not isinstance(lookup, ast.Subscript) or not _name(lookup.value, 'GATE_BASES') or
                not isinstance(lookup.slice, ast.Constant) or
                not isinstance(lookup.slice.value, str) or
                root_call.args[0].value != lookup.slice.value):
            continue
        key, argument = root_call.args[0], lookup.slice
        if not (1 <= key.lineno <= len(lines) and 1 <= argument.lineno <= len(lines)):
            continue
        spans = (_string_id_span(lines[key.lineno - 1], key),
                 _string_id_span(lines[argument.lineno - 1], argument))
        if not all(spans):
            continue
        spans_by_line.setdefault(key.lineno, []).append(spans[0])
        spans_by_line.setdefault(argument.lineno, []).append(spans[1])
    return {line: tuple(spans) for line, spans in spans_by_line.items()}


def _build_gate_spans_for_added_line(line, source_lines, spans_by_line):
    if not isinstance(line.line, int) or not (1 <= line.line <= len(source_lines)):
        return ()
    source_text = source_lines[line.line - 1]
    if source_text != line.text or _sha_line(source_text) != line.digest:
        return ()
    return spans_by_line.get(line.line, ())


def _document_fixture_typed_spans(path, source):
    """Map only linked document-field and expected-diagnostic literals in known consumers."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return {}
    lines = source.splitlines()
    found = {}

    def function(name):
        hits = [node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
        return hits[0] if len(hits) == 1 else None

    def call(node, name):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != name:
            return False
        owner = node.func.value
        if name in {'detect_bucket', 'count_tasks'}:
            return isinstance(owner, ast.Attribute) and _attribute(owner, 'self', 'field_report')
        return _name(owner, 'self')

    def value(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = value(node.left), value(node.right)
            return left + right if left is not None and right is not None else None
        return None

    def parts(node):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = parts(node.left), parts(node.right)
            return left + right if left is not None and right is not None else None
        return [node]

    def one_id(node):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            return None
        matches = list(ID_PATTERN.finditer(node.value))
        return matches[0].group('token') if len(matches) == 1 else None

    def mark(node, expected, dest):
        if (not isinstance(node, ast.Constant) or not isinstance(node.value, str) or
                not (1 <= node.lineno <= node.end_lineno <= len(lines)) or
                one_id(node) != expected):
            return False
        raw = ast.get_source_segment(source, node)
        if raw is None:
            return False
        matches = list(ID_PATTERN.finditer(raw))
        if len(matches) != 1 or matches[0].group('token') != expected:
            return False
        before = raw[:matches[0].start('token')]
        offset = before.count('\n')
        line = node.lineno + offset
        if not (1 <= line <= len(lines)):
            return False
        if offset:
            start = len(before.rsplit('\n', 1)[-1])
        else:
            try:
                prefix = lines[line - 1].encode('utf-8')[:node.col_offset].decode('utf-8')
            except UnicodeDecodeError:
                return False
            start = len(prefix) + len(before)
        end = start + len(expected)
        if lines[line - 1][start:end] != expected:
            return False
        dest.setdefault(line, []).append((start, end))
        return True

    def row_id(text, kind):
        if text is None:
            return None
        hits = re.findall(r'(?m)^\|\s*(' + kind + r'-[0-9]{1,3})\s*\|\s*[A-Za-z ]+\s*\|$', text)
        return hits[0] if len(hits) == 1 else None

    if path == 'eval/tests/tooling/maintaining/field-report/test_unclosed_fence.py':
        def board_rejection(method):
            if method is None:
                return False
            for assertion in ast.walk(method):
                if not call(assertion, 'assertEqual') or len(assertion.args) != 2:
                    continue
                observed, expected = assertion.args
                if (not call(observed, 'detect_bucket') or len(observed.args) != 1 or
                        not isinstance(observed.args[0], ast.Dict) or
                        not isinstance(expected, ast.Tuple) or len(expected.elts) != 2 or
                        not isinstance(expected.elts[0], ast.Constant) or
                        expected.elts[0].value != 'unknown' or
                        not isinstance(expected.elts[1], ast.Constant) or
                        expected.elts[1].value is not None):
                    continue
                fields = {key.value: item for key, item in zip(observed.args[0].keys, observed.args[0].values)
                          if isinstance(key, ast.Constant) and isinstance(key.value, str)}
                producer = fields.get('board.md')
                if isinstance(producer, ast.Call) and _name(producer.func, 'broken_board_text'):
                    return True
            return False

        def task_rejection(method):
            if method is None:
                return False
            for statement in method.body:
                if not isinstance(statement, ast.With):
                    continue
                expected_error = any(call(item.context_expr, 'assertRaisesRegex') and
                                     len(item.context_expr.args) >= 1 and
                                     _name(item.context_expr.args[0], 'ValueError')
                                     for item in statement.items)
                if not expected_error:
                    continue
                for consumer in ast.walk(statement):
                    if call(consumer, 'count_tasks') and len(consumer.args) == 1:
                        producer = consumer.args[0]
                        if isinstance(producer, ast.Call) and _name(producer.func, 'broken_task_board_text'):
                            return True
            return False

        fence = next((node.value for node in tree.body if isinstance(node, ast.Assign)
                      and len(node.targets) == 1 and _name(node.targets[0], 'OPEN_FENCE')
                      and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)), None)
        if isinstance(fence, ast.Constant) and fence.value.count('```') == 1:
            for name, kind, header in (('broken_board_text', 'P', '| Point | Status |'),
                                       ('broken_task_board_text', 'T', '| Task | Status |')):
                fn = function(name)
                consumer_method = function('test_detect_bucket_returns_unknown_alone_and_beside_a_valid_four'
                                           if name == 'broken_board_text' else
                                           'test_count_tasks_raises_on_an_unclosed_fence')
                linked = (board_rejection(consumer_method) if name == 'broken_board_text' else
                          task_rejection(consumer_method))
                if not fn or not linked or len(fn.body) != 1 or not isinstance(fn.body[0], ast.Return):
                    continue
                terms = parts(fn.body[0].value)
                if (not terms or len(terms) != 3 or not isinstance(terms[0], ast.Constant) or
                        not _name(terms[1], 'OPEN_FENCE') or not isinstance(terms[2], ast.Constant)):
                    continue
                first, last = terms[0], terms[2]
                if (not isinstance(first.value, str) or not isinstance(last.value, str) or
                        header not in first.value or '|---|---|' not in first.value or
                        not last.value.startswith('| ')):
                    continue
                first_id, last_id = row_id(first.value, kind), row_id(last.value, kind)
                local = {}
                if first_id and last_id and mark(first, first_id, local) and mark(last, last_id, local):
                    for line, spans in local.items():
                        found.setdefault(line, []).extend(spans)
        method = function('test_detect_bucket_returns_unknown_alone_and_beside_a_valid_four')
        if method:
            assignments = [n for n in method.body if isinstance(n, ast.Assign) and
                           len(n.targets) == 1 and _name(n.targets[0], 'valid_four')]
            if len(assignments) == 1:
                expr = assignments[0].value
                terms = parts(expr)
                document = value(expr)
                linked = False
                for n in ast.walk(method):
                    if not call(n, 'detect_bucket') or len(n.args) != 1 or not isinstance(n.args[0], ast.Dict):
                        continue
                    fields = {k.value: v for k, v in zip(n.args[0].keys, n.args[0].values)
                              if isinstance(k, ast.Constant) and isinstance(k.value, str)}
                    if (_name(fields.get('task-board.md'), 'valid_four') and
                            isinstance(fields.get('board.md'), ast.Call) and
                            _name(fields['board.md'].func, 'broken_board_text') and
                            any(call(parent, 'assertEqual') and len(parent.args) == 2 and
                                parent.args[0] is n and isinstance(parent.args[1], ast.Tuple) and
                                len(parent.args[1].elts) == 2 and
                                isinstance(parent.args[1].elts[0], ast.Constant) and
                                parent.args[1].elts[0].value == 'unknown' and
                                isinstance(parent.args[1].elts[1], ast.Constant) and
                                parent.args[1].elts[1].value is None
                                for parent in ast.walk(method))):
                        linked = True
                if (linked and document and '| Task | Status |' in document and
                        'Schema: tackle-workspace/4' in document and '|---|---|' in document and
                        terms and len(terms) == 1 and isinstance(terms[0], ast.Constant)):
                    token = row_id(terms[0].value, 'T')
                    if token:
                        mark(terms[0], token, found)

    elif path == 'eval/tests/product/lint/rows/test_workspace_shapes.py':
        method = function('test_plan_seals_need_the_exact_decision')
        if method:
            calls = [n.value for n in method.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
            writes = [(i, n) for i, n in enumerate(calls) if call(n, 'write') and len(n.args) == 2]
            plans = [(i, n) for i, n in writes if value(n.args[0]) == 'plan.md']
            decisions = [(i, n) for i, n in writes if value(n.args[0]) == 'decisions.md']
            if len(plans) == 1 and len(decisions) == 2 and plans[0][0] < decisions[0][0] < decisions[1][0]:
                plan, wrong, right = value(plans[0][1].args[1]), value(decisions[0][1].args[1]), value(decisions[1][1].args[1])
                seal = re.search(r'<!-- SEALED: (' + _CASE_ID + r') -->', plan or '')
                wrong_id = re.search(r'^## (' + _CASE_ID + r')\b', wrong or '')
                right_id = re.search(r'^## (' + _CASE_ID + r')\b', right or '')
                negative = decisions[0][1].args[1]
                terms = parts(negative)
                blocked = any(call(n, 'assert_blocked') and len(n.args) == 1 and
                              isinstance(n.args[0], ast.Constant) and n.args[0].value == 7
                              for n in calls[decisions[0][0]+1:decisions[1][0]])
                passed = any(call(n, 'assert_pass') and len(n.args) == 1 and
                             isinstance(n.args[0], ast.Constant) and n.args[0].value == 7
                             for n in calls[decisions[1][0]+1:])
                if (seal and wrong_id and right_id and wrong_id.group(1) != seal.group(1) and
                        right_id.group(1) == seal.group(1) and blocked and passed and
                        terms and len(terms) == 2 and isinstance(terms[0], ast.Constant) and
                        isinstance(terms[1], ast.Constant)):
                    mark(terms[0], seal.group(1), found)

    elif path == 'eval/tests/tooling/validation-integrity/test_fields.py':
        method = function('test_row_7_requires_exact_decision_heading')
        if method:
            calls = [n.value for n in method.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
            clean = [n for n in calls if call(n, 'assert_clean') and len(n.args) == 2]
            failing = [n for n in calls if call(n, 'assert_finding') and len(n.args) == 3]
            if (len(clean) == 1 and len(failing) == 1 and
                    isinstance(clean[0].args[0], ast.Constant) and clean[0].args[0].value == 7 and
                    isinstance(failing[0].args[0], ast.Constant) and failing[0].args[0].value == 7):
                def mapping(node):
                    if not isinstance(node, ast.Dict):
                        return {}
                    return {key.value: item for key, item in zip(node.keys, node.values)
                            if isinstance(key, ast.Constant) and isinstance(key.value, str)}
                good, bad = mapping(clean[0].args[1]), mapping(failing[0].args[1])
                good_task, bad_task = value(good.get('tasks/T-A.md')), value(bad.get('tasks/T-A.md'))
                good_decision, bad_decision = value(good.get('decisions.md')), value(bad.get('decisions.md'))
                expected_node = failing[0].args[2]
                expected = value(expected_node)
                seal = re.search(r'<!-- SEALED: (' + _CASE_ID + r') -->', good_task or '')
                bad_seal = re.search(r'<!-- SEALED: (' + _CASE_ID + r') -->', bad_task or '')
                good_id = re.search(r'^## (' + _CASE_ID + r')\b', good_decision or '')
                bad_id = re.search(r'^## (' + _CASE_ID + r')\b', bad_decision or '')
                missing = re.fullmatch(r'missing seal: (' + _CASE_ID + r')', expected or '')
                if (seal and bad_seal and good_id and bad_id and missing and
                        seal.group(1) == bad_seal.group(1) == good_id.group(1) == missing.group(1) and
                        bad_id.group(1) != seal.group(1)):
                    local = {}
                    if (mark(bad.get('decisions.md'), bad_id.group(1), local) and
                            mark(expected_node, missing.group(1), local)):
                        for line, spans in local.items():
                            found.setdefault(line, []).extend(spans)
    return {line: tuple(spans) for line, spans in found.items()}


def _coverage_mutation_typed_spans(repo, path):
    """Bind the lifecycle Task ID literal to the real fixture and duration rejection oracle."""
    if path != 'eval/tests/product/lessons/test_coverage_table.py':
        return (), {}
    try:
        source = (repo / path).read_text(encoding='utf-8')
        fixture = (repo / 'eval/lessons/fixtures/coverage-lifecycle.md').read_text(encoding='utf-8')
        tree = ast.parse(source)
    except (OSError, UnicodeError, SyntaxError, ValueError):
        return (), {}
    klass = next((node for node in tree.body if isinstance(node, ast.ClassDef) and
                  node.name == 'CoverageTableGoldenTests'), None)
    if klass is None:
        return (), {}
    setup = next((node for node in klass.body if isinstance(node, ast.FunctionDef) and
                  node.name == 'setUp'), None)
    method = next((node for node in klass.body if isinstance(node, ast.FunctionDef) and
                   node.name == 'test_a_mutated_outcome_changes_the_duration_output'), None)
    if setup is None or method is None:
        return (), {}
    setup_sources = [ast.get_source_segment(source, node) for node in ast.walk(setup)
                     if isinstance(node, ast.Assign)]
    if not any(text == "self.lifecycle = HERE / 'fixtures/coverage-lifecycle.md'"
               for text in setup_sources if text):
        return (), {}
    if not any(text == 'self.command = extract_fixture_recipe_command()'
               for text in setup_sources if text):
        return (), {}
    rows = [[cell.strip() for cell in line.strip('|').split('|')]
            for line in fixture.splitlines() if line.startswith('|')]
    pair = [row for row in rows if len(row) == 14 and
            row[0].endswith('/Worker/01') and row[1] in ('start', 'finish')]
    if (len(pair) != 2 or pair[0][1] != 'start' or pair[1][1] != 'finish' or
            pair[0][0] != pair[1][0] or pair[0][2] != pair[1][2] or
            pair[0][9] != 'running' or pair[1][9] != 'success' or
            not re.fullmatch(r'T-?[0-9]{1,3}', pair[0][2])):
        return (), {}
    lines = source.splitlines()
    mutation = re.compile(
        r"^\s*original\.replace\(first_finish,\s*first_finish\.replace\('\| "
        r"(?P<id>" + _CASE_ID + r") \|', '\| T-Z \|'\), 1\),\s*$")
    found = [(number, match) for number, line in enumerate(lines, 1)
             if (match := mutation.fullmatch(line)) and match.group('id') == pair[0][2] and
             method.lineno <= number <= method.end_lineno]
    if len(found) != 1:
        return (), {}
    number, match = found[0]
    assignments = [node for node in ast.walk(method) if isinstance(node, ast.Assign)]
    variants_bindings = [node for node in assignments if len(node.targets) == 1 and
                         _name(node.targets[0], 'variants')]
    if len(variants_bindings) != 1:
        return (), {}
    variants_binding = variants_bindings[0]
    if (not isinstance(variants_binding.value, ast.Tuple) or
            len(variants_binding.value.elts) != 5 or
            not variants_binding.lineno <= number <= variants_binding.end_lineno or
            not all(isinstance(item, ast.Call) and
                    isinstance(item.func, ast.Attribute) and
                    _name(item.func.value, 'original') and
                    item.func.attr == 'replace' and len(item.args) == 3
                    for item in variants_binding.value.elts)):
        return (), {}
    supported_prefix = (
        "original.replace(first_start, first_start.replace('| running |', '| success |'), 1)",
        'original.replace(first_start, first_start + first_start, 1)',
        "original.replace(first_start, '', 1)",
        'original.replace(first_start + first_finish, first_finish + first_start, 1)',
    )
    if (tuple(ast.get_source_segment(source, item) for item in
              variants_binding.value.elts[:4]) != supported_prefix or
            variants_binding.value.elts[4].lineno != number):
        return (), {}
    if not any(node.lineno < number and ast.get_source_segment(source, node) ==
               "original = self.lifecycle.read_text(encoding='utf-8')"
               for node in assignments):
        return (), {}
    for event in ('start', 'finish'):
        if not any(node.lineno < number and isinstance(node.value, ast.Call) and
                   isinstance(node.value.func, ast.Name) and node.value.func.id == 'next' and
                   ('first_' + event) in [target.id for target in node.targets
                                         if isinstance(target, ast.Name)] and
                   "'Worker/01 | " + event + " |'" in
                   (ast.get_source_segment(source, node) or '') for node in assignments):
            return (), {}
    # The mutation must reach the actual recipe call and rejection assertion in a
    # straight-line subtest. Unsupported control flow fails closed; lexical mentions
    # of the oracle elsewhere in this method cannot admit an ID.
    if any(isinstance(node, (ast.If, ast.While, ast.Try, ast.Return, ast.Raise,
                             ast.Break, ast.Continue, ast.Match)) for node in ast.walk(method)):
        return (), {}
    loops = [node for node in method.body if isinstance(node, ast.For) and
             _name(node.target, 'text') and _name(node.iter, 'variants') and
             node.lineno > number]
    if (len(loops) != 1 or method.body[-1] is not loops[0] or
            method.body[-2] is not variants_binding):
        return (), {}
    loop = loops[0]
    if loop.orelse or len(loop.body) != 1 or not isinstance(loop.body[0], ast.With):
        return (), {}
    outer = loop.body[0]
    if (len(outer.items) != 1 or
            ast.get_source_segment(source, outer.items[0].context_expr) !=
            'self.subTest(invalid_lifecycle=text != original)' or
            len(outer.body) != 3 or not isinstance(outer.body[0], ast.With)):
        return (), {}
    inner = outer.body[0]
    if (len(inner.items) != 1 or
            ast.get_source_segment(source, inner.items[0].context_expr) !=
            "tempfile.TemporaryDirectory(prefix='tackle-lifecycle-invalid-')" or
            len(inner.body) != 3 or not all(isinstance(node, klass) for node, klass in
            zip(inner.body, (ast.Assign, ast.Expr, ast.Assign)))):
        return (), {}
    exact = lambda node, text: ast.get_source_segment(source, node) == text
    if not (exact(inner.body[0], "bad = Path(scratch) / 'invalid-lifecycle.md'") and
            exact(inner.body[1], "bad.write_text(text, encoding='utf-8')") and
            exact(inner.body[2], 'child = run_in_workspace(self.command, bad, self.sidecar)') and
            exact(outer.body[1], "self.assertEqual((child.returncode, child.stderr), (0, ''))") and
            exact(outer.body[2], "self.assertEqual(child.stdout.splitlines(),\n"
                 "                                 ['tokens 3/5 (60%)', 'duration 1/5 (20%)'])")):
        return (), {}
    return lines, {number: (_group_span(match, 'id'),)}


def _lifecycle_lite_typed_spans(repo, path):
    """Admit only the linked Lite row-16 model and its original failing overlay."""
    match = re.fullmatch(
        r'eval/lint/rows/fixtures/(?P<fixture>pass-lite|fail-16-unsupported-lite)/'
        r'docs/plans/demo/(?P<document>resource-usage|history)\.md', path)
    if not match:
        return None
    fixture = match.group('fixture')
    if fixture != 'pass-lite' and match.group('document') != 'resource-usage':
        return (), {}
    prefix = 'eval/lint/rows/fixtures/pass-lite/docs/plans/demo/'
    negative = 'eval/lint/rows/fixtures/fail-16-unsupported-lite/docs/plans/demo/resource-usage.md'
    try:
        plan = (repo / (prefix + 'plan.md')).read_text(encoding='utf-8')
        ledger = (repo / (prefix + 'resource-usage.md')).read_text(encoding='utf-8')
        history = (repo / (prefix + 'history.md')).read_text(encoding='utf-8')
        old = (repo / negative).read_text(encoding='utf-8')
        consumer = ast.parse((repo / 'eval/tests/product/lint/rows/test_lint_rows.py')
                             .read_text(encoding='utf-8'))
    except (OSError, UnicodeError, SyntaxError, ValueError):
        return (), {}
    if not plan.startswith('Gate: Lite\n'):
        return (), {}

    def tuple_items(name):
        return next((node.value.elts for node in consumer.body
                     if isinstance(node, ast.Assign) and len(node.targets) == 1 and
                     _name(node.targets[0], name) and
                     isinstance(node.value, (ast.List, ast.Tuple))), ())

    def linked(method_name, collection, outcome, failure=False):
        method = next((node for klass in consumer.body if isinstance(klass, ast.ClassDef)
                       for node in klass.body if isinstance(node, ast.FunctionDef) and
                       node.name == method_name), None)
        if method is None:
            return False
        for variants in method.body:
            if not (isinstance(variants, ast.For) and isinstance(variants.iter, ast.Call) and
                    _name(variants.iter.func, 'awk_variants')):
                continue
            for fixtures in variants.body:
                if not (isinstance(fixtures, ast.For) and _name(fixtures.iter, collection) and
                        isinstance(fixtures.target, ast.Tuple)):
                    continue
                names = ('fixture', 'base', 'number', 'expected', 'wanted') if failure else ('fixture', 'base')
                if len(fixtures.target.elts) != len(names) or not all(
                        _name(item, name) for item, name in zip(fixtures.target.elts, names)):
                    continue
                scope = fixtures.body if failure else next((node.body for node in fixtures.body
                    if isinstance(node, ast.For) and _name(node.target, 'number') and
                    isinstance(node.iter, ast.Call) and _name(node.iter.func, 'range') and
                    len(node.iter.args) == 2 and all(isinstance(arg, ast.Constant)
                    for arg in node.iter.args) and [arg.value for arg in node.iter.args] == [1, 17]), ())
                for block in scope:
                    if not isinstance(block, ast.With):
                        continue
                    body = fixtures.body if not failure else block.body
                    root = next((node for node in body if isinstance(node, ast.Assign) and
                        len(node.targets) == 1 and _name(node.targets[0], 'root') and
                        isinstance(node.value, ast.Call) and
                        isinstance(node.value.func, ast.Attribute) and
                        _name(node.value.func.value, 'self') and
                        node.value.func.attr == 'workspace' and
                        len(node.value.args) == 2 and
                        _name(node.value.args[0], 'fixture') and
                        _name(node.value.args[1], 'base')), None)
                    assertions = block.body
                    row = next((node for node in assertions if isinstance(node, ast.Assign) and
                        isinstance(node.value, ast.Call) and _name(node.value.func, 'run_row') and
                        len(node.value.args) == 3 and
                        all(_name(arg, key) for arg, key in
                            zip(node.value.args, ('number', 'root', 'awk'))) and
                        len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple) and
                        len(node.targets[0].elts) == 2 and
                        _name(node.targets[0].elts[0], 'verdict')), None)
                    oracle = next((node for node in assertions if isinstance(node, ast.Expr) and
                        isinstance(node.value, ast.Call) and
                        isinstance(node.value.func, ast.Attribute) and
                        _name(node.value.func.value, 'self') and
                        node.value.func.attr == 'assertEqual' and
                        len(node.value.args) >= 2 and
                        _name(node.value.args[0], 'verdict') and
                        ((_name(node.value.args[1], 'wanted') if failure else
                          isinstance(node.value.args[1], ast.Constant) and
                          node.value.args[1].value == outcome))), None)
                    diagnostic = not failure or any(isinstance(node, ast.Expr) and
                        isinstance(node.value, ast.Call) and
                        isinstance(node.value.func, ast.Attribute) and
                        _name(node.value.func.value, 'self') and
                        node.value.func.attr == 'assertIn' and
                        len(node.value.args) >= 1 and
                        _name(node.value.args[0], 'expected') for node in assertions)
                    if root and row and oracle and diagnostic and row.lineno < oracle.lineno:
                        return True
        return False

    clean = any(isinstance(item, ast.Tuple) and len(item.elts) == 2 and
                isinstance(item.elts[0], ast.Constant) and item.elts[0].value == 'pass-lite' and
                isinstance(item.elts[1], ast.Constant) and item.elts[1].value is None
                for item in tuple_items('PASSES'))
    bad = any(isinstance(item, ast.Tuple) and len(item.elts) == 5 and
              all(isinstance(value, ast.Constant) for value in item.elts) and
              [value.value for value in item.elts] ==
              ['fail-16-unsupported-lite', 'pass-lite', 16, 'invalid finish Outcome', 'FAIL']
              for item in tuple_items('FAILS'))
    if not (clean and bad and
            linked('test_clean_fixtures_pass_every_row', 'PASSES', 'PASS') and
            linked('test_each_row_fails_on_its_planted_defect', 'FAILS', 'FAIL', True)):
        return (), {}

    def data_rows(source):
        return [[cell.strip() for cell in line.strip('|').split('|')]
                for line in source.splitlines() if line.startswith('|') and
                len(line.strip('|').split('|')) == 14 and
                not line.startswith('| Run ID') and not line.startswith('|---')]
    rows = data_rows(ledger)
    old_rows = data_rows(old)
    if len(rows) != 2 or len(old_rows) != 2:
        return (), {}
    start, finish = rows
    old_start, old_finish = old_rows
    task = start[2]
    if (not re.fullmatch(r'T-?[0-9]{1,3}', task) or start[0] != finish[0] or
            start[1:3] != ['start', task] or finish[1:3] != ['finish', task] or
            start[9] != 'running' or finish[9:11] != ['success', '1'] or
            finish[13] != 'history.md#cycle-alpha' or
            finish[12] != 'reports/' + task + '-report.md' or
            old_finish[12] != finish[12] or
            old_start[0:3] != start[0:3] or old_finish[0:3] != finish[0:3] or
            old_start[9] != 'n/a' or old_finish[9:11] != ['complete', '1'] or
            old_finish[13] != 'demo'):
        return (), {}
    section = next((part for part in re.split(r'(?=^### Event )', history, flags=re.M)
                    if part.startswith('### Event cycle-alpha\n')), None)
    if section is None:
        return (), {}
    fields = dict(line.split(':', 1) for line in section.splitlines()[1:] if ':' in line)
    fields = {key.strip(): value.strip() for key, value in fields.items()}
    if (fields.get('Task ID') != task or not all(fields.get(key) for key in
            ('Fault', 'Observed', 'Repair', 'Check')) or
            not re.search(r'exit\s+[1-9][0-9]*', fields['Check'])):
        return (), {}

    lines = (old if fixture != 'pass-lite' else
             ledger if match.group('document') == 'resource-usage' else history).splitlines()
    spans = {}
    for number, text in enumerate(lines, 1):
        typed = (re.fullmatch(r'\|\s*(?P<run>[^|]+?)\s*\|\s*(?P<event>start|finish)\s*\|\s*(?P<id>' +
                               _CASE_ID + r')\s*\|.*', text)
                 if match.group('document') == 'resource-usage' else
                 re.fullmatch(r'Task ID:\s*(?P<id>' + _CASE_ID + r')\s*', text))
        if typed and typed.group('id') == task and (
                match.group('document') != 'resource-usage' or
                (typed.group('run').strip() == start[0] and re.fullmatch(r'r[0-9]+', start[0]))):
            spans[number] = (_group_span(typed, 'id'),)
            if match.group('document') == 'resource-usage':
                spans[number] += (_group_span(typed, 'run'),)
            if match.group('document') == 'resource-usage' and typed.group('event') == 'finish':
                verification = re.fullmatch(
                    r'\|(?:[^|]*\|){12}\s*reports/(?P<id>' + _CASE_ID +
                    r')-report[.]md\s*\|.*', text)
                if verification and verification.group('id') == task:
                    spans[number] += (_group_span(verification, 'id'),)
    if len(spans) != (1 if match.group('document') == 'history' else 2):
        return (), {}
    return lines, spans


def _lifecycle_fixture_typed_spans(repo, path):
    """Bind task-field IDs in the two row-16 clean fixtures to their actual consumer and trace."""
    lite = _lifecycle_lite_typed_spans(repo, path)
    if lite is not None:
        return lite
    match = re.fullmatch(
        r'eval/lint/rows/fixtures/(?P<fixture>pass-full|pass-full-5)/docs/plans/demo/'
        r'(?P<document>resource-usage|history)\.md', path)
    if not match:
        return (), {}
    root = 'eval/lint/rows/fixtures/' + match.group('fixture') + '/docs/plans/demo/'
    try:
        board = (repo / (root + 'task-board.md')).read_text(encoding='utf-8')
        ledger = (repo / (root + 'resource-usage.md')).read_text(encoding='utf-8')
        history = (repo / (root + 'history.md')).read_text(encoding='utf-8')
        consumer = (repo / 'eval/tests/product/lint/rows/test_lint_rows.py').read_text(encoding='utf-8')
        tree = ast.parse(consumer)
    except (OSError, UnicodeError, SyntaxError, ValueError):
        return (), {}

    passes = next((node.value for node in tree.body if isinstance(node, ast.Assign) and
                   len(node.targets) == 1 and _name(node.targets[0], 'PASSES')), None)
    names = {item.elts[0].value for item in passes.elts
             if isinstance(item, ast.Tuple) and len(item.elts) == 2 and
             isinstance(item.elts[0], ast.Constant) and isinstance(item.elts[0].value, str) and
             isinstance(item.elts[1], ast.Constant) and item.elts[1].value is None} \
        if isinstance(passes, (ast.List, ast.Tuple)) else set()
    method = next((node for klass in tree.body if isinstance(klass, ast.ClassDef)
                   for node in klass.body if isinstance(node, ast.FunctionDef) and
                   node.name == 'test_clean_fixtures_pass_every_row'), None)
    def linked_consumer():
        if method is None:
            return False
        for variant_loop in method.body:
            if not (isinstance(variant_loop, ast.For) and
                    isinstance(variant_loop.iter, ast.Call) and
                    _name(variant_loop.iter.func, 'awk_variants')):
                continue
            for fixture_loop in variant_loop.body:
                if not (isinstance(fixture_loop, ast.For) and
                        _name(fixture_loop.iter, 'PASSES') and
                        isinstance(fixture_loop.target, ast.Tuple) and
                        [_name(item, key) for item, key in
                         zip(fixture_loop.target.elts, ('fixture', 'base'))] == [True, True] and
                        len(fixture_loop.target.elts) == 2):
                    continue
                root_assignment = next((node for node in fixture_loop.body
                    if isinstance(node, ast.Assign) and len(node.targets) == 1 and
                    _name(node.targets[0], 'root') and isinstance(node.value, ast.Call) and
                    isinstance(node.value.func, ast.Attribute) and
                    _name(node.value.func.value, 'self') and
                    node.value.func.attr == 'workspace' and
                    len(node.value.args) == 2 and
                    _name(node.value.args[0], 'fixture') and
                    _name(node.value.args[1], 'base')), None)
                if root_assignment is None:
                    continue
                for row_loop in fixture_loop.body:
                    if not (isinstance(row_loop, ast.For) and
                            _name(row_loop.target, 'number') and
                            isinstance(row_loop.iter, ast.Call) and
                            _name(row_loop.iter.func, 'range') and
                            len(row_loop.iter.args) == 2 and
                            all(isinstance(arg, ast.Constant) for arg in row_loop.iter.args) and
                            [arg.value for arg in row_loop.iter.args] == [1, 17]):
                        continue
                    for subtest in row_loop.body:
                        if not isinstance(subtest, ast.With):
                            continue
                        rows = [node for node in subtest.body if isinstance(node, ast.Assign) and
                                isinstance(node.value, ast.Call) and
                                _name(node.value.func, 'run_row') and
                                len(node.value.args) == 3 and
                                all(_name(arg, value) for arg, value in
                                    zip(node.value.args, ('number', 'root', 'awk'))) and
                                len(node.targets) == 1 and
                                isinstance(node.targets[0], ast.Tuple) and
                                len(node.targets[0].elts) == 2 and
                                _name(node.targets[0].elts[0], 'verdict')]
                        passes_row = [node for node in subtest.body if isinstance(node, ast.Expr) and
                                      isinstance(node.value, ast.Call) and
                                      isinstance(node.value.func, ast.Attribute) and
                                      _name(node.value.func.value, 'self') and
                                      node.value.func.attr == 'assertEqual' and
                                      len(node.value.args) >= 2 and
                                      _name(node.value.args[0], 'verdict') and
                                      isinstance(node.value.args[1], ast.Constant) and
                                      node.value.args[1].value == 'PASS']
                        if rows and passes_row and rows[0].lineno < passes_row[0].lineno:
                            return True
        return False

    if match.group('fixture') not in names or not linked_consumer():
        return (), {}

    board_rows = [[cell.strip() for cell in line.strip('|').split('|')]
                  for line in board.splitlines() if line.startswith('|')]
    header = next((row for row in board_rows if 'Task' in row and 'Status' in row), None)
    if header is None or not {'Task', 'Status', 'Brief', 'Verification'} <= set(header):
        return (), {}
    position = {name: header.index(name) for name in ('Task', 'Status', 'Brief', 'Verification')}
    done = [row for row in board_rows if len(row) == len(header) and
            row[position['Status']] == 'Complete']
    if len(done) != 1:
        return (), {}
    task = done[0][position['Task']]
    if (not re.fullmatch(r'T-?[0-9]{1,3}', task) or
            done[0][position['Brief']] != 'tasks/' + task + '.md' or
            done[0][position['Verification']] != 'reports/' + task + '-report.md'):
        return (), {}

    ledger_lines = ledger.splitlines()
    rows = [[cell.strip() for cell in line.strip('|').split('|')]
            for line in ledger_lines if line.startswith('|')]
    data = [row for row in rows if len(row) == 14 and row[0] not in ('Run ID', '---')]
    if len(data) != 2 or len(data[0]) != 14 or len(data[1]) != 14:
        return (), {}
    start, finish = data
    if (start[0] != finish[0] or start[1:3] != ['start', task] or
            finish[1:3] != ['finish', task] or start[9] != 'running' or
            finish[9] != 'success' or finish[10] != '1' or
            finish[12] != done[0][position['Verification']] or
            not re.fullmatch(r'history\.md#[a-z][a-z0-9-]*', finish[13])):
        return (), {}
    event = finish[13].split('#', 1)[1]
    sections = [section for section in re.split(r'(?=^### Event )', history, flags=re.M)
                if section.startswith('### Event ' + event + '\n')]
    if len(sections) != 1:
        return (), {}
    fields = {}
    for line in sections[0].splitlines()[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            fields[key.strip()] = value.strip()
    if (fields.get('Task ID') != task or not all(fields.get(name) for name in
            ('Fault', 'Observed', 'Repair', 'Check')) or
            not re.search(r'exit\s+[1-9][0-9]*', fields['Check']) or
            fields.get('Counted cycle') != '1'):
        return (), {}

    source_lines = ledger_lines if match.group('document') == 'resource-usage' else history.splitlines()
    spans = {}
    for number, text in enumerate(source_lines, 1):
        if match.group('document') == 'resource-usage':
            typed = re.fullmatch(r'\|\s*(?P<run>[^|]+?)\s*\|\s*(?P<event>start|finish)\s*\|\s*(?P<id>' +
                                 _CASE_ID + r')\s*\|.*', text)
        else:
            typed = re.fullmatch(r'Task ID:\s*(?P<id>' + _CASE_ID + r')\s*', text)
        if typed and typed.group('id') == task and (
                match.group('document') != 'resource-usage' or
                (typed.group('run').strip() == start[0] and re.fullmatch(r'r[0-9]+', start[0]))):
            spans[number] = (_group_span(typed, 'id'),)
            if match.group('document') == 'resource-usage':
                spans[number] += (_group_span(typed, 'run'),)
            if match.group('document') == 'resource-usage' and typed.group('event') == 'finish':
                verification = re.fullmatch(
                    r'\|(?:[^|]*\|){12}\s*reports/(?P<id>' + _CASE_ID +
                    r')-report[.]md\s*\|.*', text)
                if verification and verification.group('id') == task:
                    spans[number] += (_group_span(verification, 'id'),)
    if len(spans) != (2 if match.group('document') == 'resource-usage' else 1):
        return (), {}
    return source_lines, spans


def _typed_id_spans(path, text):
    """Return only token spans occupying a known, typed fixture/model field."""
    if path == 'eval/rules/fixtures/build.py':
        statement = _python_statement(text)
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target, call = statement.targets[0], statement.value
            if (isinstance(target, ast.Subscript) and _name(target.value, 'bases') and
                    isinstance(call, ast.Call) and _name(call.func, 'gate_repo') and
                    len(call.args) >= 2 and _name(call.args[0], 'out')):
                key, argument = target.slice, call.args[1]
                if (isinstance(key, ast.Constant) and isinstance(key.value, str) and
                        isinstance(argument, ast.Constant) and isinstance(argument.value, str) and
                        key.value == argument.value):
                    spans = [_string_id_span(text, key), _string_id_span(text, argument)]
                    if all(spans):
                        return spans
    elif path == 'eval/tests/tooling/rules/test_ledger.py':
        statement = _python_statement(text)
        if (isinstance(statement, ast.Assign) and len(statement.targets) == 1 and
                _name(statement.targets[0], 'result') and isinstance(statement.value, ast.Call) and
                _name(statement.value.func, 'gate') and len(statement.value.args) >= 2):
            root_call, lookup = statement.value.args[:2]
            if (isinstance(root_call, ast.Call) and _attribute(root_call.func, 'self', 'root') and
                    len(root_call.args) == 1 and isinstance(root_call.args[0], ast.Constant) and
                    isinstance(root_call.args[0].value, str) and isinstance(lookup, ast.Subscript) and
                    _name(lookup.value, 'GATE_BASES') and isinstance(lookup.slice, ast.Constant) and
                    isinstance(lookup.slice.value, str) and
                    root_call.args[0].value == lookup.slice.value):
                spans = [_string_id_span(text, root_call.args[0]), _string_id_span(text, lookup.slice)]
                if all(spans):
                    return spans
    elif path == 'eval/tests/tooling/behavior/judges/resume/test_fixtures.py':
        statement = _python_statement(text)
        expression = statement.value if isinstance(statement, ast.Expr) else None
        if (isinstance(expression, ast.Tuple) and len(expression.elts) == 1 and
                isinstance(expression.elts[0], ast.Tuple)):
            expression = expression.elts[0]
        if (isinstance(expression, ast.Tuple) and len(expression.elts) == 3 and
                isinstance(expression.elts[1], ast.Constant) and isinstance(expression.elts[1].value, str) and
                isinstance(expression.elts[2], ast.Dict)):
            span = _string_id_span(text, expression.elts[0])
            if span:
                return [span]
    elif path == 'eval/tests/tooling/behavior/harness/test_subagent.py':
        statement = _python_statement(text)
        expression = statement.value if isinstance(statement, ast.Expr) else None
        calls = expression.elts if isinstance(expression, ast.Tuple) else [expression]
        spans = []
        for call in calls:
            if not isinstance(call, ast.Call) or not _name(call.func, 'tool_row') and \
                    not _name(call.func, 'text_row') and not _name(call.func, 'handback_row'):
                continue
            for keyword in call.keywords:
                if keyword.arg == 'request_id':
                    span = _string_id_span(text, keyword.value)
                    if span:
                        spans.append(span)
        if spans:
            return spans
    elif path == 'eval/tests/tooling/maintaining/field-report/test_unclosed_fence.py':
        match = re.fullmatch(
            r"\s*\|\s*(?P<id>P-?[0-9]{1,3})\s*\|\s*[A-Za-z ]+\s*\|\s*", text, re.I)
        if match:
            return [_group_span(match, 'id')]
    elif path == 'eval/tests/tooling/validation-integrity/test_fields.py':
        match = re.fullmatch(
            r'\s*"tasks/T-A\.md"\s*:\s*"## Acceptance <!-- SEALED: (?P<id>' +
            _CASE_ID + r') -->\\n"\s*,?\s*', text, re.I)
        if match:
            return [_group_span(match, 'id')]
        match = re.fullmatch(
            r'\s*"decisions\.md"\s*:\s*"## (?P<id>' + _CASE_ID +
            r') — Accepted rule\\n"\s*,?\s*', text, re.I)
        if match:
            return [_group_span(match, 'id')]
    elif path == 'eval/tests/product/lint/rows/test_workspace_shapes.py':
        match = re.fullmatch(
            r"\s*self\.write\('plan\.md', 'Gate: Lite\\n# Task\\n<!-- SEALED: (?P<id>" +
            _CASE_ID + r") -->\\n'\)\s*", text, re.I)
        if match:
            return [_group_span(match, 'id')]
        match = re.fullmatch(
            r"\s*self\.write\('decisions\.md', '## (?P<id>" + _CASE_ID +
            r") — approved\\n'\)\s*", text, re.I)
        if match:
            return [_group_span(match, 'id')]
    elif path in {'eval/status/benchmark.py', 'eval/tests/product/status/test_context.py'}:
        statement = _python_statement(text)
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target, value = statement.targets[0], statement.value
            expected_target = (_name(target, 'scope') or _attribute(target, 'self', 'scope'))
            if expected_target and isinstance(value, ast.Dict) and len(value.keys) == 3:
                entries = {}
                for key, item in zip(value.keys, value.values):
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        entries[key.value] = item
                if set(entries) == {'tasks', 'requirements', 'milestone'}:
                    span = _string_id_span(text, entries['milestone'])
                    if span:
                        return [span]
    elif path == 'eval/tests/product/templates/test_template_drift.py':
        statement = _python_statement(text)
        expression = statement.value if isinstance(statement, ast.Expr) else None
        if isinstance(expression, ast.Call) and _name(expression.func, 'dict'):
            keywords = {keyword.arg: keyword.value for keyword in expression.keywords}
            if (isinstance(keywords.get('source'), ast.Constant) and keywords['source'].value == 's1' and
                    isinstance(keywords.get('configuration'), ast.Constant) and
                    keywords['configuration'].value == 'cfg1' and
                    'contract' in keywords and 'dependencies' in keywords):
                spans = [_string_id_span(text, keywords['contract']),
                         _string_id_span(text, keywords['dependencies'])]
                if all(spans):
                    return spans
        else:
            match = re.fullmatch(
                r"\s*dict\(contract=(?P<q>['\"])(?P<contract>" + _CASE_ID +
                r")\1,\s*source=(?P=q)s1\1,\s*configuration=(?P=q)cfg1\1,\s*dependencies=(?P=q)(?P<dependencies>" +
                _CASE_ID + r")\1,\s*", text, re.I)
            if match:
                return [_group_span(match, 'contract'), _group_span(match, 'dependencies')]
    return []


_SCENARIO_WORKSPACES = {
    ('s65-migration-replay', 'h1'): 'catalog-pricing',
    ('s65-migration-replay', 'v1'): 'loyalty-cents',
    ('s66-notice-replay', 'h1'): 'status-alerts',
    ('s66-notice-replay', 'v1'): 'reminder-outbox',
}
_SCENARIO_OVERLAYS = {'a', 'b', 'fails-acceptance', 'repeats-effect', 'reset-cycles'}


def _scenario_role(path):
    """Name one exact scenario model role; never grant a directory-wide exception."""
    for (scenario, variant), workspace in _SCENARIO_WORKSPACES.items():
        root = 'eval/scenarios/' + scenario + '/variants/' + variant + '/'
        if not path.startswith(root):
            continue
        relative = path[len(root):]
        if relative == 'GROUND-TRUTH.md':
            return root, workspace, 'rubric', None
        if relative in ('hidden/test_b_board_history.py', 'hidden/test_c_cycles.py'):
            return root, workspace, 'hidden', None
        if relative == 'input/fixture/alerts.json' and scenario == 's66-notice-replay' and variant == 'h1':
            return root, workspace, 'alert', None
        if relative.startswith('input/fixture/docs/plans/' + workspace + '/'):
            rest = relative[len('input/fixture/docs/plans/' + workspace + '/'):]
            kind = 'input'
            overlay = None
        else:
            pieces = relative.split('/', 2)
            if len(pieces) != 3 or pieces[0] != 'reference' or pieces[1] not in _SCENARIO_OVERLAYS:
                return None
            overlay = pieces[1]
            prefix = 'docs/plans/' + workspace + '/'
            if not pieces[2].startswith(prefix):
                return None
            rest = pieces[2][len(prefix):]
            kind = 'reference'
        if rest in ('task-board.md', 'history.md'):
            return root, workspace, kind + ':' + rest, overlay
        if kind == 'input' and re.fullmatch(r'tasks/T-[0-9]{1,3}-' + re.escape(workspace) + r'\.md', rest):
            return root, workspace, 'input:task-heading', None
        return None
    return None


def _scenario_board(repo, root, workspace, role, overlay):
    if role.startswith('reference:'):
        base = root + 'reference/' + overlay + '/docs/plans/' + workspace + '/'
    else:
        base = root + 'input/fixture/docs/plans/' + workspace + '/'
    try:
        board = (repo / (base + 'task-board.md')).read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return None, None
    rows = [[cell.strip() for cell in line.strip('|').split('|')]
            for line in board.splitlines() if line.startswith('|')]
    headers = [row for row in rows if row == ['Task', 'What', 'Brief', 'Depends on', 'Status', 'Verification']]
    data = [row for row in rows if len(row) == 6 and re.fullmatch(r'T-([0-9]{1,3})', row[0])]
    if len(headers) != 1 or len(data) != 1:
        return None, None
    row = data[0]
    if (row[0].split('-', 1)[1] != '1' or
            row[2] != 'tasks/' + row[0] + '-' + workspace + '.md'):
        return None, None
    return row[0], base


def _scenario_indexed(repo, root):
    try:
        index = json.loads((repo / 'eval/scenarios/INDEX.json').read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError):
        return False
    if not isinstance(index, dict) or not isinstance(index.get('scenarios'), list):
        return False
    parts = root.rstrip('/').split('/')
    scenario, variant = parts[2], parts[4]
    entries = [item for item in index['scenarios'] if isinstance(item, dict) and
               item.get('scenario_id') == scenario]
    if len(entries) != 1 or not isinstance(entries[0].get('variants'), list):
        return False
    matches = [item for item in entries[0]['variants'] if isinstance(item, dict) and
               item.get('variant_id') == variant and item.get('path') == root.rstrip('/') + '/input' and
               item.get('fixture') == 'fixture' and item.get('stageable') is True]
    return len(matches) == 1


def _scenario_staged_oracle_link(tree, functions):
    """Require staged-history control/data to reach a test assertion, not merely a call."""
    names = {function.name: function for function in functions}
    if len(names) != len(functions):
        return False
    tests = set()
    for klass in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        if not any(_name(base, 'TestCase') or
                   (isinstance(base, ast.Attribute) and base.attr == 'TestCase' and
                    _name(base.value, 'unittest')) for base in klass.bases):
            continue
        tests.update(node.name for node in klass.body if isinstance(node, ast.FunctionDef) and
                     node.name.startswith('test_'))
    if not tests:
        return False
    unary_assertions = {'assertTrue', 'assertFalse', 'assertIsNone', 'assertIsNotNone'}
    binary_assertions = {'assertEqual', 'assertNotEqual', 'assertIn', 'assertNotIn',
                         'assertIs', 'assertIsNot', 'assertGreater', 'assertGreaterEqual',
                         'assertLess', 'assertLessEqual', 'assertRegex', 'assertNotRegex',
                         'assertAlmostEqual', 'assertNotAlmostEqual', 'assertCountEqual',
                         'assertSequenceEqual', 'assertListEqual', 'assertDictEqual',
                         'assertSetEqual', 'assertIsInstance', 'assertNotIsInstance'}

    def inspect(function, summaries):
        env = {}
        returned = asserted = False
        supported = True

        def tainted(node):
            if node is None:
                return False
            if isinstance(node, ast.Name):
                return env.get(node.id, False)
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and node.func.attr == 'startswith' and
                        len(node.args) == 1 and _name(node.args[0], 'STAGED_HISTORY')):
                    return True
                if isinstance(node.func, ast.Name) and summaries.get(node.func.id, False):
                    return True
            return any(tainted(child) for child in ast.iter_child_nodes(node))

        def bind(target, value):
            if isinstance(target, ast.Name):
                env[target.id] = value
            elif isinstance(target, (ast.Tuple, ast.List)):
                for item in target.elts:
                    bind(item, value)

        def block(statements, control=False):
            nonlocal returned, asserted, supported
            for statement in statements:
                if isinstance(statement, ast.Assign):
                    value = control or tainted(statement.value)
                    for target in statement.targets:
                        bind(target, value)
                elif isinstance(statement, ast.AnnAssign):
                    bind(statement.target, control or tainted(statement.value))
                elif isinstance(statement, ast.AugAssign):
                    bind(statement.target, control or tainted(statement.target) or tainted(statement.value))
                elif isinstance(statement, ast.Return):
                    returned |= control or tainted(statement.value)
                    return False
                elif isinstance(statement, ast.Raise):
                    return False
                elif isinstance(statement, ast.Expr):
                    call = statement.value
                    if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
                        if function.name in tests and _name(call.func.value, 'self'):
                            tested = (1 if call.func.attr in unary_assertions else
                                      2 if call.func.attr in binary_assertions else 0)
                            if tested and len(call.args) >= tested and any(
                                    tainted(arg) for arg in call.args[:tested]):
                                asserted = True
                        if (call.func.attr in ('append', 'extend') and
                                isinstance(call.func.value, ast.Name) and
                                any(tainted(arg) for arg in call.args)):
                            env[call.func.value.id] = True
                elif isinstance(statement, ast.If):
                    if isinstance(statement.test, ast.Constant) and statement.test.value is False:
                        if not block(statement.orelse, control):
                            return False
                    elif isinstance(statement.test, ast.Constant) and statement.test.value is True:
                        if not block(statement.body, control):
                            return False
                    else:
                        conditional = control or tainted(statement.test)
                        body_falls_through = block(statement.body, conditional)
                        else_falls_through = block(statement.orelse, conditional)
                        if not (body_falls_through or else_falls_through):
                            return False
                elif isinstance(statement, ast.For):
                    bind(statement.target, control or tainted(statement.iter))
                    block(statement.body, control)
                    block(statement.orelse, control)
                elif isinstance(statement, ast.While):
                    conditional = control or tainted(statement.test)
                    block(statement.body, conditional)
                    block(statement.orelse, conditional)
                elif isinstance(statement, (ast.Break, ast.Continue)):
                    return False
                elif isinstance(statement, ast.Pass):
                    continue
                else:
                    supported = False
                    return False
            return True

        block(function.body)
        return supported, returned, asserted

    summaries = {name: False for name in names}
    for _ in range(len(names) + 1):
        changed = False
        for name, function in names.items():
            supported, returned, _ = inspect(function, summaries)
            if supported and returned and not summaries[name]:
                summaries[name] = changed = True
        if not changed:
            break
    return any(function.name in tests and inspect(function, summaries)[0] and
               inspect(function, summaries)[2] for function in functions)


def _scenario_hidden_spans(lines, task):
    try:
        tree = ast.parse('\n'.join(lines) + '\n')
    except (SyntaxError, ValueError):
        return {}
    spans = {}
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    local_name = 'm' + str(2)
    for function in functions:
        nodes = list(ast.walk(function))
        assignments = [node for node in nodes if isinstance(node, ast.Assign) and
                       len(node.targets) == 1 and _name(node.targets[0], local_name) and
                       isinstance(node.value, ast.Call) and
                       isinstance(node.value.func, ast.Attribute) and
                       node.value.func.attr == 'match']
        ends = [node for node in nodes if isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and node.func.attr == 'end' and
                _name(node.func.value, local_name)]
        if len(assignments) == 2 and len(ends) == 2:
            for node in nodes:
                if isinstance(node, ast.Name) and node.id == local_name:
                    spans.setdefault(node.lineno, []).append((node.col_offset, node.end_col_offset))
        for branch in function.body:
            if not isinstance(branch, ast.For):
                continue
            for conditional in branch.body:
                if not isinstance(conditional, ast.If) or not isinstance(conditional.test, ast.Call):
                    continue
                call = conditional.test
                if (not isinstance(call.func, ast.Attribute) or call.func.attr != 'startswith' or
                        len(call.args) != 1 or not isinstance(call.args[0], ast.Constant) or
                        call.args[0].value != '| ' + task):
                    continue
                returns = [node for node in ast.walk(conditional) if isinstance(node, ast.Return) and
                           isinstance(node.value, ast.IfExp) and
                           isinstance(node.value.body, ast.Subscript) and
                           isinstance(node.value.body.slice, ast.Constant) and
                           node.value.body.slice.value == 4]
                if not returns:
                    continue
                literal = call.args[0]
                text = lines[literal.lineno - 1]
                match = re.search(r'(?<![A-Za-z0-9_])' + re.escape(task) + r'(?![A-Za-z0-9_])', text)
                if match and len([m for m in ID_PATTERN.finditer(text) if m.group('token') == task]) == 1:
                    spans.setdefault(literal.lineno, []).append(match.span())
    assignments = [node for node in tree.body if isinstance(node, ast.Assign) and
                   len(node.targets) == 1 and _name(node.targets[0], 'STAGED_HISTORY') and
                   isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)]
    if len(assignments) == 1:
        literal = assignments[0].value
        field = re.findall(r'^- In flight: (T-[0-9]{1,3}),', literal.value, flags=re.M)
        uses = [function for function in functions if any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
            node.func.attr == 'startswith' and len(node.args) == 1 and
            _name(node.args[0], 'STAGED_HISTORY') for node in ast.walk(function))]
        if field == [task] and uses and _scenario_staged_oracle_link(tree, functions):
            text = lines[literal.lineno - 1]
            match = re.search(r'\\n- In flight: (?P<id>T-[0-9]{1,3}),', text)
            if match and match.group('id') == task:
                spans.setdefault(literal.lineno, []).append(match.span('id'))
    return spans


def _scenario_typed_spans(repo, path):
    role = _scenario_role(path)
    if role is None:
        return (), {}
    root, workspace, kind, overlay = role
    if not _scenario_indexed(repo, root):
        return (), {}
    try:
        source = (repo / path).read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return (), {}
    lines = source.splitlines()
    board_role = kind if kind.startswith('reference:') else 'input:task-board.md'
    task, base = _scenario_board(repo, root, workspace, board_role, overlay)
    if task is None:
        return lines, {}
    spans = {}
    if kind == 'hidden':
        return lines, _scenario_hidden_spans(lines, task)
    for number, text in enumerate(lines, 1):
        if kind.endswith(':task-board.md'):
            match = re.fullmatch(r'\|\s*(?P<id>T-[0-9]{1,3})\s*\|[^|]*\|\s*tasks/(?P<brief>T-[0-9]{1,3})-' +
                                 re.escape(workspace) + r'\.md\s*\|[^|]*\|[^|]*\|[^|]*\|', text)
            if match and match.group('id') == match.group('brief') == task:
                spans[number] = [_group_span(match, 'id'), _group_span(match, 'brief')]
        elif kind.endswith(':history.md'):
            match = re.fullmatch(r'- In flight: (?P<id>T-[0-9]{1,3}),[^\n]*', text)
            if match and match.group('id') == task:
                spans[number] = [_group_span(match, 'id')]
        elif kind == 'input:task-heading':
            match = re.fullmatch(r'# Task (?P<id>T-[0-9]{1,3})\s+—.*', text)
            if match and match.group('id') == task and path == base + 'tasks/' + task + '-' + workspace + '.md':
                spans[number] = [_group_span(match, 'id')]
        elif kind == 'rubric' and len(text.strip()) >= 24 and text.startswith('- `task-board.md`:'):
            matches = list(ID_PATTERN.finditer(text))
            if len(matches) == 1 and matches[0].group('token') == task:
                start, end = matches[0].span('token')
                if text[start - 1:start] == '`' and text[end:end + 1] == '`':
                    spans[number] = [(start, end)]
        elif kind == 'alert':
            match = re.fullmatch(r'\s*"message"\s*:\s*"(?P<id>p(?:[1-9]|[1-9][0-9]))\s+(?P<body>[^"\\]+)"\s*,?', text)
            if match and len(list(ID_PATTERN.finditer(text))) == 1:
                try:
                    data = json.loads(source)
                except ValueError:
                    continue
                alerts = data.get('alerts') if isinstance(data, dict) else None
                expected_message = match.group('id') + ' ' + match.group('body')
                if isinstance(alerts, list) and sum(
                        isinstance(item, dict) and
                        isinstance(item.get('id'), str) and
                        bool(re.fullmatch(r'latency[-_][a-z]+', item['id'])) and
                        item.get('message') == expected_message and
                        'latency' in expected_message.lower() for item in alerts) == 1:
                    spans[number] = [_group_span(match, 'id')]
    return lines, spans


def _static_exception(path, line, counts):
    if counts.get((path, line.digest), 0) != 1:
        return False
    if path in _SEALED_COHORT_LINES:
        return (line.digest == _SEALED_LINE_HASH and
                line.text.lstrip().startswith('"decision_rule":'))
    return line.digest in _STATIC_LINE_HASHES.get(path, set())


def packaging_relocated_note(repo, base_revision):
    """Bind the single inherited citation to both historical blobs and current complete bytes."""
    repo = Path(repo)
    if (base_revision != _PREFLIGHT_BASE or (repo / _OLD_LINT_SPEC).exists() or
            (repo / _OLD_LINT_SPEC).is_symlink()):
        return None
    target = repo / _NEW_LINT_SPEC
    if not target.is_file() or target.is_symlink():
        return None
    blobs = []
    expected_blobs = [
        (_PREFLIGHT_BASE, '1ada4d66448f57942f887d588a2b3dc32ed3cc6b37b4092aaa82d602e2273c71'),
        ('v9.0.0', '5aeab0c7be0715b8b3f61e9490a4809139b8beac9d4919c9643eade49f8a3b93'),
    ]
    for revision, expected_hash in expected_blobs:
        try:
            result = subprocess.run(
                ['git', '-C', str(repo), 'show', revision + ':' + _OLD_LINT_SPEC],
                capture_output=True, check=False)
        except OSError:
            return None
        if result.returncode or hashlib.sha256(result.stdout).hexdigest() != expected_hash:
            return None
        blobs.append(result.stdout)
    current = target.read_bytes()
    if current != blobs[1]:
        return None
    for blob in [*blobs, current]:
        if sum(hashlib.sha256(item).hexdigest() == _INHERITED_LINE
               for item in blob.splitlines()) != 1:
            return None
    return _NEW_LINT_SPEC, _INHERITED_LINE


def scan_committed_text(repo, base_revision, initiative_slug):
    """Return safe metadata for added-line workspace IDs or the exact initiative slug."""
    repo = Path(repo)
    diff = _git_diff(repo, base_revision)
    additions = _added_lines(diff)
    counts = {}
    for line in additions:
        key = (line.path, line.digest)
        counts[key] = counts.get(key, 0) + 1
    relocated_note = packaging_relocated_note(repo, base_revision)
    slug_pattern = re.compile(
        r'(?<![A-Za-z0-9_])' + re.escape(initiative_slug) + r'(?![A-Za-z0-9_-]|\.[0-9])', re.IGNORECASE)
    findings = []
    build_path = 'eval/rules/fixtures/build.py'
    build_source_lines = []
    build_typed_spans = {}
    if any(line.path == build_path for line in additions):
        try:
            build_source = (repo / build_path).read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            build_source = None
        if build_source is not None:
            build_source_lines = build_source.splitlines()
            build_typed_spans = _build_gate_typed_spans(build_source)
    ledger_path = 'eval/tests/tooling/rules/test_ledger.py'
    ledger_source_lines = []
    ledger_typed_spans = {}
    if any(line.path == ledger_path for line in additions):
        try:
            ledger_source = (repo / ledger_path).read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            ledger_source = None
        if ledger_source is not None:
            ledger_source_lines = ledger_source.splitlines()
            ledger_typed_spans = _ledger_gate_typed_spans(ledger_source)
    document_paths = {
        'eval/tests/tooling/maintaining/field-report/test_unclosed_fence.py',
        'eval/tests/product/lint/rows/test_workspace_shapes.py',
        'eval/tests/tooling/validation-integrity/test_fields.py',
    }
    document_sources = {}
    for path in document_paths:
        if not any(line.path == path for line in additions):
            continue
        try:
            source = (repo / path).read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            continue
        document_sources[path] = (source.splitlines(), _document_fixture_typed_spans(path, source))
    lifecycle_paths = {
        'eval/lint/rows/fixtures/' + fixture + '/docs/plans/demo/' + document + '.md'
        for fixture in ('pass-full', 'pass-full-5')
        for document in ('resource-usage', 'history')
    } | {
        'eval/lint/rows/fixtures/pass-lite/docs/plans/demo/resource-usage.md',
        'eval/lint/rows/fixtures/pass-lite/docs/plans/demo/history.md',
        'eval/lint/rows/fixtures/fail-16-unsupported-lite/docs/plans/demo/resource-usage.md',
    }
    lifecycle_sources = {path: _lifecycle_fixture_typed_spans(repo, path)
                         for path in lifecycle_paths if any(line.path == path for line in additions)}
    scenario_sources = {path: _scenario_typed_spans(repo, path)
                        for path in {line.path for line in additions} if _scenario_role(path) is not None}
    coverage_path = 'eval/tests/product/lessons/test_coverage_table.py'
    coverage_lines, coverage_spans = (_coverage_mutation_typed_spans(repo, coverage_path)
        if any(line.path == coverage_path for line in additions) else ((), {}))
    for line in additions:
        typed_spans = _typed_id_spans(line.path, line.text)
        if line.path == build_path:
            typed_spans.extend(_build_gate_spans_for_added_line(
                line, build_source_lines, build_typed_spans))
        if line.path == ledger_path:
            typed_spans.extend(_build_gate_spans_for_added_line(
                line, ledger_source_lines, ledger_typed_spans))
        if line.path in document_sources:
            source_lines, document_spans = document_sources[line.path]
            typed_spans.extend(_build_gate_spans_for_added_line(
                line, source_lines, document_spans))
        if line.path in lifecycle_sources:
            source_lines, lifecycle_spans = lifecycle_sources[line.path]
            typed_spans.extend(_build_gate_spans_for_added_line(
                line, source_lines, lifecycle_spans))
        if line.path in scenario_sources:
            source_lines, scenario_spans = scenario_sources[line.path]
            typed_spans.extend(_build_gate_spans_for_added_line(
                line, source_lines, scenario_spans))
        if line.path == coverage_path:
            typed_spans.extend(_build_gate_spans_for_added_line(
                line, coverage_lines, coverage_spans))
        exact_exception = _static_exception(line.path, line, counts)
        inherited_exception = (relocated_note == (line.path, line.digest) and
                              counts.get((line.path, line.digest), 0) == 1)
        for match in ID_PATTERN.finditer(line.text):
            span = match.span('token')
            if span in typed_spans or exact_exception or inherited_exception:
                continue
            findings.append(Finding(line.path, line.line, 'workspace-id', match.group('token'), line.digest))
        for match in slug_pattern.finditer(line.text):
            findings.append(Finding(line.path, line.line, 'initiative-slug', match.group(0), line.digest))
    return findings


def format_findings(findings):
    """Render metadata only; never echo added source text."""
    return '\n'.join('%s:%d: %s sha256=%s' %
                     (item.path, item.line, item.kind, item.line_sha256)
                     for item in findings)
