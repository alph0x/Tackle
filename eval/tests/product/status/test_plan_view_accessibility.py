"""The plan view's text and state marks meet WCAG AA contrast in both themes, text colors come only from text tokens, and its interactive elements work from the keyboard.

The contrast and usage checks read the shipped template: they resolve each semantic token for light and dark, composite translucent tokens over their background and list every text color declaration outside the token layer. The keyboard checks run the shipped controller through the minimal DOM the status suites share. Layout, painting and the full keyboard walk are outside these checks.
"""
import re
import tempfile
import unittest
from pathlib import Path

from plan_view_dom import run_scenario
from test_architecture_map import base_map, delta_of, run_view
from test_plan_view import TEMPLATE

MODES = ('light', 'dark')
TEXT_FLOOR = 4.5
NON_TEXT_FLOOR = 3.0
TEXT_PAIRS = [(foreground, backdrop) for foreground in ('ink', 'ink2', 'mut', 'accent-ink') for backdrop in ('bg', 'bg2', 'surface')]
TEXT_PAIRS += [('on-accent', 'accent'), ('bg', 'ink')]
NON_TEXT_PAIRS = [(foreground, backdrop) for foreground in ('edge', 'line2', 'mut') for backdrop in ('bg', 'surface')]
ARCHITECTURE_STROKE = re.compile(r'#architecture \.anode>rect\{[^}]*stroke:color-mix\(in srgb,var\(--ink\) (\d+)%,transparent\)')
TEXT_VALUES = {'var(--ink)', 'var(--ink2)', 'var(--mut)', 'var(--accent-ink)', 'var(--on-accent)', 'var(--bg)', 'currentColor', 'inherit'}
TEXT_COMPOUNDS = {'.nt', '.nid', '.band-h', '.band-c', '.agroup-head', '.agroup-count', '.component-kicker', '.ant', '.aelabel', '.aelabel.on'}
COLOR_DECLARATION = re.compile(r'(?<![-\w])(color|fill)\s*:([^;]*)')
RING_DECLARATION = re.compile(r'(?<![-\w])(stroke|border|border-color|outline|outline-color)\s*:(?!\s*none)')
FOCUS_TARGETS = ('.flow-svg .node:focus-visible', '#architecture .anode:focus-visible', '.lens-node:focus-visible')
CHANGED_PRIMITIVES = ('--ink-edge', '--chalk-edge', '--stone-400', '--night-600')
REFERENCE_COLORS = {
    '--stone-100': '#eff0ed', '--stone-200': '#e6e8e4', '--stone-300': '#d0d4d1', '--stone-400': '#adb2b0', '--paper': '#fafaf8',
    '--graphite-900': '#111315', '--graphite-700': '#3b4046', '--graphite-500': '#62686f',
    '--orange-600': '#f24a00', '--orange-800': '#ad3300', '--orange-100': '#fbdccd',
    '--night-950': '#0e1012', '--night-900': '#15181b', '--night-850': '#161a1d', '--night-700': '#2b3035', '--night-600': '#495057',
    '--chalk-100': '#eceeea', '--chalk-300': '#b9bdbf', '--chalk-500': '#8d9399',
    '--orange-500': '#ff5c1f', '--orange-300': '#ff8a57', '--ember-950': '#3a1d10',
    '--ink-grid': 'rgba(17,19,21,.06)', '--ink-edge': 'rgba(17,19,21,.36)',
    '--chalk-grid': 'rgba(236,238,234,.05)', '--chalk-edge': 'rgba(236,238,234,.32)',
    '--white': '#ffffff', '--black': '#000', '--rule-print': '#c9cdca',
    '--bg': 'light-dark(var(--stone-100), var(--night-950))',
    '--bg2': 'light-dark(var(--stone-200), var(--night-900))',
    '--surface': 'light-dark(var(--paper), var(--night-850))',
    '--ink': 'light-dark(var(--graphite-900), var(--chalk-100))',
    '--ink2': 'light-dark(var(--graphite-700), var(--chalk-300))',
    '--mut': 'light-dark(var(--graphite-500), var(--chalk-500))',
    '--line': 'light-dark(var(--stone-300), var(--night-700))',
    '--line2': 'light-dark(var(--stone-400), var(--night-600))',
    '--accent': 'light-dark(var(--orange-600), var(--orange-500))',
    '--accent-ink': 'light-dark(var(--orange-800), var(--orange-300))',
    '--accent-soft': 'light-dark(var(--orange-100), var(--ember-950))',
    '--on-accent': 'light-dark(var(--graphite-900), var(--night-950))',
    '--grid': 'light-dark(var(--ink-grid), var(--chalk-grid))',
    '--edge': 'light-dark(var(--ink-edge), var(--chalk-edge))',
    '--edge-strong': 'light-dark(var(--graphite-900), var(--chalk-100))',
    '--select': 'light-dark(var(--graphite-900), var(--chalk-100))',
}


