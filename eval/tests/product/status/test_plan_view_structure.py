"""The plan view template is a layered design system with one palette and a modular page script.

The stylesheet is five cascade layers after one layer statement, its colors are primitive tokens reached through
light-dark semantic tokens, and its shared base sits in one marked range. The page script is named modules over one
context object, with no explanatory comments beyond the frozen-surface doc-comment. The checks read the template's
single html block with brace counting that skips strings and comments. Pixel parity against the previous template is
the separate acceptance script; these checks name the structure the design contract requires.
"""
import hashlib
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
TEMPLATE = REPO / 'skills/tackle/references/plan-view.template.md'
LAYER_STATEMENT = '@layer tokens, base, components, features, print;'
LAYERS = ('tokens', 'base', 'components', 'features', 'print')
BASE_START = '/* tackle-base:start */'
BASE_END = '/* tackle-base:end */'
THEME_START = '/* tackle-base-theme:start */'
THEME_END = '/* tackle-base-theme:end */'
THEME_SHA256 = '359f52f7d1ba7f040c0b5cda2e6f1273eb30efe0cca621115c147912f78ad82f'
SEMANTIC = ('--bg', '--bg2', '--surface', '--ink', '--ink2', '--mut', '--line', '--line2', '--accent', '--accent-ink',
            '--accent-soft', '--on-accent', '--grid', '--edge', '--edge-strong', '--select')
TOKEN_SELECTORS = {':root', ':root[data-theme="dark"]', ':root:not([data-theme="light"])'}
LITERAL_COLOR = re.compile(r'#[0-9a-fA-F]{3,8}\b|rgba?\(|hsl\(')
MODULES = (
    ('headerLayout', ['view']),
    ('sectionSpy', ['view']),
    ('diagramCanvases', ['view']),
    ('flowSelection', ['view', 'canvases']),
    ('stateFilters', ['view']),
    ('narrowFlow', ['view', 'canvases']),
    ('architecture', ['view', 'canvases']),
    ('decisionLog', ['view']),
    ('exportScope', ['view']),
    ('mermaidExport', ['view']),
    ('fileView', ['view']),
    ('escapeClearsSelection', ['view', 'selection', 'architecture']),
)
ROOT_CALLS = (
    'headerLayout(view);',
    'sectionSpy(view);',
    'var canvases = diagramCanvases(view);',
    'var selection = flowSelection(view, canvases);',
    'stateFilters(view);',
    'narrowFlow(view, canvases);',
    'var architectureState = architecture(view, canvases);',
    'decisionLog(view);',
    'exportScope(view);',
    'mermaidExport(view);',
    'fileView(view);',
    'escapeClearsSelection(view, selection, architectureState);',
)


def html_block(text):
    fences = re.findall(r'^```html\n(.*?)^```$', text, flags=re.S | re.M)
    if len(fences) != 1:
        raise AssertionError('the template must hold exactly one html block')
    return fences[0]


def skip_string(text, index):
    quote = text[index]
    index += 1
    while index < len(text) and text[index] != quote:
        index += 2 if text[index] == '\\' else 1
    return index + 1


def strip_comments(text):
    out, index = [], 0
    while index < len(text):
        if text.startswith('/*', index):
            index = text.index('*/', index) + 2
        elif text[index] in '"\'':
            end = skip_string(text, index)
            out.append(text[index:end])
            index = end
        else:
            out.append(text[index])
            index += 1
    return ''.join(out)


def skip_url(text, index):
    if text.startswith('url(', index):
        return text.index(')', index) + 1
    return None


def close_of(text, open_index):
    depth, index = 0, open_index
    while index < len(text):
        if text[index] in '"\'':
            index = skip_string(text, index)
            continue
        if text.startswith('/*', index):
            index = text.index('*/', index) + 2
            continue
        if text.startswith('url(', index):
            index = skip_url(text, index)
            continue
        if text[index] == '{':
            depth += 1
        elif text[index] == '}':
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise AssertionError('unbalanced braces')


class Node:
    def __init__(self, prelude, children, body):
        self.prelude = prelude
        self.children = children
        self.body = body

    def selector(self):
        return ' '.join(self.prelude.split())

    def declarations(self):
        pairs = []
        for item in split_top(self.body or ''):
            if ':' in item:
                name, value = item.split(':', 1)
                pairs.append((name.strip(), value.strip()))
        return pairs


def split_top(text):
    parts, start, index = [], 0, 0
    while index < len(text):
        if text[index] in '"\'':
            index = skip_string(text, index)
            continue
        if text.startswith('url(', index):
            index = skip_url(text, index)
            continue
        if text[index] == ';':
            parts.append(text[start:index])
            start = index + 1
        index += 1
    if text[start:].strip():
        parts.append(text[start:])
    return [part.strip() for part in parts if part.strip()]


