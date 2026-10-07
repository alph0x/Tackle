"""Exercise plan export through the shipped recipe and its real print handler.

The Python fixture helpers are imported read-only from the protected plan-view
tests. The Node VM supplies only the native event/DOM surface; it does not
replace the export behavior under test or claim browser UI evidence.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


HELPER_PATH = Path(__file__).with_name('test_plan_view.py')
_spec = importlib.util.spec_from_file_location('_plan_view_export_helpers', HELPER_PATH)
HELPERS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(HELPERS)

SCOPE_ID = 'plan-export-scope'
BUTTON_ID = 'plan-export-button'
STATUS_ID = 'plan-export-status'
PLAN_REPORT_ID = 'print-report-plan'
PROGRESS_REPORT_ID = 'print-report-progress'
HANDLER_ID = 'plan-view-export-handler'
BOTH_REPORT_ID = 'print-report-both'
REPORT_IDS = {PLAN_REPORT_ID, PROGRESS_REPORT_ID, BOTH_REPORT_ID}


class ExportPageParser(HTMLParser):
    """Collect the static report text and the real inline handler from a page."""

    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
            'meta', 'param', 'source', 'track', 'wbr'}
    UNSAFE_REPORT_TAGS = {'script', 'img', 'iframe', 'object', 'embed'}

    def __init__(self):
        super().__init__()
        self.ids = []
        self.id_counts = {}
        self.options = []
        self.scope_attrs = {}
        self.scope_labelled = False
        self._in_scope_select = False
        self._in_scope_label = False
        self._handler = False
        self.handler_count = 0
        self.handler_parts = []
        self.active_report = None
        self.report_depth = 0
        self.reports = {}

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        ident = attrs.get('id')
        if ident:
            self.ids.append(ident)
            self.id_counts[ident] = self.id_counts.get(ident, 0) + 1
        if tag == 'label' and attrs.get('for') == SCOPE_ID:
            self.scope_labelled = True
        if tag == 'select' and ident == SCOPE_ID:
            self._in_scope_select = True
            self.scope_attrs = attrs
        elif tag == 'option' and self._in_scope_select:
            self.options.append(attrs.get('value'))
        elif tag == 'select' and self._in_scope_select:
            self._in_scope_select = False

        if tag == 'script' and ident == HANDLER_ID:
            self._handler = True
            self.handler_count += 1
        if self.active_report is None and ident in REPORT_IDS:
            self.active_report = ident
            self.report_depth = 1
            self.reports[ident] = {'attrs': attrs, 'text': [], 'rows': 0, 'unsafe_tags': []}
            return
        if self.active_report is not None:
            report = self.reports[self.active_report]
            if tag == 'tr':
                report['rows'] += 1
            if tag in self.UNSAFE_REPORT_TAGS:
                report['unsafe_tags'].append(tag)
            if tag not in self.VOID:
                self.report_depth += 1

    def handle_endtag(self, tag):
        if tag == 'script' and self._handler:
            self._handler = False
        if tag == 'select' and self._in_scope_select:
            self._in_scope_select = False
        if self.active_report is not None and tag not in self.VOID:
            self.report_depth -= 1
            if self.report_depth == 0:
                self.active_report = None

    def handle_data(self, data):
        if self._handler:
            self.handler_parts.append(data)
        if self.active_report is not None:
            self.reports[self.active_report]['text'].append(data)

    @property
    def handler_source(self):
        return ''.join(self.handler_parts)

    def report_text(self, ident):
        return ' '.join(self.reports[ident]['text'])


def parse_export_page(page):
    parser = ExportPageParser()
    parser.feed(page)
    parser.close()
    return parser


def render_page(files, case):
    with tempfile.TemporaryDirectory() as tmp:
        result, page = HELPERS.page_of(tmp, files, case)
    return result, page


def obligation_id(number):
    return 'O-%02d' % number


def large_progress_files(count=200):
    requirement = HELPERS.req_id(1)
    plan = ('# Plan — Export proof\n\nThe export contains the complete plan and authoritative progress.\n\n'
            '| Criterion | Required behavior |\n|---|---|\n| `%s` | Preserve every task row and its verification. |\n' % requirement)
    board = HELPERS.BOARD_HEAD
    for number in range(1, count + 1):
        task = HELPERS.task_id(number)
        dependency = 'none' if number == 1 else HELPERS.task_id(number - 1)
        status = 'Complete' if number == 1 else 'Draft'
        verification = 'verify-%03d%s' % (number, '-final-sentinel' if number == count else '')
        title = 'task-%03d%s' % (number, '-long-cell sentinel ' * 8 if number == count else '')
        board += '| %s | %s | `tasks/brief.md` | %s | %s | %s |\n' % (
            task, title, dependency, status, verification)
    open_obligation, closed_obligation = obligation_id(41), obligation_id(42)
    board += ('\n## Obligations\n\n'
              '| Obligation | What | Owner | Trigger | State | Discharge check | Reference |\n'
              '|---|---|---|---|---|---|---|\n'
              '| %s | open-obligation-sentinel | %s | export review | Open | include in report | %s |\n'
              '| %s | discharged-control-sentinel | %s | export review | Discharged | already done | %s |\n' % (
                  open_obligation, HELPERS.task_id(18), HELPERS.decision_id(91),
                  closed_obligation, HELPERS.task_id(18), HELPERS.decision_id(90)))
    base = HELPERS.workspace_files()
    files = {
        'plan.md': plan,
        'task-board.md': board,
        'tasks/brief.md': '# Shared brief\n\n- **Traces to**: %s\n- **Goal**: prove complete export membership.\n' % requirement,
        'history.md': ('# History\n\n### State snapshot\n- old-snapshot-sentinel\n\n'
                       '## Later\n\n### State snapshot\n- newest-snapshot-sentinel\n- Active obligations: %s\n' % open_obligation),
        'AGENTS.md': base['AGENTS.md'],
        'decisions.md': base['decisions.md'],
        'resource-usage.md': (base['resource-usage.md'] +
            HELPERS.usage_row('run/export', 'start', HELPERS.task_id(200), 'coordinator')),
    }
    return files


NODE_HANDLER_HARNESS = r'''const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(process.argv[2], 'utf8');
const windowListeners = Object.create(null);
let nextMode = 'complete';
const scopes = [];
const during = [];
function element(name, attrs) {
  return {
    name,
    attrs: Object.assign({}, attrs || {}),
    value: 'both',
    textContent: '',
    listeners: Object.create(null),
    addEventListener(type, fn) {
      (this.listeners[type] || (this.listeners[type] = [])).push(fn);
    },
    dispatch(type, event) {
      (this.listeners[type] || []).forEach((fn) => fn(event || { preventDefault() {} }));
    },
    getAttribute(key) { return Object.prototype.hasOwnProperty.call(this.attrs, key) ? this.attrs[key] : null; },
    setAttribute(key, value) { this.attrs[key] = String(value); },
    removeAttribute(key) { delete this.attrs[key]; },
    focus() { document.activeElement = this; }
  };
}
const root = element('root', { 'data-print-scope': 'prior-root-scope' });
const body = element('body');
const scope = element('scope');
const button = element('button');
const status = element('status');
const originalFocus = element('previous-focus');
const printDialogFocus = element('native-print-dialog');
const elements = {
  'plan-export-scope': scope,
  'plan-export-button': button,
  'plan-export-status': status
};
const document = {
  title: 'Original workspace title',
  documentElement: root,
  body,
  activeElement: originalFocus,
  getElementById(id) { return elements[id] || null; }
};
function dispatchWindow(type) {
  (windowListeners[type] || []).forEach((fn) => fn());
}
const window = {
  addEventListener(type, fn) { (windowListeners[type] || (windowListeners[type] = [])).push(fn); },
  print() {
    if (nextMode === 'deferred') return;
    dispatchWindow('beforeprint');
    document.activeElement = printDialogFocus;
    scopes.push(root.getAttribute('data-print-scope'));
    during.push({ title: document.title, printing: body.getAttribute('data-printing') });
    if (nextMode === 'throw') throw new Error('native print failed');
    if (nextMode !== 'cancel') dispatchWindow('afterprint');
  }
};
vm.runInNewContext(source, { window, document });
function state() {
  return {
    title: document.title,
    rootScope: root.getAttribute('data-print-scope'),
    bodyPrinting: body.getAttribute('data-printing'),
    focus: document.activeElement && document.activeElement.name
  };
}
const restored = [];
let errorStatus = '';
function exportScope(value, mode) {
  scope.value = value;
  document.activeElement = button;
  const expected = state();
  nextMode = mode;
  button.dispatch('click', { preventDefault() {} });
  if (mode === 'cancel') dispatchWindow('afterprint');
  if (mode === 'throw') errorStatus = status.textContent;
  restored.push(JSON.stringify(state()) === JSON.stringify(expected));
}
function deferredExport(value) {
  scope.value = value;
  document.activeElement = button;
  const expected = state();
  nextMode = 'deferred';
  button.dispatch('click', { preventDefault() {} });
  dispatchWindow('beforeprint');
  document.activeElement = printDialogFocus;
  scopes.push(root.getAttribute('data-print-scope'));
  during.push({ title: document.title, printing: body.getAttribute('data-printing') });
  dispatchWindow('afterprint');
  restored.push(JSON.stringify(state()) === JSON.stringify(expected));
}
exportScope('plan', 'complete');
exportScope('progress', 'cancel');
exportScope('both', 'throw');
exportScope('plan', 'complete');
deferredExport('progress');
document.activeElement = originalFocus;
const ordinaryExpected = state();
nextMode = 'complete';
window.print();
restored.push(JSON.stringify(state()) === JSON.stringify(ordinaryExpected));
console.log(JSON.stringify({ scopes, during, restored, errorStatus }));
'''


def executive_narrative():
    return {
        'context': 'Reader context: this plan helps a team carry work across sessions.',
        'purpose': 'Keep progress clear and prepare a reliable release.',
        'plan': {
            'themes': [{'title': 'Continuity benefit', 'text': 'Keep your place between sessions.'}],
            'scope': {'included': ['Clear project history'], 'deferred': ['A separate live research campaign']},
            'roadmap': [{'title': 'Build the foundations', 'text': 'Prepare the tools before refining the presentation.'}],
            'key_choices': [{'title': 'Current choice', 'text': 'Separate release checks from future live research.'}],
        },
        'progress': {
            'completed': 999, 'total': 999,
            'achievements': [{'title': 'Foundation ready', 'text': 'The completed local work is recorded.'}],
            'open_work': [{'title': 'Next work', 'text': 'Finish the remaining presentation work.'}],
            'next': ['Review the presentation before release'],
            'evidence': 'Local checks cover the recorded scope; live behavior remains unmeasured.',
        },
    }


class PlanViewExportTests(unittest.TestCase):
    def test_executive_export_has_context_and_preserves_the_technical_source(self):
        full = HELPERS.workspace_files()
        narrative = executive_narrative()
        full['view/export-summary.json'] = json.dumps(narrative)
        full['plan.md'] += (
            '\n## Late section — café Ω\n\nlate-plan-sentinel\n\n'
            '- late-list-sentinel\n\n'
            '```text\nlate-code-sentinel\n```\n\n'
            '| left | right |\n|---|---|\n| escaped\\|pipe-sentinel | late-table-sentinel |\n')
        with tempfile.TemporaryDirectory() as tmp:
            result, out = HELPERS.run_recipe(tmp, full, 'full-export')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertEqual((out.parent / 'plan.md').read_text(encoding='utf-8'), full['plan.md'])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        parsed = parse_export_page(page)
        self.assertIn(PLAN_REPORT_ID, parsed.reports, 'the actual recipe must build a plan report')
        plan_text = parsed.report_text(PLAN_REPORT_ID)
        for sentinel in ('late-plan-sentinel', 'late-list-sentinel', 'late-code-sentinel',
                         'pipe-sentinel', 'late-table-sentinel', HELPERS.req_id(1)):
            with self.subTest(sentinel=sentinel):
                self.assertNotIn(sentinel, plan_text)
        for ident in REPORT_IDS:
            text = parsed.report_text(ident)
            self.assertEqual(text.count(narrative['context']), 1)
            self.assertIn(narrative['purpose'], text)
        for ident in (PLAN_REPORT_ID, BOTH_REPORT_ID):
            self.assertIn('Continuity benefit', parsed.report_text(ident))
            self.assertIn('Current choice', parsed.report_text(ident))
        self.assertNotIn('Foundation ready', plan_text)
        self.assertNotIn('Current choice', parsed.report_text(PROGRESS_REPORT_ID))
        self.assertIn('Foundation ready', parsed.report_text(BOTH_REPORT_ID))
        self.assertEqual(set(parsed.options), {'plan', 'progress', 'both'})
        self.assertIn(BUTTON_ID, parsed.ids)
        self.assertTrue(parsed.scope_attrs.get('aria-label') or parsed.scope_labelled,
                        'the scope choices need a programmatic label')
        self.assertIn('Save as PDF', HELPERS.visible_text(page))

        lite_plan = ('Gate: Lite\n' + HELPERS.SPANISH_PLAN + HELPERS.lite_plan().split('Gate: Lite\n', 1)[1])
        lite_files = {'plan.md': lite_plan, 'history.md': '# History\n'}
        result, lite_page = render_page(lite_files, 'lite-export')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lite = parse_export_page(lite_page)
        self.assertIn(PLAN_REPORT_ID, lite.reports)
        self.assertIn(PROGRESS_REPORT_ID, lite.reports)
        lite_plan_text = lite.report_text(PLAN_REPORT_ID)
        progress_text = lite.report_text(PROGRESS_REPORT_ID)
        self.assertIn('Ready', progress_text)
        self.assertNotIn('pytest tests/test_parser.py', progress_text)
        self.assertNotIn('This export presents', progress_text)
        self.assertNotRegex(progress_text, r'\bT-\d+\b|\b\d+%')
        self.assertNotIn('Gate: Lite', lite_page)
        self.assertIn('Guardar como PDF', HELPERS.visible_text(lite_page))

    def test_executive_progress_uses_canonical_aggregates_with_or_without_curation(self):
        for curated in (False, True, 'invalid-shape', 'unsupported-schema', 'planned-only-zero'):
            with self.subTest(curated=curated):
                files = large_progress_files()
                if curated is True:
                    files['view/export-summary.json'] = json.dumps(executive_narrative())
                elif curated == 'invalid-shape':
                    files['view/export-summary.json'] = json.dumps({'context': 42, 'plan': [], 'progress': 'invalid'})
                elif curated == 'unsupported-schema':
                    files['view/export-summary.json'] = json.dumps({'schema': 'unsupported/999', 'context': 'unsupported-context-sentinel'})
                elif curated == 'planned-only-zero':
                    files['task-board.md'] = files['task-board.md'].replace('| Complete |', '| Draft |')
                    files['view/summary.json'] = json.dumps({'outcomes': [{'title': 'Planned-only benefit', 'text': 'planned-only-outcome-sentinel'}]})
                completed = 0 if curated == 'planned-only-zero' else 1
                result, page = render_page(files, 'aggregate-export-' + str(curated))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                parsed = parse_export_page(page)
                for ident in REPORT_IDS:
                    self.assertEqual(parsed.id_counts.get(ident), 1)
                for ident in (PROGRESS_REPORT_ID, BOTH_REPORT_ID):
                    report = parsed.reports[ident]
                    progress = parsed.report_text(ident)
                    self.assertEqual(report['attrs'].get('data-completed'), str(completed))
                    self.assertEqual(report['attrs'].get('data-total'), '200')
                    self.assertRegex(progress, rf'\b{completed}\s+(?:of|/)\s+200\b')
                    expected_states = {'Draft': 200} if completed == 0 else {'Complete': 1, 'Draft': 199}
                    self.assertEqual(json.loads(report['attrs']['data-state-counts']), expected_states)
                    self.assertRegex(progress, rf'\bDraft\s*:?\s*{200-completed}\b')
                    for raw in ('verify-200-final-sentinel', 'newest-snapshot-sentinel',
                                'old-snapshot-sentinel', 'discharged-control-sentinel'):
                        self.assertNotIn(raw, progress)
                    self.assertNotIn('999', progress)
                    self.assertLess(report['rows'], 20)
                    self.assertLess(len(re.findall(r'\btask-\d{3}', progress)), 20,
                                    'a large board needs an overview, not hundreds of repeated task titles')
                    self.assertNotIn('unsupported-context-sentinel', progress)
                    self.assertEqual(report['unsafe_tags'], [])
                if curated == 'planned-only-zero':
                    self.assertNotIn('planned-only-outcome-sentinel', parsed.report_text(PROGRESS_REPORT_ID))

    def test_actual_recipe_escapes_hostile_report_text_and_refuses_invalid_overwrite(self):
        payload = '<img src=x onerror=alert(77)>'
        files = HELPERS.workspace_files()
        narrative = executive_narrative()
        narrative['context'] = payload
        narrative['purpose'] = payload
        narrative['plan']['themes'][0]['text'] = payload
        narrative['progress']['evidence'] = payload
        files['view/export-summary.json'] = json.dumps(narrative)
        files['plan.md'] = files['plan.md'].replace('# Action plan — demo', '# Export ' + payload)
        files['plan.md'] += '\n## Hostile code\n\n```html\n</script><script>alert(77)</script>\n```\n'
        files['task-board.md'] = files['task-board.md'].replace(HELPERS.ATTR, payload)
        files['task-board.md'] = files['task-board.md'].replace('| Complete | v |', '| Complete | ' + payload + ' |', 1)
        files['history.md'] += '\n' + payload
        task = HELPERS.task_id(1)
        files['resource-usage.md'] += HELPERS.usage_row('run/hostile', 'start', task, payload)
        files['task-board.md'] += (
            '\n## Obligations\n\n'
            '| Obligation | What | Owner | Trigger | State | Discharge check | Reference |\n'
            '|---|---|---|---|---|---|---|\n'
            '| %s | %s | %s | export | Open | include | %s |\n' % (
                obligation_id(41), payload, task, HELPERS.decision_id(91)))
        result, page = render_page(files, 'hostile-export')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        parsed = parse_export_page(page)
        self.assertIn(PLAN_REPORT_ID, parsed.reports)
        self.assertIn(PROGRESS_REPORT_ID, parsed.reports)
        self.assertNotIn(payload, page, 'workspace payload must be encoded in HTML and JSON contexts')
        self.assertNotIn('</script><script>alert(77)', page)
        for ident in REPORT_IDS:
            with self.subTest(report=ident):
                self.assertIn(payload, parsed.report_text(ident))
                self.assertEqual(parsed.reports[ident]['unsafe_tags'], [])
        self.assertNotRegex(page, r'<script\b[^>]*\bsrc=|<link\b[^>]*\bhref=')
        self.assertNotIn('fonts.googleapis', page)

        invalid = HELPERS.workspace_files()
        invalid['task-board.md'] = '# no task rows\n'
        sentinel = 'previous printable output must survive refusal\n'
        invalid['plan-view.html'] = sentinel
        with tempfile.TemporaryDirectory() as tmp:
            result, out = HELPERS.run_recipe(tmp, invalid, 'invalid-export')
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(out.read_text(encoding='utf-8'), sentinel)

    def test_real_handler_restores_title_attributes_and_focus_for_print_lifecycle(self):
        result, page = render_page(HELPERS.workspace_files(), 'handler-export')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        parsed = parse_export_page(page)
        self.assertEqual(parsed.handler_count, 1, 'execute the single handler shipped in the generated page')
        self.assertTrue(parsed.handler_source.strip(), 'the shipped export handler must be present')
        self.assertIn(BUTTON_ID, parsed.ids)
        self.assertIn(STATUS_ID, parsed.ids, 'print errors need an accessible status target')
        node = os.environ.get('TACKLE_NODE') or shutil.which('node')
        if node and not Path(node).is_file():
            node = shutil.which(node)
        self.assertTrue(node and Path(node).is_file(),
                        'an existing Node interpreter is required; do not silently skip handler checks')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = root / 'handler.js'
            harness = root / 'harness.js'
            handler.write_text(parsed.handler_source, encoding='utf-8')
            harness.write_text(NODE_HANDLER_HARNESS, encoding='utf-8')
            result = subprocess.run([node, str(harness), str(handler)], capture_output=True,
                                    text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        state = json.loads(result.stdout)
        self.assertEqual(state['scopes'], ['plan', 'progress', 'both', 'plan', 'progress', 'both'])
        self.assertEqual(state['restored'], [True, True, True, True, True, True])
        self.assertEqual(len(state['during']), 6)
        self.assertTrue(all(item['printing'] == 'true' for item in state['during']))
        self.assertTrue(all(item['title'] != 'Original workspace title' for item in state['during']))
        self.assertTrue(state['errorStatus'], 'a native print exception must be reported')