def read_template(path=TEMPLATE):
    return Path(path).read_text(encoding='utf-8')


def layer_bodies(text, name):
    bodies = []
    for opening in re.finditer(r'@layer %s\s*\{' % name, text):
        depth, index = 1, opening.end()
        while depth:
            depth += {'{': 1, '}': -1}.get(text[index], 0)
            index += 1
        bodies.append(text[opening.end():index - 1])
    return bodies


def selectors_and_declarations(body):
    for selector, declarations in re.findall(r'([^{}]+)\{([^{}]*)\}', body):
        yield [part.strip() for part in selector.split(',') if part.strip()], declarations


def all_rules(text, layers=('base', 'components', 'features')):
    return [rule for name in layers for body in layer_bodies(text, name) for rule in selectors_and_declarations(body)]


def root_tokens(text):
    tokens = ''.join(layer_bodies(text, 'tokens'))
    root = re.search(r':root\s*\{([^}]*)\}', tokens).group(1)
    return {name: value.strip() for name, value in re.findall(r'(--[a-z0-9-]+)\s*:([^;]+);', root)}


def split_arguments(text):
    parts, depth, current = [], 0, ''
    for char in text:
        if char == ',' and depth == 0:
            parts.append(current.strip())
            current = ''
            continue
        depth += {'(': 1, ')': -1}.get(char, 0)
        current += char
    parts.append(current.strip())
    return parts


def color_of(value, tokens, mode):
    value = value.strip()
    dynamic = re.fullmatch(r'light-dark\((.*)\)', value, re.S)
    if dynamic:
        light, dark = split_arguments(dynamic.group(1))
        return color_of(dark if mode == 'dark' else light, tokens, mode)
    reference = re.fullmatch(r'var\((--[a-z0-9-]+)\)', value)
    if reference:
        return color_of(tokens[reference.group(1)], tokens, mode)
    hexadecimal = re.fullmatch(r'#([0-9a-f]{6})', value)
    if hexadecimal:
        digits = hexadecimal.group(1)
        return tuple(int(digits[index:index + 2], 16) for index in (0, 2, 4)) + (1.0,)
    rgba = re.fullmatch(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\.\d+|\d+(?:\.\d+)?)\s*\)', value)
    if rgba:
        red, green, blue, alpha = rgba.groups()
        return (int(red), int(green), int(blue), float(alpha))
    raise ValueError('unsupported color value: %s' % value)


def over(color, backdrop):
    alpha = color[3]
    return tuple(alpha * channel + (1 - alpha) * under for channel, under in zip(color[:3], backdrop[:3])) + (1.0,)