def parse(text):
    nodes, index, start = [], 0, 0
    while index < len(text):
        char = text[index]
        if char in '"\'':
            index = skip_string(text, index)
            continue
        if text.startswith('url(', index):
            index = skip_url(text, index)
            continue
        if char == '{':
            close = close_of(text, index)
            prelude = text[start:index].strip()
            inner = text[index + 1:close]
            if prelude.startswith(('@layer', '@media')):
                nodes.append(Node(prelude, parse(inner), None))
            else:
                nodes.append(Node(prelude, None, inner))
            index = close + 1
            start = index
            continue
        if char == ';':
            prelude = text[start:index].strip()
            if prelude:
                nodes.append(Node(prelude, None, None))
            index += 1
            start = index
            continue
        index += 1
    return nodes


def walk(nodes, ancestors=()):
    for node in nodes:
        yield node, ancestors
        if node.children:
            yield from walk(node.children, ancestors + (node,))


class PlanViewStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = TEMPLATE.read_text(encoding='utf-8')
        cls.html = html_block(cls.text)
        style = cls.html[cls.html.index('<style>') + len('<style>'):cls.html.index('</style>')]
        cls.style_raw = style
        cls.style = strip_comments(style)
        cls.nodes = parse(cls.style)
        script = cls.html[cls.html.index('<script id="plan-view-controller">'):]
        cls.script = script[script.index('\n') + 1:script.index('</script>')]

    def layer_nodes(self):
        return [node for node in self.nodes if node.prelude.startswith('@layer') and node.children is not None]

    def test_layer_statement(self):
        self.assertEqual(self.style.count(LAYER_STATEMENT), 1)
        self.assertEqual(self.style_raw.count(LAYER_STATEMENT), 1)
        self.assertEqual(self.nodes[0].prelude + ';', LAYER_STATEMENT)
        names = [node.prelude.split()[1] for node in self.layer_nodes()]
        self.assertEqual(names, ['tokens', 'base', 'components', 'base', 'features', 'print'])
        self.assertEqual([node.prelude for node in self.nodes[1:] if not node.prelude.startswith('@layer')], [],
                         'a rule sits outside the layers')

    def test_tokens_hold_only_tokens_and_color_scheme(self):
        tokens = next(node for node in self.layer_nodes() if node.prelude == '@layer tokens')
        for node in tokens.children:
            if node.prelude.startswith('@font-face'):
                continue
            if node.prelude.startswith('@media'):
                self.assertEqual(node.prelude.replace(' ', ''), '@media(prefers-color-scheme:dark)')
                self.assertEqual([child.selector() for child in node.children], [':root:not([data-theme="light"])'])
                rules = node.children
            else:
                self.assertIn(node.selector(), TOKEN_SELECTORS)
                rules = [node]
            for rule in rules:
                for name, _ in rule.declarations():
                    self.assertTrue(name.startswith('--') or name == 'color-scheme', name)

    def test_each_semantic_token_is_declared_once_as_light_dark(self):
        declared = {}
        for node, _ in walk(self.nodes):
            for name, value in (node.declarations() if node.body is not None else []):
                if name in SEMANTIC:
                    declared.setdefault(name, []).append((node.selector(), value))
        self.assertEqual(sorted(declared), sorted(SEMANTIC))
        for name in SEMANTIC:
            self.assertEqual(len(declared[name]), 1, name + ' is declared more than once')
            selector, value = declared[name][0]
            self.assertEqual(selector, ':root', name)
            self.assertRegex(value, r'^light-dark\(var\(--[a-z0-9-]+\), var\(--[a-z0-9-]+\)\)$', name)

    def test_color_scheme_rules_keep_their_values(self):
        by_selector = {}
        for node, _ in walk(self.nodes):
            if node.body is not None and node.selector() in TOKEN_SELECTORS:
                by_selector.setdefault(node.selector(), []).append(node.declarations())
        root = [pairs for pairs in by_selector[':root']]
        self.assertIn(('color-scheme', 'light'), root[0])
        dark = by_selector[':root[data-theme="dark"]'][0]
        self.assertEqual([pair for pair in dark if pair[0] == 'color-scheme'], [('color-scheme', 'dark')])
        self.assertEqual([name for name, _ in dark], ['color-scheme'])
        system = by_selector[':root:not([data-theme="light"])'][0]
        self.assertEqual(system, [('color-scheme', 'dark')])

    def test_no_literal_color_outside_tokens(self):
        for node, ancestors in walk(self.nodes):
            if node.body is None or any(a.prelude == '@layer tokens' for a in ancestors):
                continue
            for name, value in node.declarations():
                self.assertIsNone(LITERAL_COLOR.search(value), node.selector() + ' ' + name + ':' + value)

    def test_one_marked_base_range_holds_the_layers_up_to_components(self):
        self.assertEqual(self.style_raw.count(BASE_START), 1)
        self.assertEqual(self.style_raw.count(BASE_END), 1)
        start = self.style_raw.index(BASE_START) + len(BASE_START)
        end = self.style_raw.index(BASE_END)
        self.assertLess(start, self.style_raw.index(LAYER_STATEMENT))
        self.assertLess(self.style_raw.index(LAYER_STATEMENT), end)
        self.assertEqual(self.style_raw[start:].lstrip().startswith(LAYER_STATEMENT), True)
        components = self.style_raw.index('@layer components{')
        self.assertLess(components, end)
        self.assertEqual(self.style_raw[close_of(self.style_raw, components) + 1:end].strip(), '')
        self.assertNotIn('@layer features{', self.style_raw[start:end])

    def test_theme_range_is_byte_identical_to_the_previous_base(self):
        start = self.script.index(THEME_START)
        end = self.script.index(THEME_END)
        between = self.script[start + len(THEME_START) + 1:end].rstrip('\n')
        self.assertEqual(hashlib.sha256(between.encode('utf-8')).hexdigest(), THEME_SHA256)

    def test_last_feature_blocks_are_the_responsive_and_reduced_motion_rules(self):
        features = next(node for node in self.layer_nodes() if node.prelude == '@layer features')
        self.assertEqual([node.prelude.replace(' ', '') for node in features.children[-2:]],
                         ['@media(max-width:420px)', '@media(prefers-reduced-motion:reduce)'])

    def test_print_link_rule_competes_inside_a_second_base_layer(self):
        raw_rule = 'a{color:inherit;text-decoration:none}'
        self.assertEqual(self.style.count(raw_rule), 1)
        matches = [(node, ancestors) for node, ancestors in walk(self.nodes)
                   if node.body is not None and node.selector() == 'a' and node.declarations() == [
                       ('color', 'inherit'), ('text-decoration', 'none')]]
        self.assertEqual(len(matches), 1)
        node, ancestors = matches[0]
        self.assertEqual([a.prelude for a in ancestors], ['@layer base', '@media print'])
        self.assertIs(ancestors[0], self.layer_nodes()[3])
        raw_position = self.style_raw.index(raw_rule)
        self.assertGreater(raw_position, self.style_raw.index(BASE_END))
        self.assertLess(raw_position, self.style_raw.index('@layer features{'))
        print_layer = next(n for n in self.layer_nodes() if n.prelude == '@layer print')
        self.assertNotIn('a', [child.selector() for child in print_layer.children if child.body is not None])

    def test_controller_is_named_modules_over_one_context(self):
        self.assertEqual(self.script.count('var view = {'), 1)
        self.assertRegex(self.script, r'\n  var view = \{ doc: doc, root: root, data: data, all: all, one: one, '
                                      r'stored: stored, setHash: setHash \};\n')
        found = re.findall(r'^  function (\w+)\(([^)]*)\) \{$', self.script, flags=re.M)
        expected = [(name, ', '.join(params)) for name, params in MODULES]
        self.assertEqual([item for item in found if item[0] in {name for name, _ in MODULES}], expected)
        root_start = self.script.rindex('\n  headerLayout(view);')
        calls = [line.strip() for line in self.script[root_start:].split('\n') if line.strip()]
        self.assertEqual(calls[:len(ROOT_CALLS)], list(ROOT_CALLS))

    def test_controller_has_one_doc_comment_and_no_other_comment(self):
        end_marker = self.script.index(THEME_END)
        before = self.script[:self.script.index(THEME_START)]
        after = self.script[end_marker + len(THEME_END):]
        comments = []
        for part in (before, after):
            index = 0
            while index < len(part):
                if part[index] in '"\'`':
                    index = skip_string(part, index)
                elif part.startswith('//', index):
                    comments.append(part[index:part.index('\n', index)])
                    index = part.index('\n', index)
                elif part.startswith('/*', index):
                    stop = part.index('*/', index) + 2
                    comments.append(part[index:stop])
                    index = stop
                else:
                    index += 1
        self.assertEqual(len(comments), 1, comments)
        self.assertTrue(comments[0].startswith('/**'), comments[0][:40])
        self.assertTrue(after.lstrip().startswith(comments[0]), 'the doc-comment is not right after the theme range')
        self.assertTrue(after[after.index(comments[0]) + len(comments[0]):].lstrip().startswith('var view = {'))


if __name__ == '__main__':
    unittest.main()
