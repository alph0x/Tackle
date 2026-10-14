"""An authorized auxiliary page built with the plan-view recipe's page mode inherits the plan view's visual base.

The base is the marked part of the shipped template: the CSS between the base markers and the theme script between
the theme markers. The page is one self-contained file that carries the template's tokens, top bar, toggle and theme
script; product samples keep their own markup and declare their own colors. The tests run the recipe's page mode as
a child process, check the page's bytes and its read-only check, and run the page's theme script under Node with a
small DOM stub. Visual review of the rendered page is outside these oracles. Fixture ids are built at run time.
"""
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from eval.tests.product.status.test_plan_view import RECIPE, TEMPLATE, recipe_source, run_recipe, workspace_files

RECIPE_OVERRIDE = None
MARKER = re.compile(r'/\* tackle-base(?:-theme)?:(?:start|end) \*/\n')
SPANISH_PLAN = ('# Plan — Migración\n\nEl plan describe los pasos de la migración. Cada tarea tiene una verificación. '
                'La configuración queda lista después de la revisión.\n')
ALLOWED_UNSCOPED = {':root', ':root[data-theme="dark"]', ':root:not([data-theme="light"])', '*', '*::before',
                    '*::after', 'html', 'body', '::selection', 'a', 'button', 'select', 'input', 'code', 'pre',
                    '[hidden]', ':focus-visible', 'main', 'h3', 'h4', 'h5'}
# Base rules that are not unscoped but name no class on their last compound. Each is reviewed: the top-bar navigation
# and theme-toggle rules style controls no page fragment contains, and the section heading rule is the one the page's
# heading block uses (a sample inside a heading block takes that heading's size, by design).
ALLOWED_REACH = ALLOWED_UNSCOPED | {'.theme-toggle svg', '.nav a', '.nav a:hover', '.nav a[aria-current="true"]',
                                    '.sec-head h2'}
SAMPLE = ('<div class="tk-sample"><span style="background:#0f380f;color:#9bbc0f">a</span>'
          '<span style="background:#9bbc0f;color:#0f380f">b</span></div>')
