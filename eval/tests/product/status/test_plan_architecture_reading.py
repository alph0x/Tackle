"""Every directed component connection in the plan view stays readable.

The shipped recipe draws the architecture map before and after the plan. Each arrow carries its recorded
words, a complete source, relation and destination guide follows each picture before any selection, and
selecting a component narrows the guide and the arrows to its own connections and opens a lens with what flows
into it and out of it, where a neighbor can be walked to, until the selection is cleared. The page's controller runs on the page's markup in a minimal DOM; the CSS check
covers the base display rule for arrow words only, not a rendering engine.
"""
import html
import re
import tempfile
import unittest

from plan_view_dom import run_scenario
from test_architecture_map import base_map, delta_of, fenced_source, run_view, VIEW_RECIPE


def guide_rows(page):
    rows = []
    for guide in re.findall(r'<div class="arel-guide">(.*?)</div>', page, re.S):
        current = []
        for attrs, body in re.findall(r'<li class="arel-row"([^>]*)>(.*?)</li>', guide, re.S):
            fields = {key: html.unescape(value) for key, value in re.findall(r'<span class="arel-(from|label|to)">(.*?)</span>', body, re.S)}
            endpoints = dict(re.findall(r'data-(from|to)="([^"]*)"', attrs))
            assert 'hidden' not in attrs, 'a static guide row starts hidden'
            current.append((endpoints['from'], endpoints['to'], fields))
        rows.append(current)
    return rows


def label_display(page):
    css = re.search(r'<style>(.*?)</style>', page, re.S).group(1)
    display = 'inline'
    for body in re.findall(r'(?:^|[}\s,])\.aelabel\s*\{([^}]*)\}', css):
        found = re.findall(r'\bdisplay\s*:\s*([^;}]+)', body)
        if found:
            display = found[-1].strip()
    return display


def arrow_words(page, pic):
    block = re.search(r'<div class="arch-pic" data-pic="%s">(.*?)(?=<div class="arch-pic"|</section>)' % pic, page, re.S).group(1)
    return [(a, b, html.unescape(text)) for a, b, text in
            re.findall(r'<text class="aelabel[^"]*" data-from="([^"]*)" data-to="([^"]*)"[^>]*>([^<]*)</text>', block)]