def luminance(color):
    channels = []
    for value in color[:3]:
        scaled = value / 255
        channels.append(scaled / 12.92 if scaled <= 0.03928 else ((scaled + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(first, second):
    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def hue(color):
    red, green, blue = (channel / 255 for channel in color[:3])
    high, low = max(red, green, blue), min(red, green, blue)
    spread = high - low
    if spread == 0:
        return 0.0
    if high == red:
        sector = ((green - blue) / spread) % 6
    elif high == green:
        sector = (blue - red) / spread + 2
    else:
        sector = (red - green) / spread + 4
    return sector * 60


def hue_gap(first, second):
    gap = abs(hue(first) - hue(second)) % 360
    return min(gap, 360 - gap)


def pair_ratio(tokens, foreground, backdrop, mode):
    under = color_of(tokens['--' + backdrop], tokens, mode)
    return contrast(over(color_of(tokens['--' + foreground], tokens, mode), under), under)


def architecture_stroke_ratio(text, tokens, mode, backdrop):
    percent = int(ARCHITECTURE_STROKE.search(text).group(1))
    under = color_of(tokens['--' + backdrop], tokens, mode)
    ink = color_of(tokens['--ink'], tokens, mode)[:3] + (percent / 100,)
    return contrast(over(ink, under), under)


def contrast_report(text):
    tokens = root_tokens(text)
    report = {}
    for mode in MODES:
        for foreground, backdrop in TEXT_PAIRS:
            report[('text', foreground, backdrop, mode)] = pair_ratio(tokens, foreground, backdrop, mode)
        for foreground, backdrop in NON_TEXT_PAIRS:
            report[('non-text', foreground, backdrop, mode)] = pair_ratio(tokens, foreground, backdrop, mode)
        for backdrop in ('bg', 'surface'):
            report[('non-text', 'architecture-stroke', backdrop, mode)] = architecture_stroke_ratio(text, tokens, mode, backdrop)
    return report


def floor_failures(text):
    floors = {'text': TEXT_FLOOR, 'non-text': NON_TEXT_FLOOR}
    return {key: ratio for key, ratio in contrast_report(text).items() if ratio < floors[key[0]]}


def is_text_selector(selector):
    compound = re.split(r'[\s>+~]+', selector.strip())[-1]
    return bool(re.match(r'text([.:#\[]|$)', compound)) or compound in TEXT_COMPOUNDS


def text_color_violations(text):
    found = []
    for selectors, declarations in all_rules(text):
        for prop, raw in COLOR_DECLARATION.findall(declarations):
            if prop == 'fill' and not any(is_text_selector(selector) for selector in selectors):
                continue
            value = ''.join(re.sub(r'\s*!important\s*$', '', raw.strip()).split())
            if value not in TEXT_VALUES:
                found.append((prop, ', '.join(selectors), value))
    return found


HELPERS = r"""
const keyed = (env, selector, attribute, value) => env.one(selector + '[' + attribute + '="' + value + '"]');
"""


class PlanViewAccessibilityTests(unittest.TestCase):
    page = None

    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as tmp:
            result, page, _ = run_view(tmp, 'keyboard', delta_of(), base=base_map())
        assert result.returncode == 0, result.stdout + result.stderr
        cls.page = page

    def scenario(self, code):
        result = run_scenario(self.page, HELPERS + code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'OK', result.stderr)

    def test_text_pairs_meet_the_text_floor_in_both_themes(self):
        below = {key: ratio for key, ratio in contrast_report(read_template()).items() if key[0] == 'text' and ratio < TEXT_FLOOR}
        self.assertEqual(below, {})

    def test_non_text_marks_meet_the_non_text_floor_in_both_themes(self):
        below = {key: ratio for key, ratio in contrast_report(read_template()).items()
                 if key[0] == 'non-text' and key[1] != 'architecture-stroke' and ratio < NON_TEXT_FLOOR}
        self.assertEqual(below, {})

    def test_architecture_node_stroke_meets_the_non_text_floor_in_both_themes(self):
        below = {key: ratio for key, ratio in contrast_report(read_template()).items()
                 if key[1] == 'architecture-stroke' and ratio < NON_TEXT_FLOOR}
        self.assertEqual(below, {})

    def test_lightened_mut_is_reported_below_the_text_floor(self):
        original = read_template()
        lightened = original.replace('--graphite-500:#62686f', '--graphite-500:#8a9096')
        self.assertNotEqual(lightened, original)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / 'plan-view.template.md'
            copy.write_text(lightened, encoding='utf-8')
            failures = floor_failures(read_template(copy))
        self.assertIn(('text', 'mut', 'bg', 'light'), failures)
        self.assertLess(failures[('text', 'mut', 'bg', 'light')], TEXT_FLOOR)

    def test_text_colors_come_only_from_text_tokens(self):
        self.assertEqual(text_color_violations(read_template()), [])

    def test_accent_as_text_is_reported(self):
        original = read_template()
        accented = original.replace('gap:10px;margin:0;color:var(--accent-ink)', 'gap:10px;margin:0;color:var(--accent)', 1)
        self.assertNotEqual(accented, original)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / 'plan-view.template.md'
            copy.write_text(accented, encoding='utf-8')
            violations = text_color_violations(read_template(copy))
        self.assertIn(('color', '.kicker', 'var(--accent)'), violations)

    def test_literal_text_color_in_a_feature_rule_is_reported(self):
        original = read_template()
        literal = original.replace('@layer features{', '@layer features{\n.probe-literal{color:#62686f}', 1)
        self.assertNotEqual(literal, original)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / 'plan-view.template.md'
            copy.write_text(literal, encoding='utf-8')
            violations = text_color_violations(read_template(copy))
        self.assertIn(('color', '.probe-literal', '#62686f'), violations)

    def test_only_failing_tokens_change_and_each_changed_primitive_keeps_its_hue(self):
        tokens = root_tokens(read_template())
        for name, reference in REFERENCE_COLORS.items():
            if name not in CHANGED_PRIMITIVES:
                self.assertEqual(tokens[name], reference, name)
        for name in CHANGED_PRIMITIVES:
            gap = hue_gap(color_of(REFERENCE_COLORS[name], {}, 'light'), color_of(tokens[name], tokens, 'light'))
            self.assertLessEqual(gap, 1.0, name)

    def test_focus_rings_change_a_stroke_border_or_outline(self):
        rules = all_rules(read_template())
        for target in FOCUS_TARGETS:
            with self.subTest(target=target):
                declarations = [body for selectors, body in rules if any(target in selector for selector in selectors)]
                self.assertTrue(any(RING_DECLARATION.search(body) for body in declarations))

    def test_enter_on_a_task_node_selects_that_task(self):
        self.scenario(r"""
const env = load();
const node = env.one('.flow-svg .node');
assert.ok(node, 'the keyboard page has a task node');
const task = node.getAttribute('data-task');
node.key('Enter');
assert.strictEqual(env.root.getAttribute('data-selected-task'), task);
""")

    def test_space_on_an_architecture_card_selects_it(self):
        self.scenario(r"""
const env = load();
const card = env.one('.acard');
assert.ok(card, 'the keyboard page has an architecture card');
const cid = card.getAttribute('data-cid');
card.key(' ');
assert.ok(keyed(env, '.acard', 'data-cid', cid).classList.contains('sel'));
""")

    def test_escape_clears_the_task_and_component_selection(self):
        self.scenario(r"""
const env = load();
const node = env.one('.flow-svg .node');
assert.ok(node, 'the keyboard page has a task node');
node.key('Enter');
assert.ok(env.root.getAttribute('data-selected-task'));
const card = env.one('.acard');
assert.ok(card, 'the keyboard page has an architecture card');
const cid = card.getAttribute('data-cid');
card.key(' ');
assert.ok(keyed(env, '.acard', 'data-cid', cid).classList.contains('sel'));
env.root.key('Escape');
assert.strictEqual(env.root.getAttribute('data-selected-task'), null);
assert.strictEqual(env.all('.acard.sel').length, 0);
""")


if __name__ == '__main__':
    unittest.main()