FRAGMENT = '<h1>Palette proposals</h1>\n<p>Two options.</p>\n'
NODE_HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(process.argv[2], 'utf8');
function environment(initial) {
  const attrs = {};
  const storage = {};
  if (initial) { storage['tackle-plan-view-theme'] = initial; }
  const root = {
    classList: { add() {}, remove() {} },
    getAttribute(name) { return Object.prototype.hasOwnProperty.call(attrs, name) ? attrs[name] : null; },
    setAttribute(name, value) { attrs[name] = String(value); },
  };
  const handlers = {};
  const toggle = { addEventListener(type, fn) { handlers[type] = fn; } };
  const document = { documentElement: root, getElementById(id) { return id === 'theme' ? toggle : null; } };
  const window = {
    localStorage: {
      getItem(key) { return Object.prototype.hasOwnProperty.call(storage, key) ? storage[key] : null; },
      setItem(key, value) { storage[key] = String(value); },
      removeItem(key) { delete storage[key]; },
    },
    matchMedia() { return { matches: false }; },
  };
  const context = { document, window, console, location: { pathname: '/aux.html', search: '' } };
  vm.createContext(context);
  vm.runInContext(source, context);
  return { attrs, storage, handlers };
}
const result = { fresh: null, afterFirst: null, storedFirst: null, afterSecond: null, storedSecond: null, startDark: null };
let env = environment(null);
result.fresh = env.attrs['data-theme'] === undefined ? null : env.attrs['data-theme'];
env.handlers.click();
result.afterFirst = env.attrs['data-theme'];
result.storedFirst = env.storage['tackle-plan-view-theme'] === undefined ? null : env.storage['tackle-plan-view-theme'];
env.handlers.click();
result.afterSecond = env.attrs['data-theme'];
result.storedSecond = env.storage['tackle-plan-view-theme'] === undefined ? null : env.storage['tackle-plan-view-theme'];
env = environment('dark');
result.startDark = env.attrs['data-theme'] === undefined ? null : env.attrs['data-theme'];
process.stdout.write(JSON.stringify(result));
"""


def current_recipe():
    return RECIPE_OVERRIDE if RECIPE_OVERRIDE is not None else recipe_source()


def strip_markers(text):
    return MARKER.sub('', text)


def style_of(page):
    return re.search(r'<style>\n(.*?)\n</style>', page, re.S).group(1)


def selectors_of(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'url\([^)]*\)', 'url()', css)
    found = []
    for preamble in re.findall(r'([^{}]+)\{', css):
        preamble = preamble.strip()
        if preamble.startswith('@'):
            continue
        found += [part.strip() for part in preamble.split(',')]
    return found


def reaching_samples(selectors):
    """Selectors that could match product samples: unscoped ones, and descendant, child or sibling selectors whose last
    compound names no class (for example `.sec span`)."""
    found = set()
    for selector in selectors:
        last = re.split(r'[\s>+~]+', selector)[-1]
        unscoped = not re.search(r'\.[A-Za-z_-]', selector)
        bare_tail = bool(re.search(r'[\s>+~]', selector)) and not re.search(r'\.[A-Za-z_-]', last)
        if unscoped or bare_tail:
            found.add(selector)
    return found


def normalized_view(page):
    page = re.sub(r'<meta name="tackle-(?:input-digest|file-revision)"[^>]*>', '', page)
    page = MARKER.sub('', page)
    return re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', 'STAMP', page)


def tree_digest(root):
    entries = []
    for path in sorted(Path(root).rglob('*')):
        if path.is_file():
            entries.append((str(path.relative_to(root)), hashlib.sha256(path.read_bytes()).hexdigest()))
    return entries


def template_copy(tmp, case, text):
    path = Path(tmp) / (case + '-template.md')
    path.write_text(text, encoding='utf-8')
    return path


def workspace_with_view(tmp, case, plan=None, template=None):
    files = workspace_files()
    if plan is not None:
        files['plan.md'] = plan
    if template is None:
        result, view = run_recipe(tmp, files, case)
    else:
        workspace = Path(tmp) / case
        for name, text in files.items():
            (workspace / name).parent.mkdir(parents=True, exist_ok=True)
            (workspace / name).write_text(text, encoding='utf-8')
        script = Path(tmp) / (case + '-view-recipe.py')
        script.write_text(current_recipe(), encoding='utf-8')
        view = workspace / 'plan-view.html'
        result = subprocess.run([sys.executable, '-I', str(script), '--template', str(template), str(workspace), str(view)],
                                capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return Path(tmp) / case


def page_command(tmp, case, workspace, fragment, output, template=None, check=False):
    script = Path(tmp) / (case + '-recipe.py')
    script.write_text(current_recipe(), encoding='utf-8')
    args = [sys.executable, '-I', str(script), '--template', str(template or TEMPLATE)]
    if check:
        args.append('--check')
    args += ['--page', str(fragment), str(workspace), str(output)]
    return subprocess.run(args, capture_output=True, text=True, timeout=60)


def run_page(tmp, case, workspace, fragment, output=None, template=None):
    frag = Path(tmp) / (case + '-fragment.html')
    frag.write_bytes(fragment if isinstance(fragment, bytes) else fragment.encode('utf-8'))
    out = Path(output) if output else Path(workspace) / 'aux.html'
    result = page_command(tmp, case, workspace, frag, out, template)
    return result, out, frag


class AuxPageTests(unittest.TestCase):
    def test_tokens_and_font_are_inherited_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'tokens')
            result, out, _ = run_page(tmp, 'tokens', workspace, FRAGMENT)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            template = TEMPLATE.read_text(encoding='utf-8')
            tokens = template[template.index(':root{'):template.index('*,*::before,*::after')]
            self.assertIn(':root[data-theme="dark"]{', tokens)
            self.assertIn(':root:not([data-theme="light"])', tokens)
            self.assertIn(tokens, page)
            self.assertIn('--sans:Outfit', page)
            self.assertIn('@font-face{font-family:Outfit;', page)
            for rule in ('.sec-head{', '.sec-head h2{', '.sec-lede{', '.kicker{', '.kicker::before{',
                         'h3,h4,h5{text-wrap:balance}'):
                line = next(l for l in template.split('\n') if l.startswith(rule))
                self.assertIn(line, page, 'the heading rule ' + rule + ' is not byte-equal to the template')

    def test_top_bar_brand_and_toggle_come_from_the_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'topbar')
            result, out, _ = run_page(tmp, 'topbar', workspace, FRAGMENT)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertEqual(page.count('class="topbar"'), 1)
            brand = re.search(r'<a class="brand" href="([^"]*)"><span class="brand-mark" aria-hidden="true"></span>'
                              r'<span class="brand-name">([^<]*)</span></a>', page)
            self.assertIsNotNone(brand)
            self.assertEqual(brand.group(1), 'plan-view.html')
            self.assertEqual(brand.group(2), 'demo')
            template = TEMPLATE.read_text(encoding='utf-8')
            button = re.search(r'<button type="button" class="theme-toggle" id="theme".*?</button>', template, re.S).group(0)
            page_button = re.search(r'<button type="button" class="theme-toggle" id="theme".*?</button>', page, re.S).group(0)
            self.assertEqual(page_button, button.replace('{{ui_theme}}', 'Switch between light and dark'))

            long_title = '# Action plan — ' + 'x' * 50 + '\n'
            long_workspace = workspace_with_view(tmp, 'long-title', plan=long_title)
            (long_workspace / 'pages').mkdir()
            result, out, _ = run_page(tmp, 'long-title', long_workspace, '<p>Two options.</p>\n', output=long_workspace / 'pages' / 'aux.html')
            self.assertEqual(result.returncode, 0, result.stderr)
            long_page = out.read_text(encoding='utf-8')
            self.assertIn('<span class="brand-name">' + 'x' * 39 + '…</span>', long_page)
            self.assertIn('href="../plan-view.html"', long_page)
            self.assertIn('<title>' + 'x' * 50 + '</title>', long_page)

    def test_skeleton_has_the_template_metas_one_style_and_the_fragment_in_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'skeleton')
            result, out, _ = run_page(tmp, 'skeleton', workspace, FRAGMENT)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertTrue(page.startswith('<!doctype html>\n<html lang="en">'))
            template = TEMPLATE.read_text(encoding='utf-8')
            for meta in ('<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">',
                         '<meta name="color-scheme" content="light dark">'):
                self.assertIn(meta, template)
                self.assertIn(meta, page)
            self.assertEqual(len(re.findall(r'<style\b', page)), 1)
            self.assertIn('<style>\n', page)
            self.assertIn('<main id="main"><div class="sec">' + FRAGMENT + '</div></main>', page)
            self.assertIn('<meta name="tackle-input-digest" content=', page)
            self.assertNotIn('tackle-file-revision', page)

    def test_theme_script_shares_the_view_storage_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'theme-key')
            result, out, _ = run_page(tmp, 'theme-key', workspace, FRAGMENT)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            script = re.search(r'<script>\n(.*?)</script>', page, re.S).group(1)
            self.assertIn("stored('tackle-plan-view-theme')", script)
            self.assertIn("stored('tackle-plan-view-theme', next)", script)
            self.assertIn("getElementById('theme')", script)
            self.assertNotIn('tackle-base', page)

    def test_theme_toggle_flips_the_theme_and_stores_it(self):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'the theme test needs node on the PATH')
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'toggle')
            result, out, _ = run_page(tmp, 'toggle', workspace, FRAGMENT)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            script = re.search(r'<script>\n(.*?)</script>', page, re.S).group(1)
            script_path = Path(tmp) / 'page-script.js'
            script_path.write_text(script, encoding='utf-8')
            harness = Path(tmp) / 'harness.js'
            harness.write_text(NODE_HARNESS, encoding='utf-8')
            run = subprocess.run([node, str(harness), str(script_path)], capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stderr)
            seen = json.loads(run.stdout)
            self.assertIsNone(seen['fresh'])
            self.assertEqual(seen['afterFirst'], 'dark')
            self.assertEqual(seen['storedFirst'], 'dark')
            self.assertEqual(seen['afterSecond'], 'light')
            self.assertEqual(seen['storedSecond'], 'light')
            self.assertEqual(seen['startDark'], 'dark')

    def test_language_follows_the_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'spanish', plan=SPANISH_PLAN)
            result, out, _ = run_page(tmp, 'spanish', workspace, FRAGMENT)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertTrue(page.startswith('<!doctype html>\n<html lang="es">'))
            self.assertIn('aria-label="Cambiar entre claro y oscuro"', page)
            self.assertIn('Ir al contenido', page)

    def test_title_comes_from_the_heading_or_the_plan(self):
        cases = (
            ('plain', '<p>Two options.</p>\n', '<title>demo</title>'),
            ('entities', '<h1>Palette <em>proposals</em> &amp; more</h1>\n',
             '<title>Palette proposals &amp; more</title>'),
            ('injection', '<h1>a</title><script>alert(1)</script></h1>\n', '<title>aalert(1)</title>'),
        )
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'titles')
            for name, fragment, expected in cases:
                with self.subTest(case=name):
                    result, out, _ = run_page(tmp, 'title-' + name, workspace, fragment)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    page = out.read_text(encoding='utf-8')
                    self.assertIn(expected, page)
                    self.assertNotIn('&amp;amp;', page.split('</title>', 1)[0])
                    head_title = re.search(r'<title>(.*?)</title>', page, re.S).group(1)
                    self.assertNotIn('<', head_title)

    def test_fragment_is_inserted_byte_for_byte(self):
        fragment = b'<p>{{word}} &amp; \\1 {{ }}</p>\r\n<p>caf\xc3\xa9</p>\r\n'
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'bytes')
            result, out, _ = run_page(tmp, 'bytes', workspace, fragment)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(fragment, out.read_bytes())

    def test_product_sample_keeps_its_appearance(self):
        fragment = FRAGMENT + SAMPLE + '\n'
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'sample')
            result, out, _ = run_page(tmp, 'sample', workspace, fragment)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertIn(SAMPLE, page)
            css = style_of(page)
            self.assertNotIn('tk-sample', css)
            self.assertEqual(reaching_samples(selectors_of(css)) - ALLOWED_REACH, set(),
                             'a base rule may reach product samples')

    def test_a_class_qualified_rule_that_reaches_samples_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            lines = TEMPLATE.read_text(encoding='utf-8').split('\n')
            index = next(i for i, line in enumerate(lines) if line.startswith('.sec::before{'))
            lines.insert(index + 1, '.sec span{color:#c80000}')
            template = template_copy(tmp, 'leak', '\n'.join(lines))
            workspace = workspace_with_view(tmp, 'leak', template=template)
            result, out, _ = run_page(tmp, 'leak', workspace, SAMPLE + '\n', template=template)
            self.assertEqual(result.returncode, 0, result.stderr)
            leak = reaching_samples(selectors_of(style_of(out.read_text(encoding='utf-8')))) - ALLOWED_REACH
            self.assertIn('.sec span', leak, 'the sample check must flag a class-qualified rule that reaches samples')

    def test_brand_link_path_is_url_encoded(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'ws #1 x')
            out_dir = Path(tmp) / 'out dir #2'
            out_dir.mkdir()
            result, out, _ = run_page(tmp, 'encoded', workspace, FRAGMENT, output=out_dir / 'aux.html')
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertIn('<a class="brand" href="../ws%20%231%20x/plan-view.html">', page)

    def test_page_is_local_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'local')
            result, out, _ = run_page(tmp, 'local', workspace, FRAGMENT)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertIsNone(re.search(r'https?://', page))
            self.assertNotIn('<link rel="stylesheet"', page)
            self.assertIsNone(re.search(r'<script\b[^>]*\bsrc=', page))

    def test_only_marked_ranges_reach_the_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = TEMPLATE.read_text(encoding='utf-8')
            self.assertEqual(text.count('.hero{padding-top:28px}'), 1)
            template = template_copy(tmp, 'unmarked', text.replace('.hero{padding-top:28px}', '.hero{padding-top:99px}'))
            workspace = workspace_with_view(tmp, 'unmarked', template=template)
            result, out, _ = run_page(tmp, 'unmarked', workspace, FRAGMENT, template=template)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertNotIn('99px', page)
            self.assertNotIn('28px}', page)
            self.assertNotIn('@media print', page)
            self.assertNotIn('print-report', page)
            self.assertLess(page.index('@font-face'), page.index('main{display:block}'))
            self.assertLess(page.index('main{display:block}'), page.index('.sec::before'))

    def test_marked_template_builds_the_same_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            marked = workspace_with_view(tmp, 'marked')
            unmarked_template = template_copy(tmp, 'unmarked-view', strip_markers(TEMPLATE.read_text(encoding='utf-8')))
            unmarked = workspace_with_view(tmp, 'unmarked-view-build', template=unmarked_template)
            marked_page = (marked / 'plan-view.html').read_text(encoding='utf-8')
            unmarked_page = (unmarked / 'plan-view.html').read_text(encoding='utf-8')
            self.assertIn('/* tackle-base:start */', TEMPLATE.read_text(encoding='utf-8'))
            self.assertNotEqual(marked_page, unmarked_page)
            self.assertEqual(normalized_view(marked_page), normalized_view(unmarked_page))

    def test_check_is_current_then_stale_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = workspace_with_view(tmp, 'check')
            result, out, frag = run_page(tmp, 'check', workspace, FRAGMENT)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertNotIn('tackle-file-revision', page)
            self.assertFalse((out.parent / (out.stem + '.stamp.js')).exists())
            before = tree_digest(tmp)
            current = page_command(tmp, 'check', workspace, frag, out, check=True)
            self.assertEqual(current.returncode, 0, current.stderr)
            self.assertEqual(current.stdout.strip(), 'view current')
            frag.write_text(FRAGMENT + '<p>Edited.</p>\n', encoding='utf-8')
            stale = page_command(tmp, 'check', workspace, frag, out, check=True)
            self.assertEqual(stale.returncode, 1, stale.stdout + stale.stderr)
            self.assertEqual(stale.stdout.strip(), 'view stale: fragment')
            self.assertEqual(out.read_text(encoding='utf-8'), page)
            after = [entry for entry in tree_digest(tmp) if not entry[0].endswith('-fragment.html')]
            self.assertEqual([entry for entry in before if not entry[0].endswith('-fragment.html')], after)

    def test_page_mode_refuses_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = TEMPLATE.read_text(encoding='utf-8')
            missing_end = text.replace('/* tackle-base:end */\n', '', 1)
            reversed_pair = text.replace('/* tackle-base-theme:start */', '@@SWAP@@', 1) \
                .replace('/* tackle-base-theme:end */', '/* tackle-base-theme:start */', 1) \
                .replace('@@SWAP@@', '/* tackle-base-theme:end */', 1)
            duplicate_start = text.replace('/* tackle-base:start */\n', '/* tackle-base:start */\n/* tackle-base:start */\n', 1)
            workspace = workspace_with_view(tmp, 'refusals')
            cases = {
                'missing-end': template_copy(tmp, 'missing-end', missing_end),
                'reversed': template_copy(tmp, 'reversed', reversed_pair),
                'duplicate-start': template_copy(tmp, 'duplicate-start', duplicate_start),
            }
            for name, template in cases.items():
                with self.subTest(template=name):
                    out = Path(tmp) / (name + '.html')
                    result, _, _ = run_page(tmp, name, workspace, FRAGMENT, output=out, template=template)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertEqual(len(result.stderr.strip().splitlines()), 1)
                    self.assertFalse(out.exists())
            with self.subTest(case='no-view'):
                bare = Path(tmp) / 'bare'
                bare.mkdir()
                (bare / 'plan.md').write_text('# Plan — bare\n', encoding='utf-8')
                result, out, _ = run_page(tmp, 'bare', bare, FRAGMENT)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(len(result.stderr.strip().splitlines()), 1)
                self.assertFalse(out.exists())
            with self.subTest(case='missing-fragment'):
                out = Path(tmp) / 'missing.html'
                frag = Path(tmp) / 'does-not-exist.html'
                result = page_command(tmp, 'missing-fragment', workspace, frag, out)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(len(result.stderr.strip().splitlines()), 1)
                self.assertFalse(out.exists())
            with self.subTest(case='view-path'):
                view = workspace / 'plan-view.html'
                before = view.read_bytes()
                result, _, _ = run_page(tmp, 'view-path', workspace, FRAGMENT, output=view)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(view.read_bytes(), before)

    def test_single_source_follows_the_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = TEMPLATE.read_text(encoding='utf-8')
            self.assertEqual(text.count('--accent:#f24a00;'), 1)
            changed = text.replace('--accent:#f24a00;', '--accent:#1d6fd0;').replace('tackle-plan-view-theme', 'probe-theme')
            template = template_copy(tmp, 'single-source', changed)
            workspace = workspace_with_view(tmp, 'single-source', template=template)
            result, out, _ = run_page(tmp, 'single-source', workspace, FRAGMENT, template=template)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertIn('--accent:#1d6fd0;', page)
            self.assertNotIn('--accent:#f24a00;', page)
            self.assertIn("stored('probe-theme')", page)
            self.assertNotIn('tackle-plan-view-theme', page)


if __name__ == '__main__':
    unittest.main()