class ArchitectureReadingTests(unittest.TestCase):
    page = None

    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as tmp:
            result, cls.page, _ = run_view(tmp, 'reading', delta_of(), base_map())
        assert result.returncode == 0, result.stdout + result.stderr

    def scenario(self, code):
        result = run_scenario(self.page, code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'OK', result.stderr)

    def test_every_directed_connection_is_worded_on_its_arrow_and_listed_before_selection(self):
        base = base_map()
        titles = {c['id']: c['title'] for c in base['components']}
        titles['viewer'] = 'Viewer'
        expected = {'today': base['relations'], 'after': base['relations'] + [['intake', 'viewer', 'calls']]}
        rows = guide_rows(self.page)
        self.assertEqual(len(rows), 2)
        for actual, pic in zip(rows, ('today', 'after')):
            self.assertEqual(actual, [(a, b, {'from': titles[a], 'label': label, 'to': titles[b]}) for a, b, label in expected[pic]])
            self.assertEqual(sorted(arrow_words(self.page, pic)), sorted((a, b, label) for a, b, label in expected[pic]))
        self.assertNotEqual(label_display(self.page), 'none')
        fault = re.sub(r'(\.aelabel\s*\{[^}]*\bdisplay\s*:)\s*[a-z-]+', r'\1none', self.page)
        self.assertEqual(label_display(fault), 'none', 'the oracle rejects hidden arrow words')
        equivalent = re.sub(r'(\.aelabel\s*\{[^}]*?)\bdisplay\s*:[^;}]+;?', r'\1', self.page)
        self.assertNotEqual(label_display(equivalent), 'none', 'the default inline display is a valid alternative')
        self.assertIn('Read each row as source', self.page)

    def test_long_arrow_words_shorten_on_the_arrow_but_stay_whole_in_the_guide(self):
        base = base_map()
        long_label = 'writes the nightly records that every later review reads first'
        base['relations'][0][2] = long_label
        with tempfile.TemporaryDirectory() as tmp:
            result, page, _ = run_view(tmp, 'long-words', delta_of(), base)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        words = [text for a, b, text in arrow_words(page, 'today') if (a, b) == tuple(base['relations'][0][:2])]
        self.assertEqual(len(words), 1)
        self.assertTrue(words[0].endswith('…') and len(words[0]) <= 30 and long_label.startswith(words[0][:-1].rstrip()))
        self.assertIn(long_label, [row[2]['label'] for row in guide_rows(page)[0]])

    def test_localized_empty_and_hostile_relation_guides_keep_exact_readable_text(self):
        scope = {'__name__': 'architecture_reading_recipe'}
        exec(compile(fenced_source(VIEW_RECIPE), str(VIEW_RECIPE), 'exec'), scope)
        hostile = '<img src=x onerror=alert(1)>'
        components = {'a': {'title': hostile}, 'b': {'title': 'A full destination title'}}
        for lang, heading, empty in (('en', 'Connections in this map', 'No connections'), ('es', 'Conexiones de este mapa', 'No hay conexiones')):
            with self.subTest(lang=lang):
                ui = scope['UI'][lang]
                rendered = scope['arch_relation_guide']([('a', 'b', hostile)], components, ui)
                self.assertEqual(guide_rows(rendered)[0][0][2], {'from': hostile, 'label': hostile, 'to': components['b']['title']})
                self.assertNotIn('<img', rendered)
                self.assertIn(heading, rendered)
                self.assertIn('tabindex="0"', rendered)
                blank = scope['arch_relation_guide']([], components, ui)
                self.assertEqual(guide_rows(blank), [[]])
                self.assertIn(empty, blank)

    def test_a_selected_component_narrows_arrows_guide_and_lens_and_clears_back_to_all(self):
        self.scenario(r"""
const env = load();
const arch = env.one('#architecture');
const after = () => env.one('#architecture .arch-pic.on');
assert.strictEqual(after().getAttribute('data-pic'), 'after', 'the picture after the plan opens first');
const card = after().querySelector('.acard[data-cid="store"]');
card.click();
const rows = after().querySelectorAll('.arel-row');
const shown = rows.filter((r) => !r.hidden).map((r) => r.getAttribute('data-from') + '>' + r.getAttribute('data-to')).sort();
assert.ok(shown.length > 0 && shown.every((pair) => pair.split('>').includes('store')), 'only connections of the selection stay listed: ' + shown);
const summary = after().querySelector('.arel-summary');
assert.ok(summary.textContent.includes(card.querySelector('h5').textContent) && summary.textContent.includes(String(shown.length)));
const on = after().querySelectorAll('svg .aedge.on').map((e) => e.getAttribute('data-from') + '>' + e.getAttribute('data-to')).sort();
assert.deepStrictEqual(on, shown, 'the highlighted arrows are the listed connections');
assert.deepStrictEqual(after().querySelectorAll('svg .aelabel.on').map((e) => e.getAttribute('data-from') + '>' + e.getAttribute('data-to')).sort(), shown);
assert.ok(after().querySelector('svg').classList.contains('focus'));
const lens = arch.querySelector('.lens');
assert.ok(!lens.hidden, 'a selection opens the lens');
const title = (cid) => after().querySelector('.acard[data-cid="' + cid + '"] h5').textContent;
const types = JSON.parse(card.getAttribute('data-rel-types'));
const incoming = types.filter((r) => r.to === 'store' && r.from !== 'store');
const outgoing = types.filter((r) => r.from === 'store' && r.to !== 'store');
assert.ok(incoming.length + outgoing.length === shown.length, 'the lens holds every listed connection');
const lensRows = (side) => lens.querySelectorAll('.lens-' + side + ' .lens-node').map((n) => [n.getAttribute('data-cid'), n.querySelector('.lens-title').textContent, n.querySelector('.lens-verb').textContent]);
assert.deepStrictEqual(lensRows('in'), incoming.map((r) => [r.from, title(r.from), r.label]));
assert.deepStrictEqual(lensRows('out'), outgoing.map((r) => [r.to, title(r.to), r.label]));
assert.strictEqual(lens.querySelector('.lens-center h3').textContent, title('store'));
assert.ok(card.classList.contains('sel') && after().querySelectorAll('.acard.dim').length > 0);
const walk = lens.querySelector('.lens-node');
const next = walk.getAttribute('data-cid');
walk.click();
assert.ok(after().querySelector('.acard[data-cid="' + next + '"]').classList.contains('sel'), 'a lens neighbor becomes the selection');
assert.strictEqual(lens.querySelector('.lens-center h3').textContent, title(next));
lens.querySelector('.lens-close').click();
assert.ok(lens.hidden, 'the close button clears the lens');
card.click();
card.click();
assert.strictEqual(after().querySelectorAll('.arel-row').filter((r) => r.hidden).length, 0);
assert.strictEqual(summary.textContent, summary.getAttribute('data-all'));
assert.ok(lens.hidden && !after().querySelector('svg').classList.contains('focus'));
assert.strictEqual(after().querySelectorAll('.sel, .dim, .rel, .aedge.on').length, 0);
const node = after().querySelector('.anode[data-cid="viewer"]');
node.click();
assert.ok(after().querySelector('.acard[data-cid="viewer"]').classList.contains('sel'), 'diagram and cards share one selection');
env.one('#architecture .apics [data-pic="today"]').click();
assert.strictEqual(after().getAttribute('data-pic'), 'today');
assert.strictEqual(env.all('#architecture .sel').length, 0, 'a component missing from the other picture leaves no selection');
assert.ok(lens.hidden);
after().querySelector('.acard[data-cid="store"]').click();
env.one('#architecture .apics [data-pic="after"]').click();
assert.ok(after().querySelector('.acard[data-cid="store"]').classList.contains('sel'), 'a component present in both pictures stays selected');
env.one('#architecture').querySelector('.acard').key('Escape');
assert.strictEqual(env.all('#architecture .sel').length, 0);
""")

    def test_the_view_tabs_answer_clicks_and_arrow_keys(self):
        self.scenario(r"""
const env = load();
const tabs = env.all('#architecture .atabs [data-view]');
const panels = () => env.one('#architecture .arch-pic.on').querySelectorAll('.apanel.on').map((p) => p.getAttribute('data-view'));
assert.deepStrictEqual(panels(), ['cards']);
tabs[0].key('ArrowRight');
assert.deepStrictEqual(panels(), ['diagram']);
assert.strictEqual(tabs[1].getAttribute('aria-selected'), 'true');
assert.strictEqual(env.document.activeElement, tabs[1]);
tabs[1].key('Home');
assert.deepStrictEqual(panels(), ['cards']);
tabs[0].key('End');
assert.deepStrictEqual(panels(), ['diagram']);
tabs[1].key('ArrowLeft');
assert.deepStrictEqual(panels(), ['cards']);
tabs[1].click();
assert.deepStrictEqual(panels(), ['diagram']);
""")


if __name__ == '__main__':
    unittest.main()
